"""
SQLite-реализация репозиториев для работы с данными.

Этот модуль предоставляет конкретные реализации абстрактных репозиториев
для работы с базами данных SQLite.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from libs.repository.interfaces import (
    BaseRepository,
    ProductRepository,
    InventoryRepository,
    AddressRepository,
    CountRepository
)
from libs.domain_models import Product, InventoryItem, Address, CountItem

logger = logging.getLogger(__name__)


class SQLiteProductRepository(ProductRepository):
    """
    Реализация ProductRepository для SQLite.
    
    Предполагает наличие таблицы 'products' со структурой:
    - id (INTEGER PRIMARY KEY)
    - article (TEXT UNIQUE)
    - name (TEXT)
    - barcode (TEXT)
    - description (TEXT)
    - created_at (DATETIME)
    - updated_at (DATETIME)
    """

    def connect(self) -> None:
        if not self._connection:
            if not self.db_path:
                raise ValueError("db_path must be provided for SQLite connection")
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row
            self._local_connection = True
            self._init_schema()

    def disconnect(self) -> None:
        if self._local_connection and self._connection:
            self._connection.close()
            self._connection = None

    def _init_schema(self) -> None:
        """Создать таблицу products, если она не существует."""
        cursor = self._connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                barcode TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_article ON products(article)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_barcode ON products(barcode)")
        self._connection.commit()

    @contextmanager
    def _get_cursor(self):
        """Контекстный менеджер для получения курсора."""
        if not self._connection:
            self.connect()
        cursor = self._connection.cursor()
        try:
            yield cursor
            self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()

    def get_by_article(self, article: str) -> Optional[Product]:
        with self._get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM products WHERE article = ?",
                (article,)
            )
            row = cursor.fetchone()
            if row:
                return Product.from_dict(dict(row))
            return None

    def get_by_barcode(self, barcode: str) -> Optional[Product]:
        with self._get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM products WHERE barcode = ?",
                (barcode,)
            )
            row = cursor.fetchone()
            if row:
                return Product.from_dict(dict(row))
            return None

    def search_by_name(self, query: str, limit: int = 20) -> List[Product]:
        with self._get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM products WHERE name LIKE ? LIMIT ?",
                (f"%{query}%", limit)
            )
            rows = cursor.fetchall()
            return [Product.from_dict(dict(row)) for row in rows]

    def get_all(self, limit: Optional[int] = None) -> List[Product]:
        with self._get_cursor() as cursor:
            if limit:
                cursor.execute("SELECT * FROM products LIMIT ?", (limit,))
            else:
                cursor.execute("SELECT * FROM products")
            rows = cursor.fetchall()
            return [Product.from_dict(dict(row)) for row in rows]

    def save(self, product: Product) -> bool:
        with self._get_cursor() as cursor:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO products 
                    (article, name, barcode, description, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    product.article,
                    product.name,
                    product.barcode,
                    product.description
                ))
                return True
            except Exception as e:
                logger.error(f"Error saving product: {e}")
                return False

    def delete(self, article: str) -> bool:
        with self._get_cursor() as cursor:
            cursor.execute("DELETE FROM products WHERE article = ?", (article,))
            return cursor.rowcount > 0

    def exists(self, article: str) -> bool:
        with self._get_cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM products WHERE article = ? LIMIT 1",
                (article,)
            )
            return cursor.fetchone() is not None


class SQLiteInventoryRepository(InventoryRepository):
    """
    Реализация InventoryRepository для SQLite.
    
    Предполагает наличие таблиц:
    - inventory_documents (id, name, date, status, created_at)
    - inventory_items (id, doc_id, article, quantity, counted_quantity)
    """

    def connect(self) -> None:
        if not self._connection:
            if not self.db_path:
                raise ValueError("db_path must be provided for SQLite connection")
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row
            self._local_connection = True
            self._init_schema()

    def disconnect(self) -> None:
        if self._local_connection and self._connection:
            self._connection.close()
            self._connection = None

    def _init_schema(self) -> None:
        cursor = self._connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date DATE,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL,
                article TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                counted_quantity INTEGER DEFAULT 0,
                FOREIGN KEY (doc_id) REFERENCES inventory_documents(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_id ON inventory_items(doc_id)")
        self._connection.commit()

    @contextmanager
    def _get_cursor(self):
        if not self._connection:
            self.connect()
        cursor = self._connection.cursor()
        try:
            yield cursor
            self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()

    def create_document(self, name: str, date: Optional[str] = None) -> int:
        with self._get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO inventory_documents (name, date) VALUES (?, ?)",
                (name, date)
            )
            return cursor.lastrowid

    def add_item(self, doc_id: int, item: InventoryItem) -> bool:
        with self._get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO inventory_items (doc_id, article, quantity, counted_quantity)
                VALUES (?, ?, ?, ?)
            """, (doc_id, item.article, item.expected_quantity, item.counted_quantity))
            return True

    def get_document_items(self, doc_id: int) -> List[InventoryItem]:
        with self._get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM inventory_items WHERE doc_id = ?",
                (doc_id,)
            )
            rows = cursor.fetchall()
            return [
                InventoryItem(
                    article=row['article'],
                    expected_quantity=row['quantity'],
                    counted_quantity=row['counted_quantity']
                )
                for row in rows
            ]

    def finalize_document(self, doc_id: int) -> bool:
        with self._get_cursor() as cursor:
            cursor.execute(
                "UPDATE inventory_documents SET status = 'finalized' WHERE id = ?",
                (doc_id,)
            )
            return cursor.rowcount > 0

    def get_statistics(self, doc_id: int) -> Dict[str, Any]:
        with self._get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_items,
                    SUM(CASE WHEN quantity != counted_quantity THEN 1 ELSE 0 END) as discrepancies
                FROM inventory_items
                WHERE doc_id = ?
            """, (doc_id,))
            row = cursor.fetchone()
            return {
                'total_items': row['total_items'],
                'discrepancies': row['discrepancies'] or 0
            }


class SQLiteAddressRepository(AddressRepository):
    """
    Реализация AddressRepository для SQLite.
    
    Предполагает наличие таблиц:
    - addresses (code, description, created_at)
    - product_addresses (article, address_code, quantity)
    """

    def connect(self) -> None:
        if not self._connection:
            if not self.db_path:
                raise ValueError("db_path must be provided for SQLite connection")
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row
            self._local_connection = True
            self._init_schema()

    def disconnect(self) -> None:
        if self._local_connection and self._connection:
            self._connection.close()
            self._connection = None

    def _init_schema(self) -> None:
        cursor = self._connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS addresses (
                code TEXT PRIMARY KEY,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_addresses (
                article TEXT NOT NULL,
                address_code TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                PRIMARY KEY (article, address_code),
                FOREIGN KEY (address_code) REFERENCES addresses(code)
            )
        """)
        self._connection.commit()

    @contextmanager
    def _get_cursor(self):
        if not self._connection:
            self.connect()
        cursor = self._connection.cursor()
        try:
            yield cursor
            self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()

    def get_by_address(self, address_code: str) -> List[Product]:
        # Возвращаем заглушку, так как для полноценной реализации нужен доступ к таблице products
        # В реальном проекте здесь будет JOIN с таблицей products
        logger.warning("get_by_address requires full implementation with products table join")
        return []

    def get_product_addresses(self, article: str) -> List[Address]:
        with self._get_cursor() as cursor:
            cursor.execute(
                "SELECT address_code, quantity FROM product_addresses WHERE article = ?",
                (article,)
            )
            rows = cursor.fetchall()
            return [
                Address(code=row['address_code'], quantity=row['quantity'])
                for row in rows
            ]

    def move_product(self, article: str, from_address: str, to_address: str, quantity: int) -> bool:
        with self._get_cursor() as cursor:
            # Уменьшаем количество на старом адресе
            cursor.execute("""
                UPDATE product_addresses 
                SET quantity = quantity - ? 
                WHERE article = ? AND address_code = ?
            """, (quantity, article, from_address))
            
            # Добавляем или обновляем количество на новом адресе
            cursor.execute("""
                INSERT INTO product_addresses (article, address_code, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(article, address_code) 
                DO UPDATE SET quantity = quantity + ?
            """, (article, to_address, quantity, quantity))
            
            return True

    def add_address(self, address: Address) -> bool:
        with self._get_cursor() as cursor:
            cursor.execute(
                "INSERT OR REPLACE INTO addresses (code, description) VALUES (?, ?)",
                (address.code, address.description)
            )
            return True

    def delete_address(self, address_code: str) -> bool:
        with self._get_cursor() as cursor:
            cursor.execute("DELETE FROM addresses WHERE code = ?", (address_code,))
            cursor.execute("DELETE FROM product_addresses WHERE address_code = ?", (address_code,))
            return True


