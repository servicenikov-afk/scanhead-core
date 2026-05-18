"""
Главное окно приложения.
Содержит: кнопки управления слева, CTkTabview с вкладками справа.
Использует pack() для геометрии.
"""

import logging
from typing import Any, Dict
import os

import customtkinter as ctk
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
    │  Контент вкладки (растягивается)        │
    └─────────────────────────────────────────┘
    """

    def __init__(self, master: Any, services: Dict[str, Any]):
        super().__init__(master)
        self._services = services

        # Получаем сервисы из словаря
        self._search_service = services.get("search_service")
        self._settings_service = services.get("settings_service")

        logger.info("[MainWindow] Инициализация главного окна")

        # Загружаем иконки заранее (уменьшенный размер)
        self._img_help = self._load_icon("help32.png", size=(20, 20))
        self._img_settings = self._load_icon("settings32.png", size=(20, 20))

        # Создаём UI
        self._create_ui()

        logger.info("[MainWindow] Главное окно инициализировано")

    def _load_icon(self, filename: str, size: tuple = (20, 20)) -> ctk.CTkImage | None:
        """Загрузить иконку или вернуть None."""
        try:
            icons_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data", "icons"
            )
            img_path = os.path.join(icons_dir, filename)
            if os.path.exists(img_path):
                return ctk.CTkImage(
                    light_image=Image.open(img_path),
                    dark_image=Image.open(img_path),
                    size=size
                )
        except Exception as e:
            logger.warning(f"[MainWindow] Не удалось загрузить {filename}: {e}")
        return None

    def _create_ui(self) -> None:
        """Создание интерфейса с правильной геометрией."""
        # 1. Верхняя панель (фиксированная высота)
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(side="top", fill="x", padx=2, pady=2)

        # 2. Кнопки слева
        left_btns = ctk.CTkFrame(top_bar, fg_color="transparent")
        left_btns.pack(side="left")
        
        self._btn_help = ctk.CTkButton(
            left_btns,
            text="",
            image=self._img_help,
            width=28,
            height=28,
            command=self._open_help
        )
        self._btn_help.pack(side="left", padx=2)
        
        self._btn_settings = ctk.CTkButton(
            left_btns,
            text="",
            image=self._img_settings,
            width=28,
            height=28,
            command=self._open_settings
        )
        self._btn_settings.pack(side="left", padx=2)

        # 3. Табы справа (прижимаем pack(side="right"))
        self._notebook = ctk.CTkTabview(top_bar, height=36, corner_radius=8)
        self._notebook.pack(side="right")
        
        # Добавляем вкладки
        self._notebook.add("  🔍 Поиск | Адрес  ")
        self._notebook.add("  📋 Инвентаризация  ")

        # 4. Основной контент (растягивается на всё окно)
        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.pack(side="top", fill="both", expand=True, padx=2, pady=2)

        # 5. Инициализация вкладок ВНУТРИ контента
        self._search_tab = SearchAddressTab(self._content, self._services)
        self._search_tab.pack(fill="both", expand=True)
        
        self._inventory_tab = InventoryTab(self._content, self._services)
        # Скрываем инвентаризацию по умолчанию (пока не переключена)
        self._inventory_tab.pack_forget()

        # Привязка переключения табов
        self._notebook.configure(command=self._on_tab_change)

        logger.debug("[MainWindow] UI создан")

    def _on_tab_change(self) -> None:
        """Обработчик переключения вкладок."""
        selected = self._notebook.get()
        if "Поиск" in selected:
            self._search_tab.pack(fill="both", expand=True)
            self._inventory_tab.pack_forget()
        elif "Инвентаризация" in selected:
            self._inventory_tab.pack(fill="both", expand=True)
            self._search_tab.pack_forget()
        logger.debug(f"[MainWindow] Переключена вкладка: {selected}")

    def _on_search_result(self, products: list) -> None:
        """Обработчик результатов поиска."""
        logger.info(f"[MainWindow] Получены результаты поиска: {len(products)} товаров")

        # Всегда передаём результаты в вкладку поиска (независимо от активной вкладки)
        self._search_tab.update_products(products)

    def _open_settings(self) -> None:
        """Открытие диалога настроек."""
        logger.info("[MainWindow] Открытие настроек")
        
        # Создаём диалог с колбэком для обработки изменений настроек
        dialog = SettingsDialog(
            self,
            settings_service=self._settings_service,
            on_settings_changed=self._on_setting_changed
        )
        dialog.grab_set()  # Модальное окно
    
    def _on_setting_changed(self, key: str, value: Any) -> None:
        """Обработчик изменения настроек из диалога."""
        logger.info(f"[MainWindow] Изменена настройка {key}={value}")
        # Передаём изменение во вкладку поиска
        if hasattr(self, '_search_tab'):
            self._search_tab.on_setting_changed(key, value)

    def _open_help(self) -> None:
        """Открытие справки (заглушка)."""
        logger.info("[MainWindow] Открыта справка (заглушка)")
