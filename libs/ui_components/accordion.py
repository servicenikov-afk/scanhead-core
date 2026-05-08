"""Accordion Frame - Раскладной UI компонент

Компонент для создания раскладных секций в интерфейсе.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict


class AccordionFrame(ttk.Frame):
    """Раскладной фрейм для группировки контента
    
    Позволяет создавать секции, которые можно сворачивать и разворачивать.
    """
    
    def __init__(self, parent, *args, **kwargs):
        """Инициализация аккордеона
        
        Args:
            parent: Родительский виджет
        """
        super().__init__(parent, *args, **kwargs)
        self.sections: Dict[str, dict] = {}
    
    def add_section(self, title: str, content_frame: ttk.Frame, 
                    initially_expanded: bool = True) -> None:
        """Добавляет секцию в аккордеон
        
        Args:
            title: Заголовок секции
            content_frame: Фрейм с содержимым секции
            initially_expanded: Развернута ли секция по умолчанию
        """
        # Создаем заголовок
        header = ttk.Frame(self)
        header.pack(fill=tk.X, pady=(5, 0))
        
        # Стрелка
        arrow = tk.Label(
            header, 
            text="▼" if initially_expanded else "▶", 
            font=("Arial", 8)
        )
        arrow.pack(side=tk.LEFT, padx=(5, 10))
        
        # Текст заголовка
        tk.Label(
            header, 
            text=title, 
            font=("Arial", 8, "bold")
        ).pack(side=tk.LEFT)
        
        # Разделитель
        ttk.Separator(header, orient='horizontal').pack(
            side=tk.BOTTOM, fill=tk.X, pady=(5, 0)
        )
        
        # Функция переключения
        def toggle():
            if content_frame.winfo_viewable():
                content_frame.pack_forget()
                arrow.config(text="▶")
            else:
                content_frame.pack(fill=tk.X, pady=(5, 0))
                arrow.config(text="▼")
        
        # Привязка события клика
        for widget in (arrow, header):
            widget.bind("<Button-1>", lambda e: toggle())
        
        # Отображение начального состояния
        if initially_expanded:
            content_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Сохраняем ссылку на секцию
        self.sections[title] = {'content': content_frame, 'arrow': arrow}
