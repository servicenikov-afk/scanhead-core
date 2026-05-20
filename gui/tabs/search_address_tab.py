"""
Вкладка "Поиск | Адрес".
"""

import logging
from typing import Any, List

import customtkinter as ctk

from libs.domain_models import Product
from services.di_container import DIContainer
from services.interfaces import ISearchService, IProductRepository, IPrinterService, ISettingsService

from gui.search_bar import SearchBar
from gui.product_details import ProductDetails
from gui.print_queue import PrintQueue
from gui.sticker_preview import StickerPreview

logger = logging.getLogger(__name__)


class SearchAddressTab(ctk.CTkFrame):
    """Вкладка "Поиск | Адрес"."""
    
    def __init__(self, master: Any, di_container: DIContainer):
        super().__init__(master)
        self._container = di_container
        self._current_products: List[Product] = []
        
        logger.info("[SearchAddressTab] Инициализация вкладки")
        
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=3)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        
        self._create_search_bar()
        self._create_details_panel()
        self._create_bottom_panel()
        
        logger.info("[SearchAddressTab] Вкладка инициализирована")
    
    def _create_search_bar(self) -> None:
        """Создание поисковой строки."""
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=2, pady=(2, 5))
        search_frame.grid_columnconfigure(0, weight=1)
        
        settings_service = self._container.get(ISettingsService)
        config = {
            "search_font_size": settings_service.get_setting("search_font_size", 18),
            "search_autofocus": settings_service.get_setting("search_autofocus", True),
            "search_autofocus_delay": settings_service.get_setting("search_autofocus_delay", 1.0),
        }
        
        self._search_bar = SearchBar(
            search_frame,
            search_service=self._container.get(ISearchService),
            on_search_result=self._on_search_result,
            config=config
        )
        self._search_bar.grid(row=0, column=0, sticky="ew")
        
        logger.debug(f"[SearchAddressTab] Поисковая строка создана с конфигом: {config}")
    
    def _create_details_panel(self) -> None:
        """Создание панели с деталями товара."""
        details_frame = ctk.CTkFrame(self)
        details_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=3, pady=3)
        details_frame.grid_rowconfigure(0, weight=1)
        details_frame.grid_columnconfigure(0, weight=1)
        
        settings_service = self._container.get(ISettingsService)
        font_size = settings_service.get_setting("search_font_size", 18)
        
        self._product_details = ProductDetails(
            details_frame,
            product_repo=self._container.get(IProductRepository),
            on_add_to_queue=self._add_product_to_queue,
            font_size=font_size,
            details_service=self._container.get("product_details_service") if self._container.has("product_details_service") else None
        )
        self._product_details.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)
    
    def _create_bottom_panel(self) -> None:
        """Создание нижней панели: очередь + превью."""
        self._print_queue = PrintQueue(
            self,
            product_repo=self._container.get(IProductRepository),
            printer_service=self._container.get(IPrinterService),
            settings_service=self._container.get(ISettingsService)
        )
        self._print_queue.grid(row=2, column=0, sticky="nsew", padx=3, pady=3)
        
        self._sticker_preview = StickerPreview(
            self,
            printer_service=self._container.get(IPrinterService),
            settings_service=self._container.get(ISettingsService)
        )
        self._sticker_preview.grid(row=2, column=1, sticky="nsew", padx=3, pady=3)
    
    def _on_search_result(self, products: List[Product]) -> None:
        """Обработчик результатов поиска от SearchBar."""
        self.update_products(products)
    
    def _add_product_to_queue(self, product: Product) -> None:
        """Добавить товар в очередь печати."""
        logger.info(f"[SearchAddressTab] Добавление товара {product.article} в очередь")
        self._print_queue.add_item(product)
    
    def update_products(self, products: List[Product]) -> None:
        """
        Обновление списка товаров после поиска.
        
        :param products: Список найденных товаров
        """
        self._current_products = products
        logger.info(f"[SearchAddressTab] Обновление товаров, найдено: {len(products)}")
        
        if products:
            # Показываем первый товар в деталях
            self._product_details.set_product(products[0])
            
            # Добавляем товары в очередь
            self._print_queue.set_products(products)
            
            # Обновляем превью для первого товара
            self._sticker_preview.set_product(products[0])
        else:
            # Очищаем всё
            self._product_details.clear()
            self._print_queue.clear()
            self._sticker_preview.clear()
    
    def get_current_product(self) -> Product | None:
        """Получение текущего отображаемого товара."""
        return self._product_details.get_current_product()
    
    def on_setting_changed(self, key: str, value: Any) -> None:
        """Обработчик изменения настроек."""
        if key.startswith("search_"):
            # Обновить конфиг и применить в SearchBar
            self._search_bar.apply_settings({key: value})
            logger.info(f"[SearchAddressTab] Применена настройка {key}={value}")
