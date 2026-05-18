"""
Выпадающий список подсказок (Autocomplete Suggestion List).
Реализован как Toplevel окно, позиционируемое под полем ввода.
"""
import customtkinter as ctk
from typing import List, Callable, Optional, Any
import logging

logger = logging.getLogger(__name__)


class SuggestionList(ctk.CTkToplevel):
    """Всплывающий список подсказок для поиска."""

    def __init__(
        self,
        master: Any,
        on_select: Callable[[str], None],
        width: int = 400,
        max_height: int = 200,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        self.on_select = on_select
        self.width = width
        self.max_height = max_height
        
        # Настройка окна
        self.overrideredirect(True)  # Без рамок и заголовка
        self.attributes('-topmost', True)  # Поверх всех окон
        self.withdraw()  # Скрыто по умолчанию
        
        # Основной фрейм
        self.frame = ctk.CTkScrollableFrame(
            self,
            width=self.width,
            height=self.max_height,
            corner_radius=6,
            border_width=1
        )
        self.frame.pack(fill="both", expand=True)
        
        # Список кнопок
        self.buttons: List[ctk.CTkButton] = []
        
        # Привязка событий для закрытия
        self.bind("<FocusOut>", lambda e: self.hide())
        self.frame.bind("<FocusOut>", lambda e: self.hide())

    def show_suggestions(self, suggestions: List[str], x: int, y: int) -> None:
        """Отобразить список подсказок в указанных координатах."""
        # Очистка старых кнопок
        for btn in self.buttons:
            btn.destroy()
        self.buttons.clear()
        
        if not suggestions:
            self.withdraw()
            return
        
        # Создание кнопок
        for text in suggestions:
            btn = ctk.CTkButton(
                self.frame,
                text=text,
                anchor="w",
                height=30,
                command=lambda t=text: self._select(t),
                hover_color=("gray80", "gray20")
            )
            btn.pack(fill="x", padx=2, pady=2)
            self.buttons.append(btn)
        
        # Авто-высота (но не больше max_height)
        content_height = min(len(suggestions) * 34 + 4, self.max_height)
        self.frame.configure(height=content_height)
        
        # Позиционирование
        self.geometry(f"+{x}+{y}")
        self.deiconify()  # Показать
        self.lift()  # Поднять наверх

    def hide(self) -> None:
        """Скрыть список."""
        try:
            if self.winfo_exists():
                self.withdraw()
        except Exception:
            pass  # Виджет уже уничтожен

    def _select(self, value: str) -> None:
        """Обработка выбора элемента."""
        logger.debug(f"[SuggestionList] Выбрано: {value}")
        self.hide()
        if self.on_select:
            self.on_select(value)
    
    def destroy(self) -> None:
        """Безопасное уничтожение виджета."""
        try:
            if self.winfo_exists():
                super().destroy()
        except Exception:
            pass
