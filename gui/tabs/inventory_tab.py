"""
Вкладка "Инвентаризация" (заглушка).
"""

import logging
from typing import Any

import customtkinter as ctk

from services.di_container import DIContainer

logger = logging.getLogger(__name__)


class InventoryTab(ctk.CTkFrame):
    """Вкладка "Инвентаризация" (заглушка)."""
    
    def __init__(self, master: Any, di_container: DIContainer):
        super().__init__(master)
        self._container = di_container
        
        logger.info("[InventoryTab] Инициализация вкладки-заглушки")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self._create_content()
        
        logger.debug("[InventoryTab] Вкладка создана")
    
    def _create_content(self) -> None:
        """Создание контента вкладки."""
        content_frame = ctk.CTkFrame(self)
        content_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Заголовок
        title_label = ctk.CTkLabel(
            content_frame,
            text="🚧 Модуль в разработке",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(40, 20))
        
        # Описание
        desc_label = ctk.CTkLabel(
            content_frame,
            text="Функционал инвентаризации будет доступен в следующей версии.\n\n"
                 "Планируемый функционал:\n"
                 "• Импорт файлов Excel (.xlsx, .xls)\n"
                 "• Подключение сканеров штрих-кодов\n"
                 "• Расчёт расхождений (план vs факт)\n"
                 "• Экспорт отчётов",
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        desc_label.pack(pady=20)
        
        # Кнопки-заглушки
        buttons_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        buttons_frame.pack(pady=30)
        
        btn_import = ctk.CTkButton(
            buttons_frame,
            text="📥 Импорт Excel",
            width=150,
            command=self._on_import_click
        )
        btn_import.grid(row=0, column=0, padx=10, pady=10)
        
        btn_scanner = ctk.CTkButton(
            buttons_frame,
            text="📡 Сканер",
            width=150,
            command=self._on_scanner_click
        )
        btn_scanner.grid(row=0, column=1, padx=10, pady=10)
        
        btn_export = ctk.CTkButton(
            buttons_frame,
            text="📤 Экспорт отчёта",
            width=150,
            command=self._on_export_click
        )
        btn_export.grid(row=0, column=2, padx=10, pady=10)
        
        logger.debug("[InventoryTab] Контент вкладки создан")
    
    def _on_import_click(self) -> None:
        """Обработчик клика по кнопке импорта."""
        logger.info("[InventoryTab] Клик по кнопке 'Импорт Excel' (заглушка)")
        # TODO: Реализовать импорт через IInventoryService
    
    def _on_scanner_click(self) -> None:
        """Обработчик клика по кнопке сканера."""
        logger.info("[InventoryTab] Клик по кнопке 'Сканер' (заглушка)")
        # TODO: Реализовать подключение сканера
    
    def _on_export_click(self) -> None:
        """Обработчик клика по кнопке экспорта."""
        logger.info("[InventoryTab] Клик по кнопке 'Экспорт отчёта' (заглушка)")
        # TODO: Реализовать экспорт через IInventoryService
