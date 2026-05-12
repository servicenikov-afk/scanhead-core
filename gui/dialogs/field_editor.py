"""
Диалог редактирования одного поля товара.
Открывается как Toplevel окно.
"""

import logging
from typing import Any, Callable, Optional

import customtkinter as ctk

from services.interfaces import IProductRepository

logger = logging.getLogger(__name__)


class FieldEditor(ctk.CTkToplevel):
    """
    Диалог редактирования поля товара.
    
    Позволяет изменить одно поле (артикул, название, адрес).
    """
    
    def __init__(
        self,
        master: Any,
        field_name: str,
        current_value: str,
        product_id: int,
        product_repo: IProductRepository,
        on_save: Callable[[str, str], None]
    ):
        super().__init__(master)
        
        self._field_name = field_name
        self._product_id = product_id
        self._product_repo = product_repo
        self._on_save = on_save
        
        logger.debug(f"[FieldEditor] Открытие редактора для {field_name}")
        
        # Настройки окна
        self.title(f"Редактирование: {self._get_field_label()}")
        self.geometry("400x200")
        self.resizable(False, False)
        
        # Делаем модальным
        self.transient(master)
        
        # Создаём контент
        self._create_content(current_value)
    
    def _get_field_label(self) -> str:
        """Получение человеко-читаемого названия поля."""
        labels = {
            "article": "Артикул",
            "article2": "Артикул 2",
            "name": "Наименование",
            "address": "Адрес хранения"
        }
        return labels.get(self._field_name, self._field_name)
    
    def _create_content(self, current_value: str) -> None:
        """Создание контента диалога."""
        # Отступы
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Метка
        lbl = ctk.CTkLabel(
            self,
            text=f"{self._get_field_label()}:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        lbl.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Поле ввода
        self._entry = ctk.CTkEntry(
            self,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self._entry.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self._entry.insert(0, current_value)
        self._entry.focus_set()
        
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
        
        # Привязка Enter для сохранения
        self._entry.bind("<Return>", lambda e: self._on_click_save())
        self._entry.bind("<Escape>", lambda e: self.destroy())
    
    def _on_click_save(self) -> None:
        """Обработчик клика по кнопке 'Сохранить'."""
        new_value = self._entry.get().strip()
        
        if not new_value:
            logger.warning("[FieldEditor] Пустое значение, сохранение отменено")
            return
        
        logger.info(f"[FieldEditor] Сохранение {self._field_name} = {new_value}")
        
        # Вызываем callback для обновления через репозиторий
        self._on_save(self._field_name, new_value)
        
        # Закрываем диалог
        self.destroy()
