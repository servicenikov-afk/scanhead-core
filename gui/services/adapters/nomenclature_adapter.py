"""Адаптер для работы с основной базой номенклатуры."""
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
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
    # Дополнительные поля из css_export
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
    
    def __init__(self, db_path: str = "data/db/nomenclature.db"):
        self.db_path = Path(db_path)
        self._connection: Optional[sqlite3.Connection] = None
        
    def _get_connection(self) -> sqlite3.Connection:
        """Получить соединение с БД (ленивая инициализация)."""
        if self._connection is None:
            if not self.db_path.exists():
                logger.warning(f"[NomenclatureAdapter] БД не найдена: {self.db_path}")
                return self._create_mock_connection()
            
            self._connection = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            self._connection.row_factory = sqlite3.Row
            logger.info(f"[NomenclatureAdapter] Подключено к {self.db_path} (read-only)")
        
        return self._connection
    
    def _create_mock_connection(self) -> sqlite3.Connection:
        """Создать временную БД с моками для тестов."""
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                article TEXT PRIMARY KEY,
                name TEXT,
                article2 TEXT,
                barcodes TEXT
            )
        """)
        # Тестовые данные
        test_data = [
            ('560.0000.309', 'Распределитель выдачи молока для к/м A200', '', '460001'),
            ('560.0004.669', 'Уплотнительное кольцо 3,4x1,9 мм для к/м Flair', '', '460002'),
            ('560.0004.907', 'Уплотнение верхнего поршня 36,09x3,53 для к/м Flai', '', '460003'),
            ('560.0005.123', 'Тестовый товар', '', '460004'),
        ]
        cursor.executemany(
            "INSERT OR REPLACE INTO products (article, name, article2, barcodes) VALUES (?, ?, ?, ?)",
            test_data
        )
        conn.commit()
        logger.info("[NomenclatureAdapter] Создана тестовая БД в памяти")
        return conn
    
    def search(self, query: str) -> List[Product]:
        """Поиск товаров по артикулу, названию или штрихкоду."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        search_pattern = f"%{query}%"
        sql = """
            SELECT article, name, article2, barcodes
            FROM products
            WHERE article LIKE ? OR name LIKE ? OR barcodes LIKE ?
            LIMIT 50
        """
        
        try:
            cursor.execute(sql, (search_pattern, search_pattern, search_pattern))
            rows = cursor.fetchall()
            products = [
                Product(
                    article=row['article'],
                    name=row['name'],
                    article2=row['article2'],
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
            SELECT article, name, article2, barcodes
            FROM products
            WHERE article = ?
        """
        
        try:
            cursor.execute(sql, (article,))
            row = cursor.fetchone()
            if row:
                return Product(
                    article=row['article'],
                    name=row['name'],
                    article2=row['article2'],
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
