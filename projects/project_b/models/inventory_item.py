# models/inventory_item.py (обновленный)
from dataclasses import dataclass
from typing import Optional

@dataclass
class InventoryItem:
    """Позиция в инвентаризации"""
    article: str
    name: str
    expected: float      # Ожидаемый остаток из ведомости
    actual: float = 0    # Фактический остаток (насчитанный)
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
        """Статус позиции"""
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
        """Цвет статуса для отображения"""
        if self.actual == self.expected:
            return "green"
        elif self.actual < self.expected:
            return "orange"
        else:
            return "blue"
    
    def add(self, quantity: float = 1.0):
        """Увеличивает фактическое количество"""
        self.actual += quantity
    
    def set_actual(self, quantity: float):
        """Устанавливает фактическое количество"""
        self.actual = quantity