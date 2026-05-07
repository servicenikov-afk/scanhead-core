"""
DB Manager Core
Ядро системы управления базами данных и источниками данных.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, TypeVar, Generic
from enum import Enum
from pathlib import Path

from .models import DataRecord


class DataSourceType(Enum):
    """Типы источников данных."""
    SQLITE = "sqlite"
    POSTGRES = "postgres"
    CSV = "csv"
    XML = "xml"
    XLSX = "xlsx"
    XLS = "xls"
    SQL = "sql"  # Прямые SQL-запросы


T = TypeVar('T', bound=DataRecord)


class DataSource(ABC, Generic[T]):
    """Абстрактный базовый класс для источников данных."""

    @abstractmethod
    def connect(self) -> bool:
        """Установить соединение с источником данных."""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Разорвать соединение с источником данных."""
        pass

    @abstractmethod
    def read_all(self) -> List[T]:
        """Прочитать все записи из источника."""
        pass

    @abstractmethod
    def read_by_id(self, record_id: int) -> Optional[T]:
        """Прочитать запись по идентификатору."""
        pass

    @abstractmethod
    def write(self, record: T) -> bool:
        """Записать запись в источник."""
        pass

    @abstractmethod
    def update(self, record: T) -> bool:
        """Обновить существующую запись."""
        pass

    @abstractmethod
    def delete(self, record_id: int) -> bool:
        """Удалить запись по идентификатору."""
        pass

    @abstractmethod
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Выполнить произвольный запрос к источнику данных."""
        pass


class SQLiteDataSource(DataSource[DataRecord]):
    """Реализация источника данных для SQLite."""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.connection = None
        self.cursor = None

    def connect(self) -> bool:
        """Подключиться к SQLite базе данных."""
        try:
            import sqlite3
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            self._create_tables_if_not_exists()
            return True
        except Exception as e:
            print(f"Error connecting to SQLite: {e}")
            return False

    def disconnect(self) -> bool:
        """Отключиться от базы данных."""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None
        return True

    def _create_tables_if_not_exists(self):
        """Создать таблицы если они не существуют."""
        if not self.cursor:
            return
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article TEXT NOT NULL,
                barcode TEXT,
                name_original TEXT,
                name_sticker TEXT,
                article_old TEXT,
                articles_alternative TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        ''')
        self.connection.commit()

    def read_all(self) -> List[DataRecord]:
        """Прочитать все записи."""
        if not self.cursor:
            return []
        
        self.cursor.execute('SELECT * FROM data_records')
        rows = self.cursor.fetchall()
        return [self._row_to_record(row) for row in rows]

    def read_by_id(self, record_id: int) -> Optional[DataRecord]:
        """Прочитать запись по ID."""
        if not self.cursor:
            return None
        
        self.cursor.execute('SELECT * FROM data_records WHERE id = ?', (record_id,))
        row = self.cursor.fetchone()
        return self._row_to_record(row) if row else None

    def write(self, record: DataRecord) -> bool:
        """Записать новую запись."""
        if not self.cursor or not self.connection:
            return False
        
        try:
            import json
            self.cursor.execute('''
                INSERT INTO data_records 
                (article, barcode, name_original, name_sticker, article_old, 
                 articles_alternative, tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.article,
                record.barcode,
                record.name_original,
                record.name_sticker,
                record.article_old,
                json.dumps(record.articles_alternative),
                json.dumps(record.tags),
                json.dumps(record.metadata),
            ))
            self.connection.commit()
            record.id = self.cursor.lastrowid
            return True
        except Exception as e:
            print(f"Error writing record: {e}")
            return False

    def update(self, record: DataRecord) -> bool:
        """Обновить существующую запись."""
        if not self.cursor or not self.connection or not record.id:
            return False
        
        try:
            import json
            self.cursor.execute('''
                UPDATE data_records SET
                    article = ?, barcode = ?, name_original = ?, name_sticker = ?,
                    article_old = ?, articles_alternative = ?, tags = ?,
                    metadata = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                record.article,
                record.barcode,
                record.name_original,
                record.name_sticker,
                record.article_old,
                json.dumps(record.articles_alternative),
                json.dumps(record.tags),
                json.dumps(record.metadata),
                record.id,
            ))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error updating record: {e}")
            return False

    def delete(self, record_id: int) -> bool:
        """Удалить запись."""
        if not self.cursor or not self.connection:
            return False
        
        try:
            self.cursor.execute('DELETE FROM data_records WHERE id = ?', (record_id,))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error deleting record: {e}")
            return False

    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Выполнить произвольный SQL запрос."""
        if not self.cursor:
            return []
        
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error executing query: {e}")
            return []

    def _row_to_record(self, row) -> DataRecord:
        """Преобразовать строку результата в DataRecord."""
        import json
        from datetime import datetime
        
        if not row:
            return None
        
        articles_alt = []
        tags = []
        metadata = {}
        
        try:
            if row['articles_alternative']:
                articles_alt = json.loads(row['articles_alternative'])
            if row['tags']:
                tags = json.loads(row['tags'])
            if row['metadata']:
                metadata = json.loads(row['metadata'])
        except (json.JSONDecodeError, TypeError):
            pass
        
        return DataRecord(
            id=row['id'],
            article=row['article'],
            barcode=row['barcode'],
            name_original=row['name_original'],
            name_sticker=row['name_sticker'],
            article_old=row['article_old'],
            articles_alternative=articles_alt,
            tags=tags,
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
            metadata=metadata,
        )


