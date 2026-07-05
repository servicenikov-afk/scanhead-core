# libs/domain_models/product.py
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
@dataclass
class Product:
    article: str
    name: str
    barcodes: List[str] = field(default_factory=list)
    address: Optional[str] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    manufacturer_info: List[Dict[str, Any]] = field(default_factory=list)
    storage_locations: List[str] = field(default_factory=list)
    models: List[str] = field(default_factory=list)
    def matches_article_or_barcode(self, code: str) -> bool:
        code_norm = code.strip()
        if self.article == code_norm:
            return True
        return any(barcode == code_norm for barcode in self.barcodes)