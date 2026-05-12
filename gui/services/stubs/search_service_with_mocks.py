"""Поиск с использованием моков (для разработки/тестов)."""

import threading
import queue
import logging
from typing import Callable, List, Optional

from libs.domain_models import Product
from ..interfaces.search_service import ISearchService
from ..interfaces.mock_data_service import IMockDataService

logger = logging.getLogger(__name__)


class SearchServiceWithMocks(ISearchService):
    """Поиск с использованием моков (для разработки/тестов)."""

    def __init__(self, mock_service: IMockDataService):
        self._mocks = mock_service
        self._queue = queue.Queue()
        logger.info("[SearchServiceWithMocks] Инициализация с моками")

    def search_async(self, query: str, callback: Callable[[List[Product]], None]) -> None:
        """Асинхронный поиск по мокам."""

        def worker():
            results = self._search_sync(query)
            self._queue.put(results)

        threading.Thread(target=worker, daemon=True).start()
        self._check_queue(callback)

    def _check_queue(self, callback: Callable[[List[Product]], None]) -> None:
        """Проверка очереди результатов (вызывается из главного потока)."""
        try:
            results = self._queue.get_nowait()
            callback(results)
        except queue.Empty:
            import tkinter as tk

            root = tk._default_root
            if root:
                root.after(50, lambda: self._check_queue(callback))

    def _search_sync(self, query: str) -> List[Product]:
        """Синхронный поиск по мокам."""
        if not query.strip():
            return []

        all_products = self._mocks.load_products()
        query_lower = query.lower()

        results = []
        for product in all_products:
            if (
                (product.article and query_lower in product.article.lower())
                or (product.article2 and query_lower in product.article2.lower())
                or (product.name and query_lower in product.name.lower())
            ):
                results.append(product)

        logger.info(f"[SearchServiceWithMocks] Найдено {len(results)} товаров по запросу '{query}'")
        return results

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Получить товар по ID (заглушка, т.к. в моках нет ID)."""
        logger.warning("[SearchServiceWithMocks] get_product_by_id не поддерживается для моков")
        return None
