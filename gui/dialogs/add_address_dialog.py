"""
Диалог добавления адреса хранения.

Поддерживает два режима:
1. Форматированный ввод (сетка полей по уровням)
2. Свободный ввод (одно текстовое поле)
"""

import logging
from typing import Any, Callable, Optional, List

import customtkinter as ctk

from libs.utils import AddressFormatter, AddressFormatConfig

logger = logging.getLogger(__name__)


class AddAddressDialog(ctk.CTkToplevel):
    """
    Диалог добавления адреса хранения.
    
    Поддерживает форматированный ввод по уровням и свободный ввод.
    """
    
    def __init__(
        self,
        master: Any,
        address_formatter: AddressFormatter,
        on_save: Callable[[str], None],
        font_size: int = 14
    ):
        super().__init__(master)
        self._formatter = address_formatter
        self._on_save = on_save
        self._font_size = font_size
        self._is_free_entry_mode = False
        
        logger.debug("[AddAddressDialog] Открытие диалога добавления адреса")
        
        # Настройки окна
        self.title("➕ Добавить адрес")
        self.geometry("500x400+100+100")
        self.minsize(400, 300)
        
        self.transient(master)
        self.grab_set()
        
        # Создаём контент
        self._create_content()
    
    def _create_content(self) -> None:
        """Создание контента диалога."""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Заголовок
        title_label = ctk.CTkLabel(
            self,
            text="Введите адрес хранения",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Контейнер для полей ввода
        self._input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self._input_frame.grid_columnconfigure(0, weight=1)
        
        # Кнопка переключения режима
        self._mode_button = ctk.CTkButton(
            self._input_frame,
            text="✏️ Ввод не в формате",
            width=200,
            command=self._toggle_free_entry_mode
        )
        self._mode_button.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Контейнер для форматированных полей
        self._formatted_container = ctk.CTkFrame(self._input_frame, fg_color="transparent")
        self._formatted_container.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        # Поле свободного ввода (изначально скрыто)
        self._free_entry = ctk.CTkEntry(
            self._input_frame,
            height=self._font_size + 16,
            font=ctk.CTkFont(size=self._font_size, family="Arial"),
            fg_color="#FFFFFF",
            text_color="#000000",
            border_color="#AAAAAA",
            corner_radius=6,
            placeholder_text="Введите адрес в свободной форме"
        )
        # Не размещаем сразу, показываем только при переключении
        
        # Отображаем поля в зависимости от текущего режима
        if self._formatter.config.enabled:
            self._render_formatted_fields()
        else:
            # Если форматирование отключено - сразу показываем свободный ввод
            self._is_free_entry_mode = True
            self._show_free_entry()
        
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
    
    def _render_formatted_fields(self) -> None:
        """Отрисовка сетки полей для форматированного ввода."""
        # Очищаем контейнер
        for widget in self._formatted_container.winfo_children():
            widget.destroy()
        
        self._formatted_entries: List[ctk.CTkEntry] = []
        levels = self._formatter.get_level_names()
        
        # Размещаем поля в grid (по 3 в ряд)
        row, col = 0, 0
        for i, level_name in enumerate(levels):
            # Фрейм для пары label+entry
            field_frame = ctk.CTkFrame(self._formatted_container, fg_color="transparent")
            
            # Label с названием уровня
            lbl = ctk.CTkLabel(
                field_frame,
                text=f"{level_name}:",
                width=80,
                anchor="e",
                font=ctk.CTkFont(size=self._font_size)
            )
            lbl.pack(side="left", padx=(0, 5))
            
            # Entry для значения
            entry = ctk.CTkEntry(
                field_frame,
                height=self._font_size + 16,
                font=ctk.CTkFont(size=self._font_size, family="Arial"),
                fg_color="#FFFFFF",
                text_color="#000000",
                border_color="#AAAAAA",
                corner_radius=6,
                width=100,
                placeholder_text=level_name
            )
            entry.pack(side="left", fill="x", expand=True)
            
            field_frame.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            self._formatted_entries.append(entry)
            
            col += 1
            if col >= 3:
                col = 0
                row += 1
        
        # Настройка grid контейнера
        for c in range(min(3, len(levels))):
            self._formatted_container.grid_columnconfigure(c, weight=1)
    
    def _show_free_entry(self) -> None:
        """Показать поле свободного ввода."""
        self._formatted_container.grid_remove()
        self._mode_button.configure(text="📋 Вернуть форматированный ввод")
        self._free_entry.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        self._free_entry.focus_set()
    
    def _hide_free_entry(self) -> None:
        """Скрыть поле свободного ввода."""
        self._free_entry.grid_remove()
        self._mode_button.configure(text="✏️ Ввод не в формате")
        self._formatted_container.grid()
    
    def _toggle_free_entry_mode(self) -> None:
        """Переключение между режимом свободного и форматированного ввода."""
        if self._is_free_entry_mode:
            self._is_free_entry_mode = False
            self._hide_free_entry()
        else:
            self._is_free_entry_mode = True
            self._show_free_entry()
    
    def _on_click_save(self) -> None:
        """Обработчик клика по кнопке 'Сохранить'."""
        address = self._get_address_value()
        
        if not address or not address.strip():
            logger.warning("[AddAddressDialog] Пустой адрес, сохранение отменено")
            return
        
        address = address.strip()
        
        # Если в форматированном режиме - валидируем
        if not self._is_free_entry_mode and self._formatter.config.enabled:
            values = [e.get().strip() for e in self._formatted_entries]
            is_valid, message = self._formatter.validate(values)
            
            if not is_valid:
                logger.warning(f"[AddAddressDialog] Валидация не пройдена: {message}")
                # Можно показать диалог предупреждения
                self._show_validation_warning(message)
                return
        
        logger.info(f"[AddAddressDialog] Сохранение адреса: {address}")
        
        if self._on_save:
            self._on_save(address)
        
        self.destroy()
    
    def _get_address_value(self) -> str:
        """Получение значения адреса из полей."""
        if self._is_free_entry_mode:
            return self._free_entry.get()
        else:
            # Собираем значения из форматированных полей
            values = [e.get().strip() for e in self._formatted_entries]
            # Фильтруем пустые значения с конца
            while values and not values[-1]:
                values.pop()
            return self._formatter.format(values)
    
    def _show_validation_warning(self, message: str) -> None:
        """Показ предупреждения о валидации."""
        warning_dialog = ctk.CTkToplevel(self)
        warning_dialog.title("⚠️ Предупреждение")
        warning_dialog.geometry("400x150+150+150")
        warning_dialog.transient(self)
        warning_dialog.grab_set()
        
        lbl = ctk.CTkLabel(
            warning_dialog,
            text=message,
            font=ctk.CTkFont(size=14),
            wraplength=350
        )
        lbl.pack(padx=20, pady=20, expand=True)
        
        btn_frame = ctk.CTkFrame(warning_dialog, fg_color="transparent")
        btn_frame.pack(pady=(0, 20))
        
        btn_continue = ctk.CTkButton(
            btn_frame,
            text="Всё равно сохранить",
            command=lambda: self._force_save_and_close(warning_dialog)
        )
        btn_continue.pack(side="right", padx=5)
        
        btn_fix = ctk.CTkButton(
            btn_frame,
            text="Исправить",
            command=warning_dialog.destroy
        )
        btn_fix.pack(side="right", padx=5)
    
    def _force_save_and_close(self, warning_dialog: ctk.CTkToplevel) -> None:
        """Принудительное сохранение несмотря на валидацию."""
        warning_dialog.destroy()
        address = self._get_address_value()
        if address and self._on_save:
            self._on_save(address)
        self.destroy()
