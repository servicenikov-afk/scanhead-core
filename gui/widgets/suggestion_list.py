"""Выпадающий список подсказок для поиска."""
import customtkinter as ctk
from typing import List, Callable, Optional, Any
import logging

logger = logging.getLogger(__name__)


class SuggestionList(ctk.CTkToplevel):
    """Всплывающий список подсказок."""

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
        
        self._is_visible = False
        self._pending_action_id: Optional[int] = None
        
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.withdraw()
        
        self.frame = ctk.CTkScrollableFrame(
            self,
            width=0,
            height=self.max_height,
            corner_radius=6,
            border_width=1,
            scrollbar_button_color="#555555",
            scrollbar_button_hover_color="#777777"
        )
        self.frame.pack(fill="both", expand=True)
        
        self.buttons: List[ctk.CTkButton] = []
        
        self.bind("<FocusOut>", lambda e: self.hide())
        self.frame.bind("<FocusOut>", lambda e: self.hide())

    def show_suggestions(self, suggestions: List[str], x: int, y: int) -> None:
        if self._pending_action_id:
            self.after_cancel(self._pending_action_id)
            self._pending_action_id = None
        
        self._rebuild_buttons(suggestions)
        self._update_position(x, y)
        
        if not self._is_visible:
            if self.winfo_exists():
                self.deiconify()
            else:
                return
            self._is_visible = True
        
        if self.winfo_exists():
            self.lift()

    def _rebuild_buttons(self, items: List[str]) -> None:
        self._clear_buttons()
        
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
        for btn in self.buttons:
            if btn.winfo_exists():
                btn.pack_forget()
        self.buttons.clear()

    def _update_position(self, x: int, y: int) -> None:
        if not self.winfo_exists():
            return
        
        list_width = self.width
        button_height = self._font_size + 14
        max_items = 6
        list_height = min(len(self.buttons), max_items) * (button_height + 2) + 4
        list_height = min(list_height, self.max_height)
        
        self.geometry(f"{list_width}x{list_height}+{x}+{y}")
    
    def hide(self) -> None:
        if self._pending_action_id:
            self.after_cancel(self._pending_action_id)
            self._pending_action_id = None
        
        if self._is_visible and self.winfo_exists():
            self.withdraw()
            self._is_visible = False
        
        self._clear_buttons()

    def _select(self, value: str) -> None:
        logger.debug(f"[SuggestionList] Выбор: {value}")
        if self.on_select:
            self.on_select(value)
        self.hide()
    
    def update_font_size(self, font_size: int) -> None:
        self._font_size = font_size
        new_font = ctk.CTkFont(size=self._font_size, family="Arial")
        
        button_height = self._font_size + 14
        for btn in self.buttons:
            try:
                if btn.winfo_exists():
                    btn.configure(font=new_font, height=button_height)
            except Exception:
                pass
        
        if self.buttons:
            content_height = min(len(self.buttons) * (button_height + 2) + 4, self.max_height)
            self.frame.configure(height=content_height)
    
    def destroy(self) -> None:
        if self._pending_action_id is not None:
            try:
                self.after_cancel(self._pending_action_id)
            except Exception:
                pass
            self._pending_action_id = None
        
        self._clear_buttons()
        
        try:
            if self.winfo_exists():
                super().destroy()
        except Exception:
            pass
