"""Заглушка сервиса поиска товаров."""

import threading
import logging
from typing import Callable, List, Optional

import sys
sys.path.insert(0, '/workspace')

from libs.domain_models import Product
from gui.services.interfaces.search_service import ISearchService


logger = logging.getLogger(__name__)


class StubSearchService(ISearchService):
    """Заглушка сервиса поиска. Возвращает тестовые данные."""

    def __init__(self) -> None:
        self._test_products = [
            Product(
                id=1,
                article="ART-001",
                name="Товар тестовый 1",
                barcodes=["4600000000001", "4600000000002"],
            ),
            Product(
                id=2,
                article="ART-002",
                name="Товар тестовый 2",
                barcodes=["4600000000003"],
            ),
            Product(
                id=3,
                article="ART-003",
                name="Товар тестовый 3",
                barcodes=["4600000000004", "4600000000005"],
            ),
        ]

    def search_async(self, query: str, callback: Callable[[List[Product]], None]) -> None:
        """Поиск с эмуляцией задержки."""
        logger.info(f"[StubSearchService] Поиск: '{query}'")

        def worker() -> None:
            threading.Event().wait(0.3)  # Эмуляция задержки
            if not query.strip():
                results = []
            else:
                query_lower = query.lower()
                results = [
                    p for p in self._test_products
                    if query_lower in p.article.lower()
                    or query_lower in p.name.lower()
                    or any(query_lower in bc for bc in p.barcodes)
                ]
            logger.info(f"[StubSearchService] Найдено: {len(results)}")
            callback(results)

        threading.Thread(target=worker, daemon=True).start()

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Получение товара по ID."""
        for p in self._test_products:
            if p.id == product_id:
                return p
        return None
