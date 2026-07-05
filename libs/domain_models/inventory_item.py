# libs/domain_models/inventory_item.py
from dataclasses import dataclass
from typing import Optional
@dataclass
class InventoryItem:
    article: str
    name: str
    expected: float
    actual: float = 0.0
    address: Optional[str] = None
    source_row: int = 0
    @property
    def diff(self) -> float:
        return self.actual - self.expected
    @property
    def diff_abs(self) -> float:
        return abs(self.diff)
    @property
    def status(self) -> str:
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
        if self.actual == self.expected:
            return "green"
        elif self.actual < self.expected:
            return "orange"
        else:
            return "blue"
    def add(self, quantity: float = 1.0) -> None:
        self.actual += quantity
    def set_actual(self, quantity: float) -> None:
        self.actual = quantity