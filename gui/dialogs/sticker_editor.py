"""
Редактор пресетов стикеров.
Диалог настройки оформления этикеток.
"""

import logging
from typing import Any, Dict

import customtkinter as ctk

from services.interfaces import ISettingsService

logger = logging.getLogger(__name__)


class StickerEditor(ctk.CTkToplevel):
    """
    Диалог редактора пресетов стикеров.
    
    Позволяет настроить: размеры, шрифты, расположение элементов.
    """
    
    def __init__(self, master: Any, settings_service: ISettingsService):
        super().__init__(master)
        self._settings_service = settings_service
        
        logger.debug("[StickerEditor] Открытие редактора пресетов")
        
        # Настройки окна
        self.title("⚙ Редактор пресетов стикеров")
        self.geometry("500x400")
        self.resizable(True, True)
        
        self.transient(master)
        
        # Текущий пресет
        self._current_preset = self._settings_service.get_setting('current_preset', {})
        
        # Создаём контент
        self._create_content()
    
    def _create_content(self) -> None:
        """Создание контента диалога."""
        # Отступы
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Заголовок
        title_label = ctk.CTkLabel(
            self,
            text="Настройка оформления стикера",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Контейнер настроек
        settings_frame = ctk.CTkScrollableFrame(self)
        settings_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        # Размер стикера (ширина)
        self._create_setting_field(
            settings_frame,
            row=0,
            label="Ширина (мм):",
            key="width_mm",
            default=60
        )
        
        # Размер стикера (высота)
        self._create_setting_field(
            settings_frame,
            row=1,
            label="Высота (мм):",
            key="height_mm",
            default=40
        )
        
        # Тип штрих-кода
        self._create_combo_setting(
            settings_frame,
            row=2,
            label="Тип штрих-кода:",
            key="barcode_type",
            options=["CODE128", "EAN13", "QR"],
            default="CODE128"
        )
        
        # Размер шрифта
        self._create_setting_field(
            settings_frame,
            row=3,
            label="Размер шрифта:",
            key="font_size",
            default=12
        )
        
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
        
        btn_reset = ctk.CTkButton(
            buttons_frame,
            text="Сброс",
            width=100,
            fg_color="#808080",
            command=self._on_click_reset
        )
        btn_reset.pack(side="right", padx=5)
    
    def _create_setting_field(
        self,
        parent: Any,
        row: int,
        label: str,
        key: str,
        default: Any
    ) -> None:
        """Создание поля числовой настройки."""
        lbl = ctk.CTkLabel(
            parent,
            text=label,
            width=150,
            anchor="w"
        )
        lbl.grid(row=row, column=0, padx=5, pady=10, sticky="w")
        
        entry = ctk.CTkEntry(
            parent,
            width=100,
            height=30
        )
        entry.grid(row=row, column=1, padx=5, pady=10, sticky="w")
        entry.insert(0, str(self._current_preset.get(key, default)))
        
        setattr(self, f"_{key}_entry", entry)
    
    def _create_combo_setting(
        self,
        parent: Any,
        row: int,
        label: str,
        key: str,
        options: list,
        default: Any
    ) -> None:
        """Создание выпадающего списка настройки."""
        lbl = ctk.CTkLabel(
            parent,
            text=label,
            width=150,
            anchor="w"
        )
        lbl.grid(row=row, column=0, padx=5, pady=10, sticky="w")
        
        combo = ctk.CTkComboBox(
            parent,
            values=options,
            width=150,
            height=30
        )
        combo.grid(row=row, column=1, padx=5, pady=10, sticky="w")
        combo.set(self._current_preset.get(key, default))
        
        setattr(self, f"_{key}_combo", combo)
    
    def _on_click_save(self) -> None:
        """Обработчик клика по кнопке 'Сохранить'."""
        logger.info("[StickerEditor] Сохранение пресета")
        
        # Собираем значения из полей
        new_preset = {
            'width_mm': int(getattr(self, '_width_mm_entry').get()),
            'height_mm': int(getattr(self, '_height_mm_entry').get()),
            'barcode_type': getattr(self, '_barcode_type_combo').get(),
            'font_size': int(getattr(self, '_font_size_entry').get()),
        }
        
        # Сохраняем в сервис настроек
        self._settings_service.set_setting('current_preset', new_preset)
        
        logger.info(f"[StickerEditor] Пресет сохранён: {new_preset}")
        self.destroy()
    
    def _on_click_reset(self) -> None:
        """Обработчик клика по кнопке 'Сброс'."""
        logger.info("[StickerEditor] Сброс пресета к значениям по умолчанию")
        
        default_preset = {
            'width_mm': 60,
            'height_mm': 40,
            'barcode_type': 'CODE128',
            'font_size': 12
        }
        
        # Заполняем поля дефолтными значениями
        getattr(self, '_width_mm_entry').delete(0, "end")
        getattr(self, '_width_mm_entry').insert(0, str(default_preset['width_mm']))
        
        getattr(self, '_height_mm_entry').delete(0, "end")
        getattr(self, '_height_mm_entry').insert(0, str(default_preset['height_mm']))
        
        getattr(self, '_barcode_type_combo').set(default_preset['barcode_type'])
        
        getattr(self, '_font_size_entry').delete(0, "end")
        getattr(self, '_font_size_entry').insert(0, str(default_preset['font_size']))
