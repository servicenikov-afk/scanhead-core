"""Интерфейс сервиса печати."""

from abc import ABC, abstractmethod
from typing import List

import sys
sys.path.insert(0, '/workspace')

from libs.domain_models import Product


class IPrinterService(ABC):
    """Интерфейс сервиса печати этикеток."""

    @abstractmethod
    def print_sticker(self, product: Product, quantity: int = 1) -> bool:
        """Печать одной этикетки."""
        pass

    @abstractmethod
    def print_batch(self, products: List[Product]) -> bool:
        """Печать пачки этикеток (многостраничный документ)."""
        pass