class SQLiteCountRepository(CountRepository):
    """
    Реализация CountRepository для SQLite.
    
    Предполагает наличие таблицы:
    - count_sessions (session_id, created_at, status)
    - count_items (session_id, article, quantity, counted_at)
    """

    def connect(self) -> None:
        if not self._connection:
            if not self.db_path:
                raise ValueError("db_path must be provided for SQLite connection")
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row
            self._local_connection = True
            self._init_schema()

    def disconnect(self) -> None:
        if self._local_connection and self._connection:
            self._connection.close()
            self._connection = None

    def _init_schema(self) -> None:
        cursor = self._connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS count_sessions (
                session_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS count_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                article TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                counted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES count_sessions(session_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON count_items(session_id)")
        self._connection.commit()

    @contextmanager
    def _get_cursor(self):
        if not self._connection:
            self.connect()
        cursor = self._connection.cursor()
        try:
            yield cursor
            self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()

    def start_session(self, session_id: str) -> bool:
        with self._get_cursor() as cursor:
            cursor.execute(
                "INSERT OR REPLACE INTO count_sessions (session_id) VALUES (?)",
                (session_id,)
            )
            return True

    def add_count(self, session_id: str, item: CountItem) -> bool:
        with self._get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO count_items (session_id, article, quantity) VALUES (?, ?, ?)",
                (session_id, item.article, item.quantity)
            )
            return True

    def get_session_counts(self, session_id: str) -> List[CountItem]:
        with self._get_cursor() as cursor:
            cursor.execute(
                "SELECT article, quantity FROM count_items WHERE session_id = ?",
                (session_id,)
            )
            rows = cursor.fetchall()
            return [
                CountItem(article=row['article'], quantity=row['quantity'])
                for row in rows
            ]

    def clear_session(self, session_id: str) -> bool:
        with self._get_cursor() as cursor:
            cursor.execute("DELETE FROM count_items WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM count_sessions WHERE session_id = ?", (session_id,))
            return True

    def merge_duplicates(self, session_id: str) -> bool:
        with self._get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO count_items (session_id, article, quantity)
                SELECT session_id, article, SUM(quantity)
                FROM count_items
                WHERE session_id = ?
                GROUP BY session_id, article
                HAVING COUNT(*) > 1
            """, (session_id,))
            
            # Удаляем старые дубликаты (упрощенная логика)
            cursor.execute("""
                DELETE FROM count_items
                WHERE id NOT IN (
                    SELECT MAX(id)
                    FROM count_items
                    WHERE session_id = ?
                    GROUP BY article
                )
            """, (session_id,))
            
            return True
