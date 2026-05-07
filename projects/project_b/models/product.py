# models/product.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Product:
    """Модель товара"""
    article: str
    name: str
    barcodes: list[str] = None
    address: Optional[str] = None
    
    def __post_init__(self):
        if self.barcodes is None:
            self.barcodes = []
    
    def matches_article_or_barcode(self, code: str) -> bool:
        """Проверяет, соответствует ли код артикулу или штрих-коду"""
        code_norm = code.strip()
        if self.article == code_norm:
            return True
        return any(barcode == code_norm for barcode in self.barcodes)# product model 
