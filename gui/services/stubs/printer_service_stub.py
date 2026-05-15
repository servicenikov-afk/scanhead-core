"""Заглушка сервиса печати."""

import logging
from typing import List, Any, Optional

import sys
sys.path.insert(0, '/workspace')

from libs.domain_models import Product
from gui.services.interfaces.printer_service import IPrinterService


logger = logging.getLogger(__name__)


class StubPrinterService(IPrinterService):
    """Заглушка сервиса печати."""

    def print_sticker(self, product: Product, quantity: int = 1) -> bool:
        logger.info(f"[StubPrinterService] Печать: {product.article} ×{quantity}")
        return True

    def print_batch(self, products: List[Product]) -> bool:
        logger.info(f"[StubPrinterService] Пачка: {len(products)} этикеток")
        for p in products:
            logger.info(f"  - {p.article}: {p.name}")
        return True

    def generate_sticker(self, product: Product, preset: dict) -> Optional[Any]:
        """Генерация изображения стикера (заглушка)."""
        logger.debug(f"[StubPrinterService] Генерация превью для {product.article}")
        # Возвращаем None, так как это заглушка
        # В реальном сервисе здесь будет вызов StickerGenerator из libs/printing
        return None

    def print_queue(self, products: List[Product], one_by_one: bool = False) -> bool:
        """Печать очереди товаров."""
        if one_by_one:
            logger.info(f"[StubPrinterService] Печать очереди по одному: {len(products)} товаров")
        else:
            logger.info(f"[StubPrinterService] Печать очереди одним документом: {len(products)} товаров")
        return True
