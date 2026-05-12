"""Интерфейс репозитория товаров."""

from abc import ABC, abstractmethod
from typing import Optional

import sys
sys.path.insert(0, '/workspace')

from libs.domain_models import Product, Address


class IProductRepository(ABC):
    """Интерфейс репозитория товаров."""

    @abstractmethod
    def update_field(self, product_id: int, field_name: str, value: str) -> bool:
        """Универсальное обновление поля товара."""
        pass

    @abstractmethod
    def get_address_for_product(self, product_id: int) -> Optional[Address]:
        """Получение адреса хранения для товара."""
        pass
