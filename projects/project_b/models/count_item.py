# models/count_item.py
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class CountItem:
    """Позиция в подсчете"""
    article: str
    name: str
    quantity: float
    address: Optional[str] = None
    
    def add(self, amount: float = 1.0):
        self.quantity += amount# count item model 
