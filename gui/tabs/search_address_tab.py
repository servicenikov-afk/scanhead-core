"""
Вкладка "Поиск | Адрес".
Содержит: детали товара, очередь печати, превью стикера.
"""

import logging
from typing import Any, Dict, List

import customtkinter as ctk

from libs.domain_models import Product

from gui.search_bar import SearchBar
from gui.product_details import ProductDetails
from gui.print_queue import PrintQueue
from gui.sticker_preview import StickerPreview

logger = logging.getLogger(__name__)


class SearchAddressTab(ctk.CTkFrame):
    """
    Вкладка "Поиск | Адрес".
    
    Структура:
    ┌───────────────────────────────────────────────┐
    │  [Поиск: введите артикул или название...]     │  <- Поисковая строка
    ├──────────────────┬────────────────────────────┤
    │                  │                            │
    │  Детали товара   │     Превью стикера         │
    │  (артикул,       │     (макет + кнопка        │
    │   название,      │      редактора)            │
    │   адрес)         │                            │
    │  [➕ В очередь]  ├────────────────────────────┤
    │                  │                            │
    │                  │    Очередь печати          │
    │                  │    (Treeview + кнопки)     │
    │                  │                            │
    └──────────────────┴────────────────────────────┘
    """
    
    def __init__(self, master: Any, services: Dict[str, Any]):
        super().__init__(master)
        self._services = services
        self._current_products: List[Product] = []
        
        logger.info("[SearchAddressTab] Инициализация вкладки")
        
        # Настраиваем сетку для новой компоновки
        self.grid_rowconfigure(0, weight=0)  # Поиск - фиксированная высота
        self.grid_rowconfigure(1, weight=3)  # Детали товара: 75% высоты
        self.grid_rowconfigure(2, weight=1)  # Очередь+Превью: 25% высоты
        self.grid_columnconfigure(0, weight=3)  # Очередь: 75% ширины
        self.grid_columnconfigure(1, weight=1)  # Превью: 25% ширины
        
        # Поисковая строка (Row 0)
        self._create_search_bar()
        
        # Детали товара (Row 1, на всю ширину)
        self._create_details_panel()
        
        # Нижняя панель: очередь + превью (Row 2)
        self._create_bottom_panel()
        
        logger.info("[SearchAddressTab] Вкладка инициализирована")
    
    def _create_search_bar(self) -> None:
        """Создание поисковой строки на вкладке."""
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=2, pady=(2, 5))
        search_frame.grid_columnconfigure(0, weight=1)
        
        self._search_bar = SearchBar(
            search_frame,
            search_service=self._services.get("search_service"),
            on_search_result=self._on_search_result
        )
        self._search_bar.grid(row=0, column=0, sticky="ew")
        
        logger.debug("[SearchAddressTab] Поисковая строка создана")
    
    def _create_details_panel(self) -> None:
        """Создание панели с деталями товара (на всю ширину)."""
        details_frame = ctk.CTkFrame(self)
        details_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=3, pady=3)
        details_frame.grid_rowconfigure(0, weight=1)
        details_frame.grid_columnconfigure(0, weight=1)
        
        # Детали товара
        self._product_details = ProductDetails(
            details_frame,
            product_repo=self._services.get("product_repo"),
            on_add_to_queue=self._add_product_to_queue
        )
        self._product_details.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)
        
        logger.debug("[SearchAddressTab] Панель деталей создана")
    
    def _create_bottom_panel(self) -> None:
        """Создание нижней панели: очередь (слева) + превью (справа)."""
        # Очередь печати (Row 2, Col 0 - 75% ширины)
        self._print_queue = PrintQueue(
            self,
            product_repo=self._services.get("product_repo"),
            printer_service=self._services.get("printer_service"),
            settings_service=self._services.get("settings_service")
        )
        self._print_queue.grid(row=2, column=0, sticky="nsew", padx=3, pady=3)
        
        # Превью стикера (Row 2, Col 1 - 25% ширины)
        self._sticker_preview = StickerPreview(
            self,
            printer_service=self._services.get("printer_service"),
            settings_service=self._services.get("settings_service")
        )
        self._sticker_preview.grid(row=2, column=1, sticky="nsew", padx=3, pady=3)
        
        logger.debug("[SearchAddressTab] Нижняя панель создана")
    
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
