"""Заглушка репозитория товаров."""

import logging
import time
from typing import Optional

import sys
sys.path.insert(0, '/workspace')

from libs.domain_models import Product, Address
from gui.services.interfaces.product_repo import IProductRepository


logger = logging.getLogger(__name__)


class StubProductRepository(IProductRepository):
    """Заглушка репозитория товаров."""

    def __init__(self) -> None:
        self._test_address = Address(
            code="A-01-01",
            description="Стеллаж 1, Ячейка 1",
            quantity=100
        )

    def update_field(self, product_id: int, field_name: str, value: str) -> bool:
        """Эмуляция обновления поля."""
        logger.info(f"[StubProductRepo] {product_id}: {field_name} = '{value}'")
        time.sleep(0.1)
        return True

    def get_address_for_product(self, product_id: int) -> Optional[Address]:
        """Возвращает тестовый адрес."""
        return self._test_address
