"""
Поисковая строка с debounce (задержкой) для предотвращения частых запросов.
"""

import logging
from typing import Callable, Any, Optional
import threading
import time

import customtkinter as ctk

from services.interfaces import ISearchService
from libs.domain_models import Product

logger = logging.getLogger(__name__)


class SearchBar(ctk.CTkFrame):
    """
    Поле поиска с debounce 300мс.
    
    При вводе текста запускается таймер. Если пользователь продолжает ввод,
    таймер сбрасывается. Поиск выполняется только после паузы в 300мс.
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
        
        # Вызываем callback для обновления UI
        # Важно: вызываем через after, чтобы гарантировать главный поток
        self.after(0, lambda: self._on_search_result(products))
    
    def get_query(self) -> str:
        """Получение текущего поискового запроса."""
        return self._entry.get().strip()
    
    def clear(self) -> None:
        """Очистка поля поиска."""
        self._entry.delete(0, "end")
        self._last_query = ""
        if self._timer:
            self._timer.cancel()
            self._timer = None
