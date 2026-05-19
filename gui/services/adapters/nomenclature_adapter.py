"""Адаптер для работы с основной базой номенклатуры."""
import sqlite3
import threading
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable
import logging

from libs.domain_models import Product

logger = logging.getLogger(__name__)


class NomenclatureAdapter:
    """Адаптер для поиска товаров в nomenclature.db."""

    def __init__(self, db_path: str = "data/databases/nomenclature/nomenclature.db"):
        # Путь относительно корня проекта
        project_root = Path(__file__).parent.parent.parent.parent
        self.db_path = project_root / db_path
        
        # Проверка наличия файла
        if not self.db_path.exists():
            logger.error(f"[NomenclatureAdapter] БД НЕ НАЙДЕНА: {self.db_path}")
            logger.error(f"[NomenclatureAdapter] Текущая директория: {Path.cwd()}")
            logger.error(f"[NomenclatureAdapter] project_root: {project_root}")
            # Пробуем альтернативный путь (относительно cwd)
            alt_path = Path(db_path)
            if alt_path.exists():
                self.db_path = alt_path
                logger.warning(f"[NomenclatureAdapter] Используется альтернативный путь: {self.db_path}")
            else:
                logger.error(f"[NomenclatureAdapter] Альтернативный путь тоже не найден: {alt_path}")
        
        self._connection: Optional[sqlite3.Connection] = None
        logger.info(f"[NomenclatureAdapter] Инициализация, путь к БД: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Получить соединение с БД (ленивая инициализация)."""
        if self._connection is None:
            if not self.db_path.exists():
                logger.warning(f"[NomenclatureAdapter] БД не найдена: {self.db_path}")
                raise FileNotFoundError(f"Database not found: {self.db_path}")

            self._connection = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            self._connection.row_factory = sqlite3.Row
            logger.info(f"[NomenclatureAdapter] Подключено к {self.db_path} (read-only)")

        return self._connection

    def search_async(self, query: str, callback: Callable[[List['Product']], None]) -> None:
        """Асинхронный поиск товаров по запросу."""
        def _search_thread():
            results = self.search(query)
            # Вызываем callback в главном потоке через after, если возможно
            # Или просто вызываем напрямую - search_bar обрабатывает
            callback(results)
        
        thread = threading.Thread(target=_search_thread, daemon=True)
        thread.start()

    def search(self, query: str) -> List[Product]:
        """Поиск товаров по артикулу, названию или штрихкоду."""
        # Создаём новое соединение в текущем потоке (потокобезопасность)
        if not self.db_path.exists():
            logger.warning(f"[NomenclatureAdapter] БД не найдена: {self.db_path}")
            return []
        
        conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        
        try:
            # Динамически определяем имя таблицы
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
            table_row = cursor.fetchone()
            if not table_row:
                logger.error("[NomenclatureAdapter] Таблицы в БД не найдены")
                return []
            table_name = table_row['name']
            logger.debug(f"[NomenclatureAdapter] Используется таблица: {table_name}")
            
            search_pattern = f"%{query}%"
            # Поиск по article, name и barcodes (простая схема)
            sql = f"""
                SELECT DISTINCT article, name, barcodes
                FROM {table_name}
                WHERE article LIKE ? 
                   OR name LIKE ? 
                   OR barcodes LIKE ?
                LIMIT 50
            """
            
            cursor.execute(sql, (search_pattern, search_pattern, search_pattern))
            rows = cursor.fetchall()
            products = [
                Product(
                    article=row['article'],
                    name=row['name'],
                    barcodes=row['barcodes'] or ''
                )
                for row in rows
            ]
            logger.info(f"[NomenclatureAdapter] Найдено {len(products)} товаров по запросу '{query}'")
            return products
        except Exception as e:
            logger.error(f"[NomenclatureAdapter] Ошибка поиска: {e}")
            return []
        finally:
            conn.close()

    def get_by_article(self, article: str) -> Optional[Product]:
        """Получить товар по точному артикулу."""
        conn = self._get_connection()
        cursor = conn.cursor()

        sql = """
            SELECT article, name, barcodes
            FROM nomenclature
            WHERE article = ?
        """

        try:
            cursor.execute(sql, (article,))
            row = cursor.fetchone()
            if row:
                return Product(
                    article=row['article'],
                    name=row['name'],
                    barcodes=row['barcodes']
                )
            return None
        except Exception as e:
            logger.error(f"[NomenclatureAdapter] Ошибка получения товара: {e}")
            return None

    def close(self):
        """Закрыть соединение с БД."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("[NomenclatureAdapter] Соединение закрыто")
