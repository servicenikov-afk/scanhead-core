"""
Вкладка "Поиск | Адрес".
Содержит: детали товара, очередь печати, превью стикера.
"""

import logging
from typing import Any, List

import customtkinter as ctk

from services.di_container import DIContainer
from services.interfaces import ISearchService, IProductRepository, IPrinterService, ISettingsService
from libs.domain_models.models import Product

from gui.product_details import ProductDetails
from gui.print_queue import PrintQueue
from gui.sticker_preview import StickerPreview

logger = logging.getLogger(__name__)


class SearchAddressTab(ctk.CTkFrame):
    """
    Вкладка "Поиск | Адрес".
    
    Структура:
    ┌──────────────────┬─────────────────────────────┐
    │                  │                             │
    │  Детали товара   │     Превью стикера          │
    │  (артикул,       │     (макет + кнопка         │
    │   название,      │      редактора)             │
    │   адрес)         │                             │
    │                  ├─────────────────────────────┤
    │                  │                             │
    │                  │    Очередь печати           │
    │                  │    (Treeview + кнопки)      │
    │                  │                             │
    └──────────────────┴─────────────────────────────┘
    """
    
    def __init__(self, master: Any, container: DIContainer):
        super().__init__(master)
        self._container = container
        self._current_products: List[Product] = []
        
        logger.info("[SearchAddressTab] Инициализация вкладки")
        
        # Настраиваем сетку
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)  # Правая часть шире
        
        # Левая панель: детали товара
        self._create_left_panel()
        
        # Правая панель: превью + очередь
        self._create_right_panel()
        
        logger.info("[SearchAddressTab] Вкладка инициализирована")
    
    def _create_left_panel(self) -> None:
        """Создание левой панели с деталями товара."""
        left_frame = ctk.CTkFrame(self)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        # Детали товара
        self._product_details = ProductDetails(
            left_frame,
            product_repo=self._container.get(IProductRepository)
        )
        self._product_details.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        logger.debug("[SearchAddressTab] Левая панель создана")
    
    def _create_right_panel(self) -> None:
        """Создание правой панели с превью и очередью."""
        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        right_frame.grid_rowconfigure(0, weight=1)  # Превью
        right_frame.grid_rowconfigure(1, weight=2)  # Очередь (больше места)
        right_frame.grid_columnconfigure(0, weight=1)
        
        # Превью стикера (верх)
        self._sticker_preview = StickerPreview(
            right_frame,
            printer_service=self._container.get(IPrinterService),
            settings_service=self._container.get(ISettingsService)
        )
        self._sticker_preview.grid(row=0, column=0, sticky="nsew", padx=5, pady=(5, 2))
        
        # Очередь печати (низ)
        self._print_queue = PrintQueue(
            right_frame,
            product_repo=self._container.get(IProductRepository),
            printer_service=self._container.get(IPrinterService),
            settings_service=self._container.get(ISettingsService)
        )
        self._print_queue.grid(row=1, column=0, sticky="nsew", padx=5, pady=(2, 5))
        
        logger.debug("[SearchAddressTab] Правая панель создана")
    
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
