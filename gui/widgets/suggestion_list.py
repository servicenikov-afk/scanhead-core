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
        
        # Хранилище ID отложенных событий для кнопок
        self._button_after_ids: dict = {}
        self._destroy_after_id: Optional[int] = None

    def show_suggestions(self, suggestions: List[str], x: int, y: int) -> None:
        """Отобразить список подсказок в указанных координатах."""
        # Очистка старых кнопок с отменой отложенных событий
        self._cleanup_buttons()
        
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
    
    def _cleanup_buttons(self) -> None:
        """Очистка кнопок с безопасным уничтожением."""
        # Отменяем все отслеживаемые отложенные события
        for btn_id in list(self._button_after_ids.keys()):
            try:
                self.after_cancel(btn_id)
            except Exception:
                pass
        self._button_after_ids.clear()
        
        # Отменяем предыдущее отложенное уничтожение
        if self._destroy_after_id is not None:
            try:
                self.after_cancel(self._destroy_after_id)
            except Exception:
                pass
            self._destroy_after_id = None
        
        # Немедленное уничтожение кнопок
        for btn in self.buttons:
            try:
                if btn.winfo_exists():
                    btn.destroy()
            except Exception:
                pass
        self.buttons.clear()

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
        """Безопасное уничтожение виджета с очисткой событий."""
        # Сначала отменяем все отложенные события
        self._cleanup_buttons()
        
        try:
            if self.winfo_exists():
                super().destroy()
        except Exception:
            pass
