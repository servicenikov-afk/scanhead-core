"""
Заглушки (stubs) для сервисов.
Используются для разработки GUI без реальной бизнес-логики.
"""

import logging
from typing import Callable, List, Optional, Any
from PIL import Image

from libs.domain_models.models import Product, Address, InventoryItem
from services.interfaces import (
    ISearchService,
    IProductRepository,
    IImageService,
    IPrinterService,
    ISettingsService,
    IInventoryService,
)

logger = logging.getLogger(__name__)


class StubSearchService(ISearchService):
    """Заглушка сервиса поиска."""
    
    def __init__(self):
        self._test_products = [
            Product(
                id=1,
                article="ART001",
                name="Тестовый товар 1",
                barcodes=["4600000000001", "4600000000002"],
                addresses=[Address(code="A01", description="Стеллаж 1, Полка A")]
            ),
            Product(
                id=2,
                article="ART002",
                name="Тестовый товар 2",
                barcodes=["4600000000003"],
                addresses=[Address(code="B02", description="Стеллаж 2, Полка B")]
            ),
        ]
    
    def search_async(self, query: str, callback: Callable[[List[Product]], None]) -> None:
        logger.info(f"[StubSearchService] Поиск по запросу: '{query}'")
        # Имитация задержки поиска
        import threading
        import time
        
        def worker():
            time.sleep(0.1)  # Имитация задержки
            results = [p for p in self._test_products if 
                      query.lower() in p.article.lower() or 
                      query.lower() in p.name.lower()]
            callback(results)
        
        threading.Thread(target=worker, daemon=True).start()
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        logger.info(f"[StubSearchService] Получение товара по ID: {product_id}")
        for product in self._test_products:
            if product.id == product_id:
                return product
        return None


class StubProductRepository(IProductRepository):
    """Заглушка репозитория товаров."""
    
    def update_field(self, product_id: int, field_name: str, value: Any) -> bool:
        logger.info(f"[StubProductRepository] Обновление поля {field_name}={value} для товара {product_id}")
        # В заглушке просто логируем, в реальности будет вызов ядра
        return True
    
    def get_address_for_product(self, product_id: int) -> Optional[Address]:
        logger.info(f"[StubProductRepository] Получение адреса для товара {product_id}")
        # Возвращаем тестовый адрес
        return Address(code="TEST01", description="Тестовый адрес хранения")


class StubImageService(IImageService):
    """Заглушка сервиса изображений."""
    
    def load_image_async(self, url: str, callback: Callable[[Optional[Any]], None]) -> None:
        logger.info(f"[StubImageService] Загрузка изображения из {url}")
        # В заглушке сразу возвращаем None
        callback(None)
    
    def get_placeholder(self) -> Any:
        logger.info("[StubImageService] Получение заглушки изображения")
        # Создаём простое серое изображение-заглушку
        return Image.new('RGB', (200, 200), color='#808080')


class StubPrinterService(IPrinterService):
    """Заглушка сервиса печати."""
    
    def generate_sticker(self, product: Product, preset: dict) -> Any:
        logger.info(f"[StubPrinterService] Генерация стикера для товара {product.article}")
        # Возвращаем заглушку изображения
        img = Image.new('RGB', (400, 300), color='white')
        return img
    
    def print_sticker(self, image: Any, copies: int = 1) -> bool:
        logger.info(f"[StubPrinterService] Печать стикера, копий: {copies}")
        return True
    
    def print_queue(self, products: List[Product], one_by_one: bool = False) -> bool:
        logger.info(f"[StubPrinterService] Печать очереди, товаров: {len(products)}, по одному: {one_by_one}")
        return True


class StubSettingsService(ISettingsService):
    """Заглушка сервиса настроек."""
    
    def __init__(self):
        self._settings = {
            'theme': 'Dark',
            'language': 'ru',
            'columns_visible': ['article', 'article2', 'name', 'address'],
            'columns_order': ['article', 'article2', 'name', 'address'],
        }
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        logger.debug(f"[StubSettingsService] Получение настройки: {key}")
        return self._settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        logger.debug(f"[StubSettingsService] Сохранение настройки: {key}={value}")
        self._settings[key] = value
    
    def get_column_config(self) -> dict:
        return {
            'visible': self._settings.get('columns_visible', []),
            'order': self._settings.get('columns_order', []),
        }
    
    def set_column_config(self, config: dict) -> None:
        self._settings['columns_visible'] = config.get('visible', [])
        self._settings['columns_order'] = config.get('order', [])


class StubInventoryService(IInventoryService):
    """Заглушка сервиса инвентаризации."""
    
    def import_inventory(self, file_path: str) -> bool:
        logger.info(f"[StubInventoryService] Импорт инвентаризации из {file_path}")
        return True
    
    def export_report(self, file_path: str) -> bool:
        logger.info(f"[StubInventoryService] Экспорт отчёта в {file_path}")
        return True
    
    def start_scanning(self) -> None:
        logger.info("[StubInventoryService] Запуск сканирования")
    
    def stop_scanning(self) -> None:
        logger.info("[StubInventoryService] Остановка сканирования")