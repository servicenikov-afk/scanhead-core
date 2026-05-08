"""InventoryItem - Модель позиции инвентаризации

Модель представляет позицию в инвентаризации с ожидаемыми и фактическими остатками.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class InventoryItem:
    """Позиция в инвентаризации
    
    Атрибуты:
        article: Артикул товара
        name: Наименование товара
        expected: Ожидаемый остаток из ведомости
        actual: Фактический остаток (насчитанный)
        address: Адрес хранения (опционально)
        source_row: Номер строки в исходном файле
    """
    
    article: str
    name: str
    expected: float      # Ожидаемый остаток из ведомости
    actual: float = 0.0  # Фактический остаток (насчитанный)
    address: Optional[str] = None
    source_row: int = 0  # Номер строки в исходном файле
    
    @property
    def diff(self) -> float:
        """Разница (факт - ожидание)"""
        return self.actual - self.expected
    
    @property
    def diff_abs(self) -> float:
        """Абсолютная разница"""
        return abs(self.diff)
    
    @property
    def status(self) -> str:
        """Статус позиции
        
        Returns:
            Строковое представление статуса
        """
        if self.actual == self.expected:
            return "✓ Совпало"
        elif self.actual < self.expected:
            shortage = self.expected - self.actual
            return f"⚠ Недосдача: {shortage:.2f}"
        else:
            surplus = self.actual - self.expected
            return f"➕ Излишек: +{surplus:.2f}"
    
    @property
    def status_color(self) -> str:
        """Цвет статуса для отображения
        
        Returns:
            Название цвета (green, orange, blue)
        """
        if self.actual == self.expected:
            return "green"
        elif self.actual < self.expected:
            return "orange"
        else:
            return "blue"
    
    def add(self, quantity: float = 1.0) -> None:
        """Увеличивает фактическое количество
        
        Args:
            quantity: Количество для добавления (по умолчанию 1.0)
        """
        self.actual += quantity
    
    def set_actual(self, quantity: float) -> None:
        """Устанавливает фактическое количество
        
        Args:
            quantity: Новое фактическое количество
        """
        self.actual = quantity
