"""Address - Доменная модель адреса хранения

Модель представляет место хранения товара (ячейку, полку, зону).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Address:
    """Модель адреса хранения

    Атрибуты:
        code: Код адреса (например, "А-01-02")
        description: Описание адреса (опционально)
        quantity: Количество товара на этом адресе (для привязанных товаров)
    """
    code: str
    description: Optional[str] = None
    quantity: int = 0

    def __str__(self) -> str:
        return self.code

    def __eq__(self, other) -> bool:
        if not isinstance(other, Address):
            return False
        return self.code == other.code

    def __hash__(self) -> int:
        return hash(self.code)
