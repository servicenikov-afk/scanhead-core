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
        
        # Настраиваем сетку
        self.grid_rowconfigure(1, weight=1)  # Основной контент растягивается
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)  # Правая часть шире
        
        # Поисковая строка (Row 0)
        self._create_search_bar()
        
        # Левая панель: детали товара
        self._create_left_panel()
        
        # Правая панель: превью + очередь
        self._create_right_panel()
        
        logger.info("[SearchAddressTab] Вкладка инициализирована")
    
    def _create_search_bar(self) -> None:
        """Создание поисковой строки на вкладке."""
        search_frame = ctk.CTkFrame(self)
        search_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        search_frame.grid_columnconfigure(0, weight=1)
        
        self._search_bar = SearchBar(
            search_frame,
            search_service=self._services.get("search_service"),
            on_search_result=self._on_search_result
        )
        self._search_bar.grid(row=0, column=0, sticky="ew")
        
        logger.debug("[SearchAddressTab] Поисковая строка создана")
    
    def _create_left_panel(self) -> None:
        """Создание левой панели с деталями товара."""
        left_frame = ctk.CTkFrame(self)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_rowconfigure(1, weight=0)  # Для кнопки
        left_frame.grid_columnconfigure(0, weight=1)
        
        # Детали товара (верх)
        self._product_details = ProductDetails(
            left_frame,
            product_repo=self._services.get("product_repo")
        )
        self._product_details.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Кнопка "В очередь печати" (низ)
        add_to_queue_btn = ctk.CTkButton(
            left_frame,
            text="➕ В очередь печати",
            command=self._add_current_to_queue,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        add_to_queue_btn.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        
        logger.debug("[SearchAddressTab] Левая панель создана")
    
    def _create_right_panel(self) -> None:
        """Создание правой панели с превью и очередью."""
        right_frame = ctk.CTkFrame(self)
        right_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        right_frame.grid_rowconfigure(0, weight=1)  # Превью
        right_frame.grid_rowconfigure(1, weight=2)  # Очередь (больше места)
        right_frame.grid_columnconfigure(0, weight=1)
        
        # Превью стикера (верх)
        self._sticker_preview = StickerPreview(
            right_frame,
            printer_service=self._services.get("printer_service"),
            settings_service=self._services.get("settings_service")
        )
        self._sticker_preview.grid(row=0, column=0, sticky="nsew", padx=5, pady=(5, 2))
        
        # Очередь печати (низ)
        self._print_queue = PrintQueue(
            right_frame,
            product_repo=self._services.get("product_repo"),
            printer_service=self._services.get("printer_service"),
            settings_service=self._services.get("settings_service")
        )
        self._print_queue.grid(row=1, column=0, sticky="nsew", padx=5, pady=(2, 5))
        
        logger.debug("[SearchAddressTab] Правая панель создана")
    
    def _on_search_result(self, products: List[Product]) -> None:
        """Обработчик результатов поиска от SearchBar."""
        self.update_products(products)
    
    def _add_current_to_queue(self) -> None:
        """Добавить текущий товар в очередь печати (заглушка)."""
        logger.info("[SearchAddressTab] Кнопка 'В очередь' нажата (заглушка)")
        # TODO: Реализовать добавление в PrintQueue
    
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
