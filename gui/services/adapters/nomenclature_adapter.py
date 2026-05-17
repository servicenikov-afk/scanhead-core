"""Адаптер для работы с основной базой номенклатуры."""
import sqlite3
import threading
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Product:
    """Модель товара."""
    article: str
    name: str
    article2: Optional[str] = None
    address: Optional[str] = None
    barcodes: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'article': self.article,
            'name': self.name,
            'article2': self.article2 or '',
            'address': self.address or '',
            'barcodes': self.barcodes or '',
            'description': self.description or '',
            'category': self.category or ''
        }


class NomenclatureAdapter:
    """Адаптер для поиска товаров в nomenclature.db."""

    def __init__(self, db_path: str = "data/databases/nomenclature/nomenclature.db"):
        # Путь относительно корня проекта
        project_root = Path(__file__).parent.parent.parent.parent
        self.db_path = project_root / db_path
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
        conn = self._get_connection()
        cursor = conn.cursor()

        search_pattern = f"%{query}%"
        # Поиск по canonical_article, name_ru и alternative_articles (JSON)
        sql = """
            SELECT DISTINCT n.canonical_article as article, n.name_ru as name, 
                   n.alternative_articles as barcodes, n.unit
            FROM nomenclature n
            LEFT JOIN json_each(n.alternative_articles) as aliases
            WHERE n.canonical_article LIKE ? 
               OR n.name_ru LIKE ? 
               OR aliases.value LIKE ?
            LIMIT 50
        """

        try:
            cursor.execute(sql, (search_pattern, search_pattern, search_pattern))
            rows = cursor.fetchall()
            products = [
                Product(
                    article=row['article'],
                    name=row['name'],
                    barcodes=row['barcodes']
                )
                for row in rows
            ]
            logger.info(f"[NomenclatureAdapter] Найдено {len(products)} товаров по запросу '{query}'")
            return products
        except Exception as e:
            logger.error(f"[NomenclatureAdapter] Ошибка поиска: {e}")
            return []

    def get_by_article(self, article: str) -> Optional[Product]:
        """Получить товар по точному артикулу."""
        conn = self._get_connection()
        cursor = conn.cursor()

        sql = """
            SELECT canonical_article as article, name_ru as name, 
                   alternative_articles as barcodes, unit
            FROM nomenclature
            WHERE canonical_article = ?
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
