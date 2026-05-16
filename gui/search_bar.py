"""
Поисковая строка с debounce (задержкой) и выпадающим списком подсказок.
"""

import logging
from typing import Callable, Any, Optional, List
import threading
import time

import customtkinter as ctk

from services.interfaces import ISearchService
from libs.domain_models import Product
from gui.widgets.suggestion_list import SuggestionList

logger = logging.getLogger(__name__)


class SearchBar(ctk.CTkFrame):
    """
    Поле поиска с debounce 300мс и автодополнением.
    
    При вводе текста запускается таймер. Если пользователь продолжает ввод,
    таймер сбрасывается. Поиск выполняется только после паузы в 300мс.
    После ввода 3+ символов показывается выпадающий список подсказок.
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
        self._suggestion_window: Optional[SuggestionList] = None
        
        logger.debug("[SearchBar] Инициализация")
        
        # Создаём поле ввода
        self._entry = ctk.CTkEntry(
            self,
            placeholder_text="🔍 Поиск по артикулу, названию или штрих-коду...",
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self._entry.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Привязываем обработчик нажатий
        self._entry.bind("<KeyRelease>", self._on_key_release)
        self._entry.bind("<Button-1>", self._on_entry_click)  # Обработка клика - не сбрасывать
        self._entry.bind("<FocusOut>", lambda e: self._hide_suggestions())
        
        logger.debug("[SearchBar] Поле поиска создано")
    
    def _on_key_release(self, event) -> None:
        """Обработчик отпускания клавиши."""
        query = self._entry.get().strip()
        
        # Если запрос не изменился - игнорируем
        if query == self._last_query:
            return
        
        self._last_query = query
        
        # Отменяем предыдущий таймер
        if self._timer is not None:
            self._timer.cancel()
        
        # Если поле пустое - сразу очищаем результаты
        if not query:
            self._hide_suggestions()
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
        
        # Показываем подсказки, если найдено больше 0 и введено 3+ символа
        if len(products) > 0 and len(self._last_query) >= 3:
            self._show_suggestions(products)
        
        # Вызываем callback для обновления UI
        self.after(0, lambda: self._on_search_result(products))
    
    def _show_suggestions(self, products: List[Product]) -> None:
        """Показ выпадающего списка подсказок."""
        # Формируем список строк для отображения
        suggestions = []
        for p in products:
            # Формат: "Артикул | Наименование"
            text = f"{p.article} | {p.name[:50]}..." if len(p.name) > 50 else f"{p.article} | {p.name}"
            suggestions.append((text, p.article))
        
        # Получаем координаты поля ввода
        x = self._entry.winfo_rootx()
        y = self._entry.winfo_rooty() + self._entry.winfo_height() + 2
        
        # Создаём или обновляем окно подсказок
        if self._suggestion_window is None:
            self._suggestion_window = SuggestionList(
                self._entry,
                on_select=self._on_suggestion_select,
                width=self._entry.winfo_width()
            )
        
        # Извлекаем только текст для отображения
        suggestion_texts = [s[0] for s in suggestions]
        self._suggestion_window.show_suggestions(suggestion_texts, x, y)
    
    def _hide_suggestions(self) -> None:
        """Скрытие выпадающего списка."""
        if self._suggestion_window:
            self._suggestion_window.hide()
    
    def _on_suggestion_select(self, display_text: str) -> None:
        """Обработка выбора подсказки."""
        logger.info(f"[SearchBar] Выбрана подсказка: {display_text}")
        
        # Извлекаем артикул из текста (до " | ")
        article = display_text.split(" | ")[0].strip()
        
        # Устанавливаем значение в поле
        self._entry.delete(0, "end")
        self._entry.insert(0, article)
        self._last_query = article
        
        # Скрываем подсказки
        self._hide_suggestions()
        
        # Выполняем поиск по выбранному артикулу
        self._do_search(article)

    def _on_entry_click(self, event) -> None:
        """Обработка клика на поле поиска — НЕ сбрасывать содержимое."""
        # Просто пропускаем событие, не очищаем поле
        pass
    
    def get_query(self) -> str:
        """Получение текущего поискового запроса."""
        return self._entry.get().strip()
    
    def clear(self) -> None:
        """Очистка поля поиска."""
        self._entry.delete(0, "end")
        self._last_query = ""
        self._hide_suggestions()
        if self._timer:
            self._timer.cancel()
            self._timer = None
