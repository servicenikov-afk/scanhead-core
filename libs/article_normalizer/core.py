"""
Article Normalizer Core
Базовая логика нормализации артикулов.
"""

import re
from typing import Optional


class ArticleNormalizer:
    """
    Класс для нормализации артикулов и товарных идентификаторов.
    
    Примеры использования:
        normalizer = ArticleNormalizer()
        normalized = normalizer.normalize(" 123-abc ")
        # результат: "123ABC"
    """

    def __init__(self, remove_special_chars: bool = True, to_upper: bool = True):
        """
        Инициализация нормализатора.
        
        Args:
            remove_special_chars: Удалять специальные символы (кроме букв и цифр)
            to_upper: Приводить к верхнему регистру
        """
        self.remove_special_chars = remove_special_chars
        self.to_upper = to_upper

    def normalize(self, article: str) -> str:
        """
        Нормализовать артикул.
        
        Args:
            article: Исходный артикул
            
        Returns:
            Нормализованный артикул
        """
        if not article:
            return ""
        
        result = article.strip()
        
        if self.to_upper:
            result = result.upper()
        
        if self.remove_special_chars:
            # Оставляем только буквы, цифры и дефисы (частый разделитель в артикулах)
            result = re.sub(r'[^A-Z0-9\-]', '', result, flags=re.IGNORECASE)
        
        # Удаляем множественные дефисы
        result = re.sub(r'-+', '-', result)
        
        # Удаляем дефисы в начале и конце
        result = result.strip('-')
        
        return result

    def validate(self, article: str, min_length: int = 1, max_length: int = 50) -> bool:
        """
        Проверить валидность артикула после нормализации.
        
        Args:
            article: Артикл для проверки
            min_length: Минимальная длина
            max_length: Максимальная длина
            
        Returns:
            True если артикул валиден
        """
        normalized = self.normalize(article)
        if not normalized:
            return False
        
        if len(normalized) < min_length or len(normalized) > max_length:
            return False
        
        return True

    def extract_prefix(self, article: str) -> Optional[str]:
        """
        Извлечь префикс из артикула (если есть).
        TODO: Реализовать логику выделения префиксов.
        
        Args:
            article: Артикул
            
        Returns:
            Префикс или None
        """
        # Пока заглушка - требует доработки
        raise NotImplementedError("Метод extract_prefix требует реализации")

    def extract_base(self, article: str) -> str:
        """
        Извлечь базовую часть артикула (без префикса).
        TODO: Реализовать логику выделения базовой части.
        
        Args:
            article: Артикул
            
        Returns:
            Базовая часть артикула
        """
        # Пока просто возвращаем нормализованный артикул
        return self.normalize(article)
