"""Адаптер для временной очереди печати (temp.db)."""
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TempQueueAdapter:
    """Адаптер для управления временной очередью печати."""
    
    def __init__(self, db_path: str = "data/db/temp/temp.db"):
        self.db_path = Path(db_path)
        self._connection: Optional[sqlite3.Connection] = None
        self._ensure_schema()
        
    def _get_connection(self) -> sqlite3.Connection:
        """Получить соединение с БД."""
        if self._connection is None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row
            logger.info(f"[TempQueueAdapter] Подключено к {self.db_path}")
        return self._connection
    
    def _ensure_schema(self):
        """Создать таблицу если не существует."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS print_queue (
                article TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                address TEXT,
                quantity INTEGER DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        logger.info("[TempQueueAdapter] Схема БД проверена")
    
    def add_or_increment(self, article: str, name: str, address: str = "") -> bool:
        """Добавить товар в очередь или увеличить количество."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Проверка существования
        cursor.execute("SELECT quantity FROM print_queue WHERE article = ?", (article,))
        row = cursor.fetchone()
        
        if row:
            # Увеличить количество
            new_qty = row['quantity'] + 1
            sql = """
                UPDATE print_queue 
                SET quantity = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE article = ?
            """
            cursor.execute(sql, (new_qty, article))
            logger.info(f"[TempQueueAdapter] Увеличено количество для {article}: {new_qty}")
        else:
            # Добавить новый
            sql = """
                INSERT INTO print_queue (article, name, address, quantity)
                VALUES (?, ?, ?, 1)
            """
            cursor.execute(sql, (article, name, address))
            logger.info(f"[TempQueueAdapter] Добавлен товар {article} в очередь")
        
        conn.commit()
        return True
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Получить все товары из очереди."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        sql = """
            SELECT article, name, address, quantity, added_at, updated_at
            FROM print_queue
            ORDER BY added_at DESC
        """
        
        try:
            cursor.execute(sql)
            rows = cursor.fetchall()
            items = [
                {
                    'article': row['article'],
                    'name': row['name'],
                    'address': row['address'] or '',
                    'quantity': row['quantity'],
                    'added_at': row['added_at'],
                    'updated_at': row['updated_at']
                }
                for row in rows
            ]
            logger.debug(f"[TempQueueAdapter] Получено {len(items)} товаров из очереди")
            return items
        except Exception as e:
            logger.error(f"[TempQueueAdapter] Ошибка получения очереди: {e}")
            return []
    
    def remove(self, article: str) -> bool:
        """Удалить товар из очереди."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        sql = "DELETE FROM print_queue WHERE article = ?"
        
        try:
            cursor.execute(sql, (article,))
            conn.commit()
            logger.info(f"[TempQueueAdapter] Удалён товар {article} из очереди")
            return True
        except Exception as e:
            logger.error(f"[TempQueueAdapter] Ошибка удаления: {e}")
            conn.rollback()
            return False
    
    def clear(self) -> bool:
        """Очистить всю очередь."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        sql = "DELETE FROM print_queue"
        
        try:
            cursor.execute(sql)
            conn.commit()
            logger.info("[TempQueueAdapter] Очередь очищена")
            return True
        except Exception as e:
            logger.error(f"[TempQueueAdapter] Ошибка очистки: {e}")
            conn.rollback()
            return False
    
    def close(self):
        """Закрыть соединение с БД."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("[TempQueueAdapter] Соединение закрыто")
