"""Заглушка сервиса печати."""

import logging
from typing import List

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
