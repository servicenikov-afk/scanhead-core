"""Product - Доменная модель товара

Модель представляет товар с артикулом, наименованием и штрих-кодами.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class Product:
    """Модель товара
    
    Атрибуты:
        article: Артикул товара
        name: Наименование товара
        barcodes: Список штрих-кодов
        address: Адрес хранения (опционально)
        unit: Единица измерения (из nomenclature.db)
        description: Описание товара (из nomenclature.db)
        category: Категория товара (из css_export.db)
        manufacturer_info: Информация от производителя (из css_export.db)
        storage_locations: Все адреса хранения (из store.db)
        models: Список моделей оборудования где используется (из css_export.db)
    """
    
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
        """Проверяет, соответствует ли код артикулу или штрих-коду
        
        Args:
            code: Код для проверки (артикул или штрих-код)
            
        Returns:
            True если код соответствует артикулу или одному из штрих-кодов
        """
        code_norm = code.strip()
        if self.article == code_norm:
            return True
        return any(barcode == code_norm for barcode in self.barcodes)
