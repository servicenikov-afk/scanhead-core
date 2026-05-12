"""
Главное окно приложения.
Содержит: верхнюю панель, ttk.Notebook с вкладками, статус-бар.
"""

import logging
from typing import Any

import customtkinter as ctk
from tkinter import ttk

from services.di_container import DIContainer
from services.interfaces import ISearchService, ISettingsService

from gui.tabs.search_address_tab import SearchAddressTab
from gui.tabs.inventory_tab import InventoryTab
from gui.search_bar import SearchBar
from gui.dialogs.settings_dialog import SettingsDialog

logger = logging.getLogger(__name__)


class MainWindow(ctk.CTkFrame):
    """
    Главное окно приложения.
    
    Структура:
    ┌─────────────────────────────────────────┐
    │  [Поиск]              [⚙ Настройки]     │  <- Верхняя панель
    ├─────────────────────────────────────────┤
    │  ┌─────────┬───────────────────────┐    │
    │  │ Поиск   │  Инвентаризация       │    │  <- Notebook
    │  │ | Адрес │                       │    │
    │  └─────────┴───────────────────────┘    │
    ├─────────────────────────────────────────┤
    │  Статус-бар                             │
    └─────────────────────────────────────────┘
    """
    
    def __init__(self, master: Any, container: DIContainer):
        super().__init__(master)
        self._container = container
        
        # Получаем сервисы из контейнера
        self._search_service = container.get(ISearchService)
        self._settings_service = container.get(ISettingsService)
        
        logger.info("[MainWindow] Инициализация главного окна")
        
        # Настраиваем сетку
        self.grid_rowconfigure(1, weight=1)  # Вкладки растягиваются
        self.grid_columnconfigure(0, weight=1)
        
        # Создаём верхнюю панель
        self._create_top_panel()
        
        # Создаём notebook с вкладками
        self._create_notebook()
        
        # Создаём статус-бар
        self._create_status_bar()
        
        logger.info("[MainWindow] Главное окно инициализировано")
    
    def _create_top_panel(self) -> None:
        """Создание верхней панели с поиском и настройками."""
        top_frame = ctk.CTkFrame(self)
        top_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        top_frame.grid_columnconfigure(1, weight=1)
        
        # Логотип/название (слева)
        title_label = ctk.CTkLabel(
            top_frame, 
            text="📦 ScanHead Combine",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=(10, 20), pady=5)
        
        # Поисковая строка (центр)
        self._search_bar = SearchBar(
            top_frame, 
            search_service=self._search_service,
            on_search_result=self._on_search_result
        )
        self._search_bar.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # Кнопка настроек (справа)
        settings_btn = ctk.CTkButton(
            top_frame,
            text="⚙",
            width=40,
            command=self._open_settings
        )
        settings_btn.grid(row=0, column=2, padx=(5, 10), pady=5)
        
        logger.debug("[MainWindow] Верхняя панель создана")
    
    def _create_notebook(self) -> None:
        """Создание notebook с вкладками."""
        # Контейнер для notebook (CTkFrame)
        notebook_container = ctk.CTkFrame(self)
        notebook_container.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        notebook_container.grid_rowconfigure(0, weight=1)
        notebook_container.grid_columnconfigure(0, weight=1)
        
        # Создаём ttk.Notebook внутри CTkFrame
        self._notebook = ttk.Notebook(notebook_container)
        self._notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Вкладка "Поиск | Адрес"
        self._search_tab = SearchAddressTab(
            self._notebook,
            container=self._container
        )
        self._notebook.add(self._search_tab, text="🔍 Поиск | Адрес")
        
        # Вкладка "Инвентаризация"
        self._inventory_tab = InventoryTab(
            self._notebook,
            container=self._container
        )
        self._notebook.add(self._inventory_tab, text="📋 Инвентаризация")
        
        logger.debug("[MainWindow] Notebook с вкладками создан")
    
    def _create_status_bar(self) -> None:
        """Создание статус-бара."""
        self._status_bar = ctk.CTkLabel(
            self,
            text="Готов",
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        self._status_bar.grid(row=2, column=0, sticky="ew", padx=5, pady=2)
        
        logger.debug("[MainWindow] Статус-бар создан")
    
    def _on_search_result(self, products: list) -> None:
        """Обработчик результатов поиска."""
        if products:
            self._status_bar.configure(text=f"Найдено товаров: {len(products)}")
            # Передаём результаты в активную вкладку
            if self._notebook.index("current") == 0:
                self._search_tab.update_products(products)
        else:
            self._status_bar.configure(text="Ничего не найдено")
    
    def _open_settings(self) -> None:
        """Открытие диалога настроек."""
        logger.info("[MainWindow] Открытие настроек")
        dialog = SettingsDialog(self, self._settings_service)
        dialog.grab_set()  # Модальное окно
    
    def get_status_bar(self) -> ctk.CTkLabel:
        """Получение ссылки на статус-бар."""
        return self._status_bar
