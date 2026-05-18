"""
Поисковая строка с debounce (задержкой) и автодополнением через ttk.Combobox.
"""

import logging
from typing import Callable, Any, Optional, List
import threading
import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from services.interfaces import ISearchService
from libs.domain_models import Product

logger = logging.getLogger(__name__)


class SearchBar(ctk.CTkFrame):
    """
    Поле поиска с debounce 300мс и автодополнением через Combobox.
    
    При вводе текста запускается таймер. Если пользователь продолжает ввод,
    таймер сбрасывается. Поиск выполняется только после паузы в 300мс.
    Combobox показывает отфильтрованные подсказки при вводе.
    """
    
    def __init__(
        self, 
        master: Any, 
        search_service: ISearchService,
        on_search_result: Callable[[list], None],
        debounce_ms: int = 300
    ):
        super().__init__(master)
        self._search_service = search_service
        self._on_search_result = on_search_result
        self._debounce_ms = debounce_ms
        
        self._timer: Optional[threading.Timer] = None
        self._last_query = ""
        self._combobox: Optional[ttk.Combobox] = None
        self._products_cache: List[Product] = []
        
        logger.info("[SearchBar] Инициализация с ttk.Combobox")
        
        # Создаём поле ввода (Combobox)
        self._combobox = ttk.Combobox(
            self,
            font=("Arial", 21),
            height=15
        )
        self._combobox.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Привязываем обработчики
        self._combobox.bind("<KeyRelease>", self._on_key_release)
        self._combobox.bind("<<ComboboxSelected>>", self._on_combobox_selected)
        # Убрали FocusOut, который мешал выбору, теперь очищаем только при явном уходе фокуса с виджета
        self._combobox.bind("<FocusOut>", lambda e: self.after(200, self._clear_values))
        
        logger.info("[SearchBar] Combobox инициализирован")
    
    def _on_key_release(self, event) -> None:
        """Обработчик отпускания клавиши."""
        query = self._combobox.get().strip()
        
        # Если запрос не изменился - игнорируем
        if query == self._last_query:
            return
        
        self._last_query = query
        
        # Отменяем предыдущий таймер
        if self._timer is not None:
            self._timer.cancel()
        
        # Если поле пустое - сразу очищаем результаты
        if not query:
            self._clear_values()
            self._on_search_result([])
            return
        
        # Запускаем новый таймер
        self._timer = threading.Timer(
            self._debounce_ms / 1000.0,
            self._do_search,
            args=[query]
        )
        self._timer.start()
    
    def _do_search(self, query: str) -> None:
        """Выполнение поиска (вызывается после debounce)."""
        logger.info(f"[SearchBar] Выполнение поиска: '{query}'")
        
        # Запускаем поиск через сервис (асинхронно)
        self._search_service.search_async(query, self._on_search_complete)
    
    def _on_search_complete(self, products: list) -> None:
        """Обработчик завершения поиска (вызывается в главном потоке)."""
        logger.info(f"[SearchBar] Поиск завершён, найдено: {len(products)} товаров")
        
        # Кэшируем продукты
        self._products_cache = products
        
        # Если нет результатов - скрываем список и выходим
        if not products:
            self._clear_values()
            self._on_search_result([])
            return
        
        # Формируем список строк для отображения в Combobox
        suggestions = []
        for p in products:
            text = f"{p.article} | {p.name[:50]}..." if len(p.name) > 50 else f"{p.article} | {p.name}"
            suggestions.append(text)
        
        # Обновляем значения combobox
        self._combobox['values'] = suggestions
        
        # Принудительно открываем выпадающий список и возвращаем фокус в поле ввода
        def _open_and_focus():
            self._combobox.event_generate('<Button-1>')
            self._combobox.focus_set()
        
        self.after(0, _open_and_focus)
        
        # Вызываем callback для обновления UI (таблицы), но не очищаем поле
        self.after(0, lambda: self._on_search_result(products))
    
    def _on_combobox_selected(self, event) -> None:
        """Обработка выбора элемента из Combobox."""
        selected_text = self._combobox.get()
        logger.info(f"[SearchBar] Выбор из списка: {selected_text}")
        
        # Извлекаем артикул из текста (до " | ")
        article = selected_text.split(" | ")[0].strip()
        
        # Находим полный объект продукта в кэше
        selected_product = None
        for p in self._products_cache:
            if p.article == article:
                selected_product = p
                break
        
        # Очищаем поле поиска и список подсказок
        self._combobox.set("")
        self._last_query = ""
        self._clear_values()
        
        # Если продукт найден - передаём его в callback (одним элементом)
        if selected_product:
            self._on_search_result([selected_product])
        else:
            # Фолбэк: если не нашли в кэше, ищем заново по артикулу
            self._do_search(article)
    
    def _clear_values(self) -> None:
        """Очистка значений combobox."""
        self._combobox['values'] = []
        self._products_cache = []
    
    def get_query(self) -> str:
        """Получение текущего поискового запроса."""
        return self._combobox.get().strip()
    
    def clear(self) -> None:
        """Очистка поля поиска."""
        self._combobox.set("")
        self._last_query = ""
        self._clear_values()
        if self._timer:
            self._timer.cancel()
            self._timer = None
