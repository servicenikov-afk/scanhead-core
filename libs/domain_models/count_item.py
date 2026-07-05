# libs/domain_models/count_item.py
from dataclasses import dataclass
from typing import Optional
@dataclass
class CountItem:
    article: str
    name: str
    quantity: float
    address: Optional[str] = None
    def add(self, amount: float = 1.0) -> None:
        self.quantity += amount