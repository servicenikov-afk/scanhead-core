# address manager 
# core/address_manager.py
import csv
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class AddressDB:
    """База адресов хранения"""
    
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.addresses: Dict[str, str] = {}
        self.loaded = False
        
    def load(self) -> bool:
        """Загружает адреса из CSV"""
        try:
            if not self.csv_path.exists():
                logger.warning(f"Файл адресов не найден: {self.csv_path}")
                self.loaded = True
                return True
            
            self.addresses.clear()
            
            with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    article = row.get('article', '').strip()
                    address = row.get('address', '').strip()
                    if article and address:
                        self.addresses[article] = address
            
            self.loaded = True
            logger.info(f"Загружено адресов: {len(self.addresses)}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка загрузки адресов: {e}")
            return False
    
    def get_address(self, article: str) -> Optional[str]:
        """Возвращает адрес по артикулу"""
        if not self.loaded or not article:
            return None
        return self.addresses.get(article)
    
    def import_from_excel(self, excel_path: str, article_col: int, address_col: int) -> Tuple[bool, str, int]:
        """Импортирует адреса из Excel"""
        try:
            import pandas as pd
            
            df = pd.read_excel(excel_path, header=None)
            imported = 0
            
            for _, row in df.iterrows():
                try:
                    article = str(row.iloc[article_col]).strip() if not pd.isna(row.iloc[article_col]) else ""
                    address = str(row.iloc[address_col]).strip() if not pd.isna(row.iloc[address_col]) else ""
                    
                    if article and address and len(article) > 3:
                        self.addresses[article] = address
                        imported += 1
                except:
                    continue
            
            # Сохраняем
            self.save()
            return True, f"Импортировано адресов: {imported}", imported
            
        except Exception as e:
            return False, f"Ошибка импорта: {e}", 0
    
    def save(self) -> bool:
        """Сохраняет адреса в CSV"""
        try:
            self.csv_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['article', 'address'])
                writer.writeheader()
                for article, address in self.addresses.items():
                    writer.writerow({'article': article, 'address': address})
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения адресов: {e}")
            return False