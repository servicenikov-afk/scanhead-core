"""
Поисковая строка с debounce (задержкой) и выпадающим списком подсказок.
"""

import logging
from typing import Callable, Any, Optional, List, Dict
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
        debounce_ms: int = 300,
        font_size: int = 18,
        auto_focus: bool = True,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(master)
        self._search_service = search_service
        self._on_search_result = on_search_result
        self._debounce_ms = debounce_ms
        self._config = config or {}
        
        # Получаем настройки из конфига или используем значения по умолчанию
        self._font_size = self._config.get("search_font_size", font_size)
        self._auto_focus = self._config.get("search_autofocus", auto_focus)
        self._focus_delay = self._config.get("search_autofocus_delay", 1.0)  # секунды
        
        self._timer: Optional[threading.Timer] = None
        self._last_query = ""
        self._suggestion_window: Optional[SuggestionList] = None
        self._update_geometry_after_id: Optional[str] = None
        self._pending_update_id: Optional[str] = None
        
        logger.debug(f"[SearchBar] Инициализация (font_size={self._font_size}, auto_focus={self._auto_focus}, focus_delay={self._focus_delay})")
        
        # Создаём поле ввода с крупным шрифтом
        # Высота поля = шрифт + 8px (отступы) для рационального использования пространства
        entry_height = self._font_size + 8
        
        self._entry = ctk.CTkEntry(
            self,
            placeholder_text="🔍 Поиск по артикулу, названию или штрих-коду...",
            height=entry_height,
            font=ctk.CTkFont(size=self._font_size, family="Arial")
        )
        self._entry.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Привязываем обработчик нажатий
        self._entry.bind("<KeyRelease>", self._on_key_release)
        self._entry.bind("<Button-1>", self._on_entry_click)  # Обработка клика - не сбрасывать
        self._entry.bind("<FocusOut>", lambda e: self._hide_suggestions())
        
        # Привязка изменения размера entry для обновления геометрии dropdown
        self._entry.bind("<Configure>", self._on_entry_configure)
        
        # Автофокус с задержкой при создании
        if self._auto_focus:
            delay_ms = int(self._focus_delay * 1000)
            self.after(delay_ms, self._set_initial_focus)
        
        logger.debug("[SearchBar] Поле поиска создано")
    
    def _set_initial_focus(self) -> None:
        """Установка начального фокуса на поле ввода."""
        try:
            if self._entry.winfo_exists():
                self._entry.focus_set()
        except Exception as e:
            logger.warning(f"[SearchBar] Не удалось установить фокус: {e}")
    
    def _on_key_release(self, event) -> None:
        """Обработчик отпускания клавиши."""
        query = self._entry.get().strip()
        
        # Если поле пустое — очистить результаты и выйти
        if not query:
            if self._timer:
                self._timer.cancel()
                self._timer = None
            self._hide_suggestions()
            self._on_search_result([])
            self._last_query = ""
            return
        
        # Если запрос не изменился - игнорируем
        if query == self._last_query:
            return
        
        self._last_query = query
        
        # Отменяем предыдущий таймер
        if self._timer is not None:
            self._timer.cancel()
        
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
        
        # Если нет результатов - скрываем список и выходим
        if not products:
            self._hide_suggestions()
            self._on_search_result([])
            return
        
        # Показываем подсказки, если введено 3+ символа
        if len(self._last_query) >= 3:
            self._show_suggestions(products)
        else:
            # Если меньше 3 символов - скрываем список
            self._hide_suggestions()
        
        # Вызываем callback для обновления UI
        self.after(0, lambda: self._on_search_result(products))
    
    def _show_suggestions(self, products: List[Product]) -> None:
        """Показ выпадающего списка подсказок."""
        # Формируем список строк для отображения
        suggestions = []
        for p in products:
            # Формат: "Артикул | Наименование"
            text = f"{p.article} | {p.name[:80]}..." if len(p.name) > 80 else f"{p.article} | {p.name}"
            suggestions.append((text, p.article))
        
        # Извлекаем только текст для отображения
        suggestion_texts = [s[0] for s in suggestions]
        
        # Обновление списка подсказок только через self.after(1, ...) для стабильности
        self._pending_update_id = self.after(1, lambda: self._do_show_suggestions(suggestion_texts))
    
    def _do_show_suggestions(self, suggestion_texts: List[str]) -> None:
        """Внутренний метод показа подсказок (вызывается через after)."""
        self._pending_update_id = None
        
        if not suggestion_texts:
            self._hide_suggestions()
            return
        
        # Получаем координаты поля ввода
        try:
            if not self._entry.winfo_exists():
                return
            x = self._entry.winfo_rootx()
            y = self._entry.winfo_rooty() + self._entry.winfo_height() + 2
            entry_width = self._entry.winfo_width()
        except Exception as e:
            logger.warning(f"[SearchBar] Не удалось получить координаты entry: {e}")
            return
        
        # Создаём или обновляем окно подсказок
        if self._suggestion_window is None or not self._suggestion_window.winfo_exists():
            self._suggestion_window = SuggestionList(
                self._entry,
                on_select=self._on_suggestion_select,
                width=entry_width + 30,  # Ширина = ширина entry + 30px
                max_height=200,
                font_size=self._font_size
            )
        
        # Показываем подсказки (внутри show_suggestions вызывается _update_position)
        self._suggestion_window.show_suggestions(suggestion_texts, x, y)
    
    def _update_dropdown_geometry(self, x: int = None, y: int = None) -> None:
        """Обновить позицию и ширину dropdown относительно entry."""
        if self._suggestion_window is None or not self._suggestion_window.winfo_exists():
            return
        
        # Если координаты не переданы - получаем текущие
        if x is None:
            x = self._entry.winfo_rootx()
        if y is None:
            y = self._entry.winfo_rooty() + self._entry.winfo_height() + 2
        
        # Устанавливаем ширину dropdown = ширине entry
        entry_width = self._entry.winfo_width()
        self._suggestion_window.frame.configure(width=entry_width)
        
        # Обновляем позицию
        self._suggestion_window.geometry(f"+{x}+{y}")
    
    def _on_entry_configure(self, event=None) -> None:
        """Обработчик изменения размера entry - обновляем ширину dropdown."""
        # Отменяем предыдущее отложенное событие
        if self._update_geometry_after_id is not None:
            try:
                self.after_cancel(self._update_geometry_after_id)
            except Exception:
                pass
        
        # Планируем обновление геометрии с небольшой задержкой
        self._update_geometry_after_id = self.after(50, self._delayed_update_dropdown)
    
    def _delayed_update_dropdown(self) -> None:
        """Отложенное обновление геометрии dropdown."""
        self._update_geometry_after_id = None
        if self._suggestion_window and self._suggestion_window.winfo_exists():
            self._update_dropdown_geometry()
    
    def _hide_suggestions(self) -> None:
        """Скрытие выпадающего списка."""
        if self._suggestion_window:
            self._suggestion_window.hide()
    
    def _on_suggestion_select(self, display_text: str) -> None:
        """Обработка выбора подсказки — с корректной очисткой поля."""
        logger.info(f"[SearchBar] Выбрана подсказка: {display_text}")
        
        # Извлекаем артикул из текста (до " | ")
        article = display_text.split(" | ")[0].strip()
        
        # 1. Сначала обновить UI (ProductDetails, PrintQueue, etc.)
        #    Но не выполняем поиск сразу - сделаем это после очистки поля
        
        # 2. СБРОСИТЬ _last_query ПЕРЕД очисткой поля
        #    Это предотвратит запуск нового поиска при delete()
        self._last_query = ""
        
        # 3. Отменить любой отложенный поиск (на всякий случай)
        if self._timer:
            self._timer.cancel()
            self._timer = None
        
        # 4. Теперь безопасно очистить поле
        self._entry.delete(0, "end")
        
        # 5. Вставить артикул в поле (это вызовет KeyRelease, но _last_query="" защитит)
        self._entry.insert(0, article)
        
        # 6. Скрыть список подсказок
        self._hide_suggestions()
        
        # 7. Обновить UI с выбранным продуктом
        #    Выполняем поиск по артикулу для заполнения полей
        self._do_search(article)
        
        # 8. Вернуть фокус с задержкой (если включено)
        if self._auto_focus:
            delay_ms = int(self._focus_delay * 1000)
            self.after(delay_ms, self._restore_focus_after_select)
    
    def _restore_focus_after_select(self) -> None:
        """Восстановление фокуса на поле после выбора подсказки."""
        try:
            if self._entry.winfo_exists():
                self._entry.focus_set()
        except Exception as e:
            logger.warning(f"[SearchBar] Не удалось восстановить фокус: {e}")
    
    def apply_settings(self, config: dict) -> None:
        """Применить изменённые настройки без пересоздания."""
        # Шрифт
        if "search_font_size" in config:
            self._font_size = config["search_font_size"]
            new_font = ctk.CTkFont(size=self._font_size, family="Arial")
            self._entry.configure(font=new_font)
            # Обновить шрифт в списке подсказок если он существует
            if hasattr(self, '_suggestion_window') and self._suggestion_window is not None:
                if hasattr(self._suggestion_window, 'update_font_size'):
                    self._suggestion_window.update_font_size(self._font_size)
        
        # Автофокус (применится при следующем переключении вкладки или создании)
        if "search_autofocus" in config:
            self._auto_focus = config["search_autofocus"]
        if "search_autofocus_delay" in config:
            self._focus_delay = config["search_autofocus_delay"]

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
        
        # Отменяем отложенное событие обновления геометрии
        if self._update_geometry_after_id is not None:
            try:
                self.after_cancel(self._update_geometry_after_id)
            except Exception:
                pass
            self._update_geometry_after_id = None
        
        # Отменяем отложенное событие обновления подсказок
        if self._pending_update_id is not None:
            try:
                self.after_cancel(self._pending_update_id)
            except Exception:
                pass
            self._pending_update_id = None