class CSVDataSource(DataSource[DataRecord]):
    """Заглушка для CSV источника данных."""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
    
    def connect(self) -> bool:
        raise NotImplementedError("CSVDataSource.connect требует реализации")
    
    def disconnect(self) -> bool:
        return True
    
    def read_all(self) -> List[DataRecord]:
        raise NotImplementedError("CSVDataSource.read_all требует реализации")
    
    def read_by_id(self, record_id: int) -> Optional[DataRecord]:
        raise NotImplementedError("CSVDataSource.read_by_id требует реализации")
    
    def write(self, record: DataRecord) -> bool:
        raise NotImplementedError("CSVDataSource.write требует реализации")
    
    def update(self, record: DataRecord) -> bool:
        raise NotImplementedError("CSVDataSource.update требует реализации")
    
    def delete(self, record_id: int) -> bool:
        raise NotImplementedError("CSVDataSource.delete требует реализации")
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError("CSVDataSource.execute_query требует реализации")


# Заглушки для других источников данных
class PostgresDataSource(DataSource[DataRecord]):
    """Заглушка для PostgreSQL источника данных."""
    def connect(self) -> bool:
        raise NotImplementedError("PostgresDataSource требует реализации")
    def disconnect(self) -> bool:
        return True
    def read_all(self) -> List[DataRecord]:
        raise NotImplementedError("PostgresDataSource требует реализации")
    def read_by_id(self, record_id: int) -> Optional[DataRecord]:
        raise NotImplementedError("PostgresDataSource требует реализации")
    def write(self, record: DataRecord) -> bool:
        raise NotImplementedError("PostgresDataSource требует реализации")
    def update(self, record: DataRecord) -> bool:
        raise NotImplementedError("PostgresDataSource требует реализации")
    def delete(self, record_id: int) -> bool:
        raise NotImplementedError("PostgresDataSource требует реализации")
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError("PostgresDataSource требует реализации")


class XMLDataSource(DataSource[DataRecord]):
    """Заглушка для XML источника данных."""
    def connect(self) -> bool:
        raise NotImplementedError("XMLDataSource требует реализации")
    def disconnect(self) -> bool:
        return True
    def read_all(self) -> List[DataRecord]:
        raise NotImplementedError("XMLDataSource требует реализации")
    def read_by_id(self, record_id: int) -> Optional[DataRecord]:
        raise NotImplementedError("XMLDataSource требует реализации")
    def write(self, record: DataRecord) -> bool:
        raise NotImplementedError("XMLDataSource требует реализации")
    def update(self, record: DataRecord) -> bool:
        raise NotImplementedError("XMLDataSource требует реализации")
    def delete(self, record_id: int) -> bool:
        raise NotImplementedError("XMLDataSource требует реализации")
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError("XMLDataSource требует реализации")


class XLSXDataSource(DataSource[DataRecord]):
    """Заглушка для XLSX источника данных."""
    def connect(self) -> bool:
        raise NotImplementedError("XLSXDataSource требует реализации")
    def disconnect(self) -> bool:
        return True
    def read_all(self) -> List[DataRecord]:
        raise NotImplementedError("XLSXDataSource требует реализации")
    def read_by_id(self, record_id: int) -> Optional[DataRecord]:
        raise NotImplementedError("XLSXDataSource требует реализации")
    def write(self, record: DataRecord) -> bool:
        raise NotImplementedError("XLSXDataSource требует реализации")
    def update(self, record: DataRecord) -> bool:
        raise NotImplementedError("XLSXDataSource требует реализации")
    def delete(self, record_id: int) -> bool:
        raise NotImplementedError("XLSXDataSource требует реализации")
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError("XLSXDataSource требует реализации")


class DBManager:
    """
    Менеджер баз данных.
    Управляет подключением к различным источникам данных и предоставляет единый интерфейс.
    """

    def __init__(self):
        self.data_sources: Dict[DataSourceType, DataSource] = {}
        self.active_source: Optional[DataSource] = None

    def register_source(self, source_type: DataSourceType, source: DataSource):
        """Зарегистрировать источник данных."""
        self.data_sources[source_type] = source

    def set_active_source(self, source_type: DataSourceType) -> bool:
        """Установить активный источник данных."""
        if source_type not in self.data_sources:
            return False
        
        source = self.data_sources[source_type]
        if source.connect():
            self.active_source = source
            return True
        return False

    def get_active_source(self) -> Optional[DataSource]:
        """Получить активный источник данных."""
        return self.active_source

    def read_all(self) -> List[DataRecord]:
        """Прочитать все записи из активного источника."""
        if not self.active_source:
            return []
        return self.active_source.read_all()

    def read_by_id(self, record_id: int) -> Optional[DataRecord]:
        """Прочитать запись по ID из активного источника."""
        if not self.active_source:
            return None
        return self.active_source.read_by_id(record_id)

    def write(self, record: DataRecord) -> bool:
        """Записать запись в активный источник."""
        if not self.active_source:
            return False
        return self.active_source.write(record)

    def update(self, record: DataRecord) -> bool:
        """Обновить запись в активном источнике."""
        if not self.active_source:
            return False
        return self.active_source.update(record)

    def delete(self, record_id: int) -> bool:
        """Удалить запись из активного источника."""
        if not self.active_source:
            return False
        return self.active_source.delete(record_id)

    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Выполнить запрос к активному источнику."""
        if not self.active_source:
            return []
        return self.active_source.execute_query(query, params)

    def close_all(self):
        """Закрыть все подключения."""
        for source in self.data_sources.values():
            source.disconnect()
        self.active_source = None
