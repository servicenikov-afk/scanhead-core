"""
Модуль нечеткого поиска и фильтрации данных.
Предоставляет алгоритмы для быстрого поиска по спискам объектов.
"""
from typing import List, Any, Callable, Optional, Union
import re


class FuzzyFilter:
    """
    Универсальный фильтр для списков данных.
    
    Поддерживает режимы:
        - exact: Точное совпадение
        - startswith: Начало строки
        - contains: Содержит подстроку
        - fuzzy: Нечеткий поиск (допуск на опечатки)
        - regex: Поиск по регулярному выражению
    
    Пример использования:
        items = ["Apple", "Banana", "Cherry"]
        ff = FuzzyFilter()
        res = ff.filter(items, "aple", mode="fuzzy")
        # Результат: ["Apple"]
    """

    def __init__(self, case_sensitive: bool = False):
        """
        Инициализация фильтра.
        
        Args:
            case_sensitive: Учитывать ли регистр при поиске.
        """
        self.case_sensitive = case_sensitive

    def filter(
        self,
        items: List[Any],
        query: str,
        mode: str = "contains",
        key_extractor: Optional[Callable[[Any], str]] = None
    ) -> List[Any]:
        """
        Отфильтровать список элементов по запросу.
        
        Args:
            items: Список элементов для фильтрации.
            query: Поисковый запрос.
            mode: Режим поиска ('exact', 'startswith', 'contains', 'fuzzy', 'regex').
            key_extractor: Функция для извлечения строки из объекта. 
                           Если None, используется str(item).
                           
        Returns:
            Отфильтрованный список элементов.
        """
        if not query:
            return items
        
        if key_extractor is None:
            key_extractor = str
            
        # Нормализация запроса и данных если регистр не важен
        if not self.case_sensitive:
            query = query.lower()
            
        results = []
        
        for item in items:
            text = key_extractor(item)
            if not self.case_sensitive:
                text = text.lower()
                
            if self._match(text, query, mode):
                results.append(item)
                
        return results

    def _match(self, text: str, query: str, mode: str) -> bool:
        """Проверка соответствия текста запросу в заданном режиме."""
        try:
            if mode == "exact":
                return text == query
                
            elif mode == "startswith":
                return text.startswith(query)
                
            elif mode == "contains":
                return query in text
                
            elif mode == "regex":
                return bool(re.search(query, text))
                
            elif mode == "fuzzy":
                return self._fuzzy_match(text, query)
                
            else:
                raise ValueError(f"Неизвестный режим поиска: {mode}")
        except re.error:
            # Если регулярка битая, считаем что нет совпадений
            return False

    def _fuzzy_match(self, text: str, query: str) -> bool:
        """
        Простая эвристика нечеткого поиска.
        Проверяет, содержатся ли символы запроса в тексте в правильном порядке.
        Допускает пропуск символов в тексте.
        """
        if not query:
            return True
        if len(query) > len(text):
            return False
            
        text_idx = 0
        matches = 0
        
        for char in query:
            found = False
            while text_idx < len(text):
                if text[text_idx] == char:
                    found = True
                    text_idx += 1
                    matches += 1
                    break
                text_idx += 1
            
            if not found:
                return False
                
        # Требует совпадения хотя бы 80% символов запроса для успеха
        threshold = max(1, int(len(query) * 0.8))
        return matches >= threshold

    def highlight(
        self, 
        text: str, 
        query: str, 
        open_tag: str = "<b>", 
        close_tag: str = "</b>"
    ) -> str:
        """
        Выделить совпадающие части текста тегами.
        Работает в режиме 'contains'.
        
        Args:
            text: Исходный текст.
            query: Запрос для подсветки.
            open_tag: Открывающий тег.
            close_tag: Закрывающий тег.
            
        Returns:
            Текст с тегами.
        """
        if not query:
            return text
            
        if not self.case_sensitive:
            lower_text = text.lower()
            lower_query = query.lower()
            idx = lower_text.find(lower_query)
            if idx != -1:
                return (
                    text[:idx] + 
                    open_tag + text[idx:idx+len(query)] + close_tag + 
                    text[idx+len(query):]
                )
        else:
            idx = text.find(query)
            if idx != -1:
                return (
                    text[:idx] + 
                    open_tag + text[idx:idx+len(query)] + close_tag + 
                    text[idx+len(query):]
                )
                
        return text
