"""Адаптер для работы с базой адресов хранения (store.db)."""
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class StoreAdapter:
    """Адаптер для управления адресами хранения товаров."""
    
    def __init__(self, db_path: str = "store.db"):
        # Пробуем несколько путей: указанный, корень проекта, data/db/
        self.db_path: Optional[Path] = None
        candidates = [
            Path(db_path),
            Path(__file__).parent.parent.parent.parent / db_path,
            Path("data/db") / db_path
        ]
        for candidate in candidates:
            if candidate.exists():
                self.db_path = candidate
                break
        
        if self.db_path is None:
            # Если БД не найдена, создаём в корне проекта
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
        self._connection: Optional[sqlite3.Connection] = None
        self._ensure_schema()
        
    def _get_connection(self) -> sqlite3.Connection:
        """Получить соединение с БД."""
        if self._connection is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row
            logger.info(f"[StoreAdapter] Подключено к {self.db_path}")
        return self._connection
    
    def _ensure_schema(self):
        """Создать таблицу если не существует."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS storage_locations (
                article TEXT PRIMARY KEY,
                location_code TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        logger.info("[StoreAdapter] Схема БД проверена")
    
    def get_location(self, article: str) -> Optional[str]:
        """Получить адрес хранения для товара."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        sql = "SELECT location_code FROM storage_locations WHERE article = ?"
        
        try:
            cursor.execute(sql, (article,))
            row = cursor.fetchone()
            if row:
                location = row['location_code']
                logger.debug(f"[StoreAdapter] Адрес для {article}: {location}")
                return location
            return None
        except Exception as e:
            logger.error(f"[StoreAdapter] Ошибка получения адреса: {e}")
            return None
    
    def update_location(self, article: str, location: str) -> bool:
        """Обновить или создать адрес хранения."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        sql = """
            INSERT OR REPLACE INTO storage_locations (article, location_code, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """
        
        try:
            cursor.execute(sql, (article, location))
            conn.commit()
            logger.info(f"[StoreAdapter] Обновлён адрес для {article}: {location}")
            return True
        except Exception as e:
            logger.error(f"[StoreAdapter] Ошибка обновления адреса: {e}")
            conn.rollback()
            return False
    
    def close(self):
        """Закрыть соединение с БД."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("[StoreAdapter] Соединение закрыто")
