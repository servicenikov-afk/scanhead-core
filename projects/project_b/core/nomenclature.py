# nomenclature db 
# core/nomenclature.py
import csv
import logging
from pathlib import Path
from typing import Dict, Optional, List
from models.product import Product

logger = logging.getLogger(__name__)

class NomenclatureDB:
    """База номенклатуры (read-only)"""
    
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.products: Dict[str, Product] = {}  # по артикулу
        self.barcode_index: Dict[str, str] = {}  # штрих-код -> артикул
        self.loaded = False
        
    def load(self) -> bool:
        """Загружает номенклатуру из CSV"""
        try:
            if not self.csv_path.exists():
                logger.error(f"Файл не найден: {self.csv_path}")
                return False
            
            self.products.clear()
            self.barcode_index.clear()
            
            with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    name = row.get('Наименование', '').strip()
                    article = row.get('Артикул', '').strip()
                    barcodes_str = row.get('Штрих-коды', '').strip()
                    
                    # Пропускаем пустые артикулы и служебные строки
                    if not article or article == 'Артикул':
                        continue
                    
                    # Парсим штрих-коды
                    barcodes = []
                    if barcodes_str:
                        for bc in barcodes_str.split(','):
                            bc_clean = bc.strip()
                            if bc_clean and bc_clean != article:
                                barcodes.append(bc_clean)
                                self.barcode_index[bc_clean] = article
                    
                    product = Product(
                        article=article,
                        name=name if name else article,
                        barcodes=barcodes
                    )
                    self.products[article] = product
            
            self.loaded = True
            logger.info(f"Загружено товаров: {len(self.products)}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка загрузки номенклатуры: {e}")
            return False
    
    def find_by_article_or_barcode(self, code: str) -> Optional[Product]:
        """Ищет товар по артикулу или штрих-коду"""
        if not self.loaded or not code:
            return None
        
        code_norm = code.strip()
        
        # Сначала ищем по артикулу
        if code_norm in self.products:
            return self.products[code_norm]
        
        # Затем по штрих-коду
        if code_norm in self.barcode_index:
            article = self.barcode_index[code_norm]
            return self.products.get(article)
        
        return None
    
    def get_product_info(self, code: str) -> tuple[str, str, bool]:
        """Возвращает (артикул, наименование, найдено)"""
        product = self.find_by_article_or_barcode(code)
        if product:
            return product.article, product.name, True
        return code, "Не найдено в базе", False