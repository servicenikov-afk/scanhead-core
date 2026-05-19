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
        font_size: int = 18,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        self.on_select = on_select
        self.width = width
        self.max_height = max_height
        self._font_size = font_size
        
        # Флаг состояния (важно!)
        self._is_visible = False
        self._pending_action_id: Optional[int] = None  # Для отмены отложенных вызовов
        
        # Настройка окна
        self.overrideredirect(True)  # Без рамок и заголовка
        self.attributes('-topmost', True)  # Поверх всех окон
        self.withdraw()  # Скрыто по умолчанию
        
        # Основной фрейм с крупным шрифтом
        self.frame = ctk.CTkScrollableFrame(
            self,
            width=0,  # 0 = авто-ширина от geometry()
            height=self.max_height,
            corner_radius=6,
            border_width=1,
            scrollbar_button_color="#555555",
            scrollbar_button_hover_color="#777777"
        )
        self.frame.pack(fill="both", expand=True)
        
        # Список кнопок
        self.buttons: List[ctk.CTkButton] = []
        
        # Привязка событий для закрытия
        self.bind("<FocusOut>", lambda e: self.hide())
        self.frame.bind("<FocusOut>", lambda e: self.hide())

    def show_suggestions(self, suggestions: List[str], x: int, y: int) -> None:
        """Показать список подсказок — детерминированно, без переключений."""
        
        # 1. Отменить любое отложенное скрытие/показ
        if self._pending_action_id:
            self.after_cancel(self._pending_action_id)
            self._pending_action_id = None
        
        # 2. Обновить контент (кнопки)
        self._rebuild_buttons(suggestions)
        
        # 3. Обновить позицию (на случай изменения ширины entry)
        self._update_position(x, y)
        
        # 4. Показать окно, если ещё не показано
        if not self._is_visible:
            if self.winfo_exists():
                self.deiconify()  # Показать существующее
            else:
                # Если окно уничтожено - воссоздать не получится в Toplevel,
                # но это крайний случай, просто возвращаемся
                return
            self._is_visible = True
        
        # 5. Поднять на передний план
        if self.winfo_exists():
            self.lift()

    def _rebuild_buttons(self, items: List[str]) -> None:
        """Пересоздать кнопки с новым контентом."""
        self._clear_buttons()
        
        # Высота кнопки = шрифт + 14px для рационального использования пространства
        button_height = self._font_size + 14
        
        for text in items:
            btn = ctk.CTkButton(
                self.frame,
                text=text,
                anchor="w",
                height=button_height,
                command=lambda t=text: self._select(t),
                hover_color=("gray80", "gray20"),
                font=ctk.CTkFont(size=self._font_size, family="Arial")
            )
            btn.pack(fill="x", padx=2, pady=1)
            self.buttons.append(btn)

    def _clear_buttons(self) -> None:
        """Безопасно удалить все кнопки."""
        for btn in self.buttons:
            if btn.winfo_exists():
                btn.pack_forget()  # Скрыть, не уничтожать (быстрее)
        self.buttons.clear()

    def _update_position(self, x: int, y: int) -> None:
        """Пересчитать позицию и размеры относительно entry — КАЖДЫЙ раз."""
        if not self.winfo_exists():
            return
        
        # Ширина списка = ширина entry + 30px
        # Вычисляется динамически из координат
        list_width = self.width  # Передаётся из SearchBar как entry_width + 30
        
        # Высота: не больше 6 пунктов * высота кнопки
        button_height = self._font_size + 14
        max_items = 6
        list_height = min(len(self.buttons), max_items) * (button_height + 2) + 4  # +2 pady, +4 padding
        list_height = min(list_height, self.max_height)
        
        # Применить геометрию
        self.geometry(f"{list_width}x{list_height}+{x}+{y}")
    
    def hide(self) -> None:
        """Скрыть список подсказок — немедленно, без отложенных действий."""
        
        # Отменить любое отложенное показывание
        if self._pending_action_id:
            self.after_cancel(self._pending_action_id)
            self._pending_action_id = None
        
        # Скрыть окно
        if self._is_visible and self.winfo_exists():
            self.withdraw()
            self._is_visible = False
        
        # Очистить кнопки (но не уничтожать toplevel — переиспользуем)
        self._clear_buttons()

    def _select(self, value: str) -> None:
        """Обработка выбора элемента."""
        logger.debug(f"[SuggestionList] Выбрано: {value}")
        # Сначала вызвать колбэк
        if self.on_select:
            self.on_select(value)
        # Потом — гарантированно скрыть список
        self.hide()
    
    def update_font_size(self, font_size: int) -> None:
        """Обновить размер шрифта для всех кнопок подсказок."""
        self._font_size = font_size
        new_font = ctk.CTkFont(size=self._font_size, family="Arial")
        
        # Обновляем шрифт и высоту у всех существующих кнопок
        button_height = self._font_size + 14
        for btn in self.buttons:
            try:
                if btn.winfo_exists():
                    btn.configure(font=new_font, height=button_height)
            except Exception:
                pass
        
        # Пересчитать высоту контента если есть кнопки
        if self.buttons:
            content_height = min(len(self.buttons) * (button_height + 2) + 4, self.max_height)
            self.frame.configure(height=content_height)
    
    def destroy(self) -> None:
        """Безопасное уничтожение виджета с очисткой событий."""
        # Отменяем все отложенные события
        if self._pending_action_id is not None:
            try:
                self.after_cancel(self._pending_action_id)
            except Exception:
                pass
            self._pending_action_id = None
        
        # Очищаем кнопки
        self._clear_buttons()
        
        try:
            if self.winfo_exists():
                super().destroy()
        except Exception:
            pass
