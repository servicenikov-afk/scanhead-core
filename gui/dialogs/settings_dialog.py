"""
Диалог настроек приложения.
Позволяет настроить тему, язык, параметры таблицы и другие опции.
"""

import logging
from typing import Any

import customtkinter as ctk

from services.interfaces import ISettingsService

logger = logging.getLogger(__name__)


class SettingsDialog(ctk.CTkToplevel):
    """
    Диалог настроек приложения.
    
    Настройки: тема, язык, конфигурация колонок таблицы.
    """
    
    def __init__(self, master: Any, settings_service: ISettingsService):
        super().__init__(master)
        self._settings_service = settings_service
        
        logger.debug("[SettingsDialog] Открытие диалога настроек")
        
        # Настройки окна
        self.title("⚙ Настройки приложения")
        self.geometry("450x350")
        self.resizable(False, False)
        
        self.transient(master)
        
        # Создаём контент
        self._create_content()
    
    def _create_content(self) -> None:
        """Создание контента диалога."""
        # Отступы
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Заголовок
        title_label = ctk.CTkLabel(
            self,
            text="Настройки приложения",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Контейнер настроек
        settings_frame = ctk.CTkFrame(self)
        settings_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        settings_frame.grid_columnconfigure(1, weight=1)
        
        # Тема оформления
        row = 0
        lbl_theme = ctk.CTkLabel(
            settings_frame,
            text="Тема оформления:",
            width=150,
            anchor="w"
        )
        lbl_theme.grid(row=row, column=0, padx=10, pady=10, sticky="w")
        
        current_theme = self._settings_service.get_setting('theme', 'Dark')
        self._theme_combo = ctk.CTkComboBox(
            settings_frame,
            values=["System", "Light", "Dark"],
            width=200
        )
        self._theme_combo.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        self._theme_combo.set(current_theme)
        
        # Язык интерфейса
        row += 1
        lbl_lang = ctk.CTkLabel(
            settings_frame,
            text="Язык интерфейса:",
            width=150,
            anchor="w"
        )
        lbl_lang.grid(row=row, column=0, padx=10, pady=10, sticky="w")
        
        current_lang = self._settings_service.get_setting('language', 'ru')
        self._lang_combo = ctk.CTkComboBox(
            settings_frame,
            values=["ru", "en"],
            width=200
        )
        self._lang_combo.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        self._lang_combo.set(current_lang)
        
        # Кнопки
        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="e")
        
        btn_cancel = ctk.CTkButton(
            buttons_frame,
            text="Отмена",
            width=100,
            command=self.destroy
        )
        btn_cancel.pack(side="right", padx=5)
        
        btn_save = ctk.CTkButton(
            buttons_frame,
            text="Сохранить",
            width=100,
            command=self._on_click_save
        )
        btn_save.pack(side="right", padx=5)
    
    def _on_click_save(self) -> None:
        """Обработчик клика по кнопке 'Сохранить'."""
        logger.info("[SettingsDialog] Сохранение настроек")
        
        # Сохраняем тему
        theme = self._theme_combo.get()
        self._settings_service.set_setting('theme', theme)
        
        # Применяем тему немедленно
        import customtkinter as ctk
        ctk.set_appearance_mode(theme)
        
        # Сохраняем язык
        lang = self._lang_combo.get()
        self._settings_service.set_setting('language', lang)
        
        logger.info(f"[SettingsDialog] Настройки сохранены: theme={theme}, language={lang}")
        self.destroy()
