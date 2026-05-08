"""
Модуль репозиториев для доступа к данным.

Предоставляет абстрактные интерфейсы и SQLite-реализации
для работы с продуктами, инвентаризацией, адресами и пересчетом.
"""

from libs.repository.interfaces import (
    BaseRepository,
    ProductRepository,
    InventoryRepository,
    AddressRepository,
    CountRepository
)

from libs.repository.sqlite_impl import (
    SQLiteProductRepository,
    SQLiteInventoryRepository,
    SQLiteAddressRepository,
    SQLiteCountRepository
)

__all__ = [
    # Интерфейсы
    'BaseRepository',
    'ProductRepository',
    'InventoryRepository',
    'AddressRepository',
    'CountRepository',
    
    # Реализации
    'SQLiteProductRepository',
    'SQLiteInventoryRepository',
    'SQLiteAddressRepository',
    'SQLiteCountRepository'
]
