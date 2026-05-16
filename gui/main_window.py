"""
Главное окно приложения.
Содержит: кнопки управления слева, ttk.Notebook с вкладками справа.
"""

import logging
from typing import Any, Dict
import os

import customtkinter as ctk
from tkinter import ttk
from PIL import Image

from gui.tabs.search_address_tab import SearchAddressTab
from gui.tabs.inventory_tab import InventoryTab
from gui.dialogs.settings_dialog import SettingsDialog

logger = logging.getLogger(__name__)


class MainWindow(ctk.CTkFrame):
    """
    Главное окно приложения.

    Структура:
    ┌─────────────────────────────────────────┐
    │  [Help] [Settings]      [Табы справа]   │
    ├─────────────────────────────────────────┤
    │  Вкладка (Поиск | Инвентаризация)       │
    └─────────────────────────────────────────┘
    """

    def __init__(self, master: Any, services: Dict[str, Any]):
        super().__init__(master)
        self._services = services

        # Получаем сервисы из словаря
        self._search_service = services.get("search_service")
        self._settings_service = services.get("settings_service")

        logger.info("[MainWindow] Инициализация главного окна")

        # Настраиваем сетку
        self.grid_rowconfigure(0, weight=1)  # Вкладки растягиваются
        self.grid_columnconfigure(0, weight=1)

        # Создаём верхнюю панель с кнопками и табами
        self._create_top_panel()

        logger.info("[MainWindow] Главное окно инициализировано")

    def _create_top_panel(self) -> None:
        """Создание верхней панели: кнопки слева, табы справа."""
        top_frame = ctk.CTkFrame(self)
        top_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        top_frame.grid_columnconfigure(1, weight=1)  # Табы занимают свободное место

        # --- ЛЕВАЯ ЧАСТЬ: Кнопки ---
        left_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="w", padx=5)

        # Путь к иконкам
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "icons")

        # Кнопка "Справка"
        try:
            help_img = ctk.CTkImage(
                light_image=Image.open(os.path.join(icons_dir, "help32.png")),
                dark_image=Image.open(os.path.join(icons_dir, "help32.png")),
                size=(28, 28)
            )
            self._help_btn = ctk.CTkButton(
                left_frame,
                text="",
                image=help_img,
                width=40,
                height=40,
                command=self._open_help
            )
            self._help_btn.pack(side="left", padx=2)
        except Exception as e:
            logger.warning(f"[MainWindow] Не удалось загрузить иконку help32.png: {e}")
            # Фолбэк на текст
            ctk.CTkButton(left_frame, text="Help", width=40, command=self._open_help).pack(side="left", padx=2)

        # Кнопка "Настройки"
        try:
            settings_img = ctk.CTkImage(
                light_image=Image.open(os.path.join(icons_dir, "settings32.png")),
                dark_image=Image.open(os.path.join(icons_dir, "settings32.png")),
                size=(28, 28)
            )
            self._settings_btn = ctk.CTkButton(
                left_frame,
                text="",
                image=settings_img,
                width=40,
                height=40,
                command=self._open_settings
            )
            self._settings_btn.pack(side="left", padx=2)
        except Exception as e:
            logger.warning(f"[MainWindow] Не удалось загрузить иконку settings32.png: {e}")
            ctk.CTkButton(left_frame, text="Sett", width=40, command=self._open_settings).pack(side="left", padx=2)

        # --- ПРАВАЯ ЧАСТЬ: Табы ---
        # Настраиваем стиль для крупных ярлыков табов
        style = ttk.Style()
        style.configure('Custom.Tab', font=('Arial', 14, 'bold'), padding=(20, 10))
        style.map('Custom.Tab', foreground=[('active', '#1E90FF')])

        # Контейнер для notebook
        notebook_container = ctk.CTkFrame(top_frame, fg_color="transparent")
        notebook_container.grid(row=0, column=1, sticky="e", padx=5)

        # Создаём ttk.Notebook с кастомным стилем и увеличенной высотой
        self._notebook = ttk.Notebook(notebook_container, style='Custom.Tab')
        self._notebook.pack(side="right")
        
        # Устанавливаем высоту табов (требует обновления после pack)
        self._notebook.configure(height=50)

        # Вкладка "Поиск | Адрес"
        self._search_tab = SearchAddressTab(
            self._notebook,
            services=self._services
        )
        self._notebook.add(self._search_tab, text="  🔍  Поиск | Адрес  ")

        # Вкладка "Инвентаризация"
        self._inventory_tab = InventoryTab(
            self._notebook,
            services=self._services
        )
        self._notebook.add(self._inventory_tab, text="  📋  Инвентаризация  ")

        logger.debug("[MainWindow] Верхняя панель с кнопками и табами создана")

    def _on_search_result(self, products: list) -> None:
        """Обработчик результатов поиска."""
        logger.info(f"[MainWindow] Получены результаты поиска: {len(products)} товаров")

        # Всегда передаём результаты в вкладку поиска (независимо от активной вкладки)
        self._search_tab.update_products(products)

    def _open_settings(self) -> None:
        """Открытие диалога настроек."""
        logger.info("[MainWindow] Открытие настроек")
        dialog = SettingsDialog(self, self._settings_service)
        dialog.grab_set()  # Модальное окно

    def _open_help(self) -> None:
        """Открытие справки (заглушка)."""
        logger.info("[MainWindow] Открыта справка (заглушка)")
