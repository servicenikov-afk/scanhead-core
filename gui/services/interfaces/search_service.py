"""Интерфейс сервиса поиска товаров."""

from abc import ABC, abstractmethod
from typing import Callable, List, Optional

import sys
sys.path.insert(0, '/workspace')

from libs.domain_models import Product


class ISearchService(ABC):
    """Интерфейс сервиса поиска товаров."""

    @abstractmethod
    def search_async(self, query: str, callback: Callable[[List[Product]], None]) -> None:
        """Поиск товаров по запросу (асинхронно)."""
        pass

    @abstractmethod
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Получение товара по ID."""
        pass
