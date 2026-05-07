# core/inventory_parser.py
import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class InventoryParser:
    def parse_inventory_file(self, file_path: str) -> List[Dict[str, Any]]:
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"Файл не найден: {file_path}")
                return []
            
            df = pd.read_excel(file_path, header=None, dtype=str)
            logger.info(f"Файл загружен, строк: {len(df)}, столбцов: {len(df.columns)}")
            
            # Поиск строки с заголовками
            header_row = None
            for idx in range(min(10, len(df))):
                row = df.iloc[idx].astype(str).str.lower()
                if any('номенклатура.артикул' in str(v) for v in row):
                    header_row = idx
                    break
            
            if header_row is None:
                logger.warning("Заголовки не найдены, использую стандартные колонки")
                header_row = 6
            
            headers = df.iloc[header_row].astype(str).str.lower()
            col_article2 = None  # Номенклатура.Артикул 2
            col_article = None    # Артикул
            col_name = None
            col_expected = None
            col_address = None
            
            for i, h in enumerate(headers):
                h_clean = h.replace(' ', '').replace('_', '').replace('.', '')
                if 'номенклатураартикул2' in h_clean or ('артикул2' in h_clean and 'номенклатура' in h_clean):
                    col_article2 = i
                elif 'артикул' in h_clean and col_article2 != i and ('номенклатура' not in h_clean or 'артикул2' not in h_clean):
                    col_article = i
                elif 'номенклатура' in h_clean and 'артикул' not in h_clean and 'код' not in h_clean:
                    col_name = i
                elif 'конечныйостаток' in h_clean or 'конечный остаток' in h:
                    col_expected = i
                elif 'адрес' in h_clean:
                    col_address = i
            
            logger.info(f"Колонки: артикул2={col_article2}, артикул={col_article}, наименование={col_name}, остаток={col_expected}, адрес={col_address}")
            
            positions = []
            start_row = header_row + 2
            
            for idx in range(start_row, len(df)):
                row = df.iloc[idx]
                
                # Проверяем оба поля на артикул
                article = None
                if col_article2 is not None and len(row) > col_article2 and pd.notna(row[col_article2]):
                    val = str(row[col_article2]).strip()
                    if val and val != 'nan':
                        article = val
                
                if not article and col_article is not None and len(row) > col_article and pd.notna(row[col_article]):
                    val = str(row[col_article]).strip()
                    if val and val != 'nan':
                        article = val
                
                name = ""
                if col_name is not None and len(row) > col_name and pd.notna(row[col_name]):
                    val = str(row[col_name]).strip()
                    if val and val != 'nan':
                        name = val
                
                expected = 0.0
                if col_expected is not None and len(row) > col_expected and pd.notna(row[col_expected]):
                    expected = self._parse_quantity(row[col_expected])
                
                address = ""
                if col_address is not None and len(row) > col_address and pd.notna(row[col_address]):
                    val = str(row[col_address]).strip()
                    if val and val != 'nan':
                        address = val
                
                # Пропускаем итоговые строки
                row_str = ' '.join([str(v).lower() for v in row[:10] if pd.notna(v) and str(v) != 'nan'])
                if 'итого' in row_str:
                    break
                
                if not article and not name:
                    continue
                
                if article:
                    positions.append({
                        'article': article,
                        'name': name or '',
                        'expected': expected,
                        'address': address,
                        'source_row': idx + 1
                    })
            
            logger.info(f"Найдено позиций: {len(positions)}")
            return positions
            
        except Exception as e:
            logger.error(f"Ошибка парсинга: {e}", exc_info=True)
            return []
    
    def _parse_quantity(self, value) -> float:
        if not value or value == 'nan':
            return 0.0
        try:
            s = str(value).strip().replace(',', '.').replace(' ', '')
            s = ''.join(c for c in s if c.isdigit() or c == '.' or c == '-')
            return float(s) if s else 0.0
        except:
            return 0.0