"""Интерфейс для загрузки тестовых данных."""

from abc import ABC, abstractmethod
from typing import List, Optional

from libs.domain_models import Product, Address


class IMockDataService(ABC):
    """Интерфейс для загрузки тестовых данных."""

    @abstractmethod
    def load_products(self) -> List[Product]:
        """Загрузить список тестовых товаров."""
        pass

    @abstractmethod
    def load_addresses(self) -> List[Address]:
        """Загрузить список тестовых адресов."""
        pass

    @abstractmethod
    def get_product_by_article(self, article: str) -> Optional[Product]:
        """Найти товар по артикулу в моках."""
        pass
