# modules/address_manager.py
import pandas as pd
import logging
import re
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import difflib
logger = logging.getLogger(__name__)
class AddressManager:
    def __init__(self, config):
        self.config = config
        self.data = {}
        self.loaded = False
        self.csv_path = Path(config.get('paths.address_csv_path',
                                       str(Path.home() / "AppData" / "Local" / "StickerMakerV3" / "addresses.csv")))
    def load_addresses(self) -> bool:
        try:
            if not self.csv_path.exists():
                self.data, self.loaded = {}, True
                return True
            self.data = {}
            with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
                for row in csv.DictReader(f):
                    art, addr = row.get('article', '').strip(), row.get('address', '').strip()
                    if art and addr:
                        self.data[art] = addr
            self.loaded = True
            return True
        except Exception as e:
            logger.error(f"Ошибка загрузки: {e}")
            return False
    def save_addresses(self) -> bool:
        try:
            self.csv_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.csv_path, 'w', encoding='utf-8', newline='') as f:
                w = csv.DictWriter(f, fieldnames=['article', 'address'])
                w.writeheader()
                for a, addr in self.data.items():
                    w.writerow({'article': a, 'address': addr})
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}")
            return False
    def find_address(self, article: str, name: str = None) -> Optional[str]:
        if not self.loaded:
            self.load_addresses()
        article = self._normalize(article)
        if article in self.data:
            return self.data[article]
        if self.data:
            #matches = difflib.get_close_matches(article, list(self.data.keys()), n=1, cutoff=0.8)
            #if matches:
            #    return self.data[matches[0]]
            return None
    def import_from_excel(self, path: str, art_col: str, addr_col: str) -> Tuple[bool, str]:
        try:
            art_idx = int(art_col.replace('Колонка', '').strip()) - 1
            addr_idx = int(addr_col.replace('Колонка', '').strip()) - 1
            
            df = pd.read_excel(path, header=None)
            
            imported = 0
            skipped = 0
            for _, row in df.iterrows():
                try:
                    art = str(row.iloc[art_idx]).strip() if not pd.isna(row.iloc[art_idx]) else ""
                    addr = str(row.iloc[addr_idx]).strip() if not pd.isna(row.iloc[addr_idx]) else ""
                    
                    # Фильтр мусора: артикул должен быть похож на артикул (цифры, точки, тире)
                    if art and addr and re.match(r'^[\d\.\-]+$', art) and len(art) > 5:
                        art_norm = self._normalize(art)
                        if art_norm:
                            self.data[art_norm] = addr
                            imported += 1
                    else:
                        skipped += 1
                except:
                    skipped += 1
            
            if imported > 0:
                self.save_addresses()
                return True, f"Импортировано: {imported} (отфильтровано мусора: {skipped})"
            else:
                return False, "Не найдено валидных пар Артикул+Адрес"
                
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    def analyze_excel_file(self, path: str) -> Dict[str, Any]:
        try:
            if not self.loaded:
                self.load_addresses()
                
            df = pd.read_excel(path, header=None)
            res = {'columns': [f"Колонка {i+1}" for i in range(len(df.columns))],
                   'sample': [], 'suggestions': {'article': [], 'address': []}}
            
            # Показываем образец
            for i in range(min(5, len(df))):
                row = {}
                for j in range(min(5, len(df.columns))):
                    val = df.iloc[i, j]
                    row[f"Кол {j+1}"] = str(val)[:30] if not pd.isna(val) else ""
                res['sample'].append(row)
            
            # Поиск колонки с артикулами по базе (только точные совпадения)
            if self.data and len(self.data) > 0:
                import random
                # Берём 10 артикулов из базы
                sample_articles = random.sample(list(self.data.keys()), min(10, len(self.data)))
                
                best_col, best_score = None, 0
                for col in range(min(20, len(df.columns))):
                    # Собираем значения из колонки (первые 100 строк)
                    col_values = set()
                    for i in range(min(100, len(df))):
                        v = df.iloc[i, col]
                        if not pd.isna(v):
                            col_values.add(str(v).strip())
                    
                    # Считаем точные совпадения
                    score = sum(1 for a in sample_articles if a in col_values)
                    if score > best_score:
                        best_score, best_col = score, col
                
                if best_col is not None and best_score >= len(sample_articles) * 0.3:  # 30% совпадений
                    res['suggestions']['article'] = [f"Колонка {best_col+1}"]
                    
                    # Поиск адресов (рядом или с паттерном)
                    addr_candidates = []
                    for col in range(max(0, best_col-3), min(len(df.columns), best_col+10)):
                        if col == best_col: continue
                        vals = [str(df.iloc[i, col]) for i in range(min(50, len(df))) if not pd.isna(df.iloc[i, col])]
                        # Паттерны: буква+цифры, просто буква E, формат D102
                        if sum(1 for v in vals if re.search(r'^[A-ZА-Я][0-9]+$|^[A-ZА-Я]$', v)) > 3:
                            addr_candidates.append(f"Колонка {col+1}")
                    res['suggestions']['address'] = addr_candidates[:3]
            
            return res
        except Exception as e:
            return {'error': str(e)}
    @staticmethod
    def _normalize(article: str) -> str:
        return str(article).strip()
    def get_stats(self) -> Dict[str, Any]:
        return {'loaded': self.loaded, 'count': len(self.data),
                'sample': list(self.data.items())[:5] if self.data else []}