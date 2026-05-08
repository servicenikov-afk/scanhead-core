"""CountItem - Модель позиции подсчета

Модель представляет позицию в списке подсчета товаров.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CountItem:
    """Позиция в подсчете
    
    Атрибуты:
        article: Артикул товара
        name: Наименование товара
        quantity: Количество
        address: Адрес хранения (опционально)
    """
    
    article: str
    name: str
    quantity: float
    address: Optional[str] = None
    
    def add(self, amount: float = 1.0) -> None:
        """Добавляет количество к текущему
        
        Args:
            amount: Количество для добавления (по умолчанию 1.0)
        """
        self.quantity += amount
