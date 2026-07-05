# libs/domain_models/address.py
from dataclasses import dataclass
from typing import Optional
@dataclass
class Address:
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