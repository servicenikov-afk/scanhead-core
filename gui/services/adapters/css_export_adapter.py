"""Адаптер для работы с базой CSS Export (css_export.db)."""
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class CssExportAdapter:
    """Адаптер для получения данных о запчастях из css_export.db."""

    def __init__(self, db_path: str = "data/databases/css_export/css_export.db"):
        # Путь относительно корня проекта
        project_root = Path(__file__).parent.parent.parent.parent
        self.db_path = project_root / db_path
        
        # Проверка наличия файла
        if not self.db_path.exists():
            logger.error(f"[CssExportAdapter] БД НЕ НАЙДЕНА: {self.db_path}")
            logger.error(f"[CssExportAdapter] Текущая директория: {Path.cwd()}")
            logger.error(f"[CssExportAdapter] project_root: {project_root}")
            # Пробуем альтернативный путь (относительно cwd)
            alt_path = Path(db_path)
            if alt_path.exists():
                self.db_path = alt_path
                logger.warning(f"[CssExportAdapter] Используется альтернативный путь: {self.db_path}")
            else:
                logger.error(f"[CssExportAdapter] Альтернативный путь тоже не найден: {alt_path}")
        
        self._connection: Optional[sqlite3.Connection] = None

    def _get_connection(self) -> sqlite3.Connection:
        """Получить соединение с БД."""
        if self._connection is None:
            if not self.db_path.exists():
                logger.warning(f"[CssExportAdapter] БД не найдена: {self.db_path}")
                raise FileNotFoundError(f"Database not found: {self.db_path}")

            self._connection = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            self._connection.row_factory = sqlite3.Row
            logger.info(f"[CssExportAdapter] Подключено к {self.db_path} (read-only)")

        return self._connection

    def get_by_article(self, article: str) -> List[Dict[str, Any]]:
        """Получить информацию о детали по артикулу (может быть несколько записей для разных моделей)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        sql = """
            SELECT product_model, position, art_no, name, usage_path,
                   category1, category2, category3, production_date_from, 
                   production_date_to, serial_from, serial_to
            FROM spare_parts
            WHERE art_no = ?
        """

        try:
            cursor.execute(sql, (article,))
            rows = cursor.fetchall()
            items = [
                {
                    'product_model': row['product_model'],
                    'position': row['position'],
                    'art_no': row['art_no'],
                    'name': row['name'],
                    'usage_path': row['usage_path'],
                    'category1': row['category1'],
                    'category2': row['category2'],
                    'category3': row['category3'],
                    'production_date_from': row['production_date_from'],
                    'production_date_to': row['production_date_to'],
                    'serial_from': row['serial_from'],
                    'serial_to': row['serial_to']
                }
                for row in rows
            ]
            logger.debug(f"[CssExportAdapter] Найдено {len(items)} записей для {article}")
            return items
        except Exception as e:
            logger.error(f"[CssExportAdapter] Ошибка получения данных: {e}")
            return []

    def search_by_name(self, query: str) -> List[Dict[str, Any]]:
        """Поиск деталей по названию."""
        conn = self._get_connection()
        cursor = conn.cursor()

        search_pattern = f"%{query}%"
        sql = """
            SELECT DISTINCT art_no, name, product_model, usage_path
            FROM spare_parts
            WHERE name LIKE ?
            LIMIT 50
        """

        try:
            cursor.execute(sql, (search_pattern,))
            rows = cursor.fetchall()
            items = [
                {
                    'art_no': row['art_no'],
                    'name': row['name'],
                    'product_model': row['product_model'],
                    'usage_path': row['usage_path']
                }
                for row in rows
            ]
            logger.info(f"[CssExportAdapter] Найдено {len(items)} записей по запросу '{query}'")
            return items
        except Exception as e:
            logger.error(f"[CssExportAdapter] Ошибка поиска: {e}")
            return []

    def close(self):
        """Закрыть соединение с БД."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("[CssExportAdapter] Соединение закрыто")
