"""
Inventory Parser - Core Module.

Parses inventory Excel files and extracts product positions with:
- Article (from multiple possible columns)
- Product name
- Expected quantity
- Storage address
- Source row information

This module is designed to be standalone and reusable across different projects.
It does not depend on any project-specific code or database connections.
"""

import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class InventoryParser:
    """
    Parser for inventory Excel files.
    
    Automatically detects column headers and extracts product positions
    from various Excel formats used in warehouse management systems.
    """
    
    def parse_inventory_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse an inventory Excel file and extract product positions.
        
        Args:
            file_path: Path to the Excel file (.xlsx, .xls)
            
        Returns:
            List of dictionaries containing product information:
            - article: Product article/code
            - name: Product name
            - expected: Expected quantity
            - address: Storage address
            - source_row: Row number in the source file
            
        Raises:
            FileNotFoundError: If the file does not exist
            Exception: For other parsing errors (logged and returns empty list)
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"Файл не найден: {file_path}")
                return []
            
            df = pd.read_excel(file_path, header=None, dtype=str)
            logger.info(f"Файл загружен, строк: {len(df)}, столбцов: {len(df.columns)}")
            
            # Поиск строки с заголовками
            header_row = self._find_header_row(df)
            
            if header_row is None:
                logger.warning("Заголовки не найдены, использую стандартные колонки")
                header_row = 6
            
            # Определение колонок
            columns = self._detect_columns(df, header_row)
            logger.info(f"Колонки: {columns}")
            
            # Парсинг позиций
            positions = self._parse_positions(df, header_row, columns)
            
            logger.info(f"Найдено позиций: {len(positions)}")
            return positions
            
        except Exception as e:
            logger.error(f"Ошибка парсинга: {e}", exc_info=True)
            return []
    
    def _find_header_row(self, df: pd.DataFrame, max_search: int = 10) -> Optional[int]:
        """
        Find the row containing column headers.
        
        Searches for a row containing 'номенклатура.артикул' or similar patterns.
        
        Args:
            df: DataFrame to search in
            max_search: Maximum number of rows to search
            
        Returns:
            Row index if found, None otherwise
        """
        for idx in range(min(max_search, len(df))):
            row = df.iloc[idx].astype(str).str.lower()
            if any('номенклатура.артикул' in str(v) for v in row):
                return idx
        return None
    
    def _detect_columns(self, df: pd.DataFrame, header_row: int) -> Dict[str, Optional[int]]:
        """
        Detect column indices by analyzing header row.
        
        Args:
            df: DataFrame with inventory data
            header_row: Index of the header row
            
        Returns:
            Dictionary with column indices:
            - article2: Column for 'Номенклатура.Артикул 2'
            - article: Column for 'Артикул'
            - name: Column for product name
            - expected: Column for expected quantity
            - address: Column for storage address
        """
        headers = df.iloc[header_row].astype(str).str.lower()
        
        columns = {
            'article2': None,
            'article': None,
            'name': None,
            'expected': None,
            'address': None
        }
        
        for i, h in enumerate(headers):
            h_clean = h.replace(' ', '').replace('_', '').replace('.', '')
            
            if 'номенклатураартикул2' in h_clean or ('артикул2' in h_clean and 'номенклатура' in h_clean):
                columns['article2'] = i
            elif 'артикул' in h_clean and columns['article2'] != i and ('номенклатура' not in h_clean or 'артикул2' not in h_clean):
                columns['article'] = i
            elif 'номенклатура' in h_clean and 'артикул' not in h_clean and 'код' not in h_clean:
                columns['name'] = i
            elif 'конечныйостаток' in h_clean or 'конечный остаток' in h:
                columns['expected'] = i
            elif 'адрес' in h_clean:
                columns['address'] = i
        
        return columns
    
    def _parse_positions(
        self, 
        df: pd.DataFrame, 
        header_row: int, 
        columns: Dict[str, Optional[int]]
    ) -> List[Dict[str, Any]]:
        """
        Parse product positions from DataFrame.
        
        Args:
            df: DataFrame with inventory data
            header_row: Index of the header row
            columns: Dictionary with detected column indices
            
        Returns:
            List of parsed product positions
        """
        positions = []
        start_row = header_row + 2
        
        for idx in range(start_row, len(df)):
            row = df.iloc[idx]
            
            # Извлечение артикула (проверка обоих полей)
            article = self._extract_article(row, columns)
            
            # Извлечение наименования
            name = self._extract_string_field(row, columns['name'])
            
            # Извлечение количества
            expected = 0.0
            if columns['expected'] is not None and len(row) > columns['expected']:
                expected = self._parse_quantity(row[columns['expected']])
            
            # Извлечение адреса
            address = self._extract_string_field(row, columns['address'])
            
            # Пропуск итоговых строк
            if self._is_total_row(row):
                break
            
            # Пропуск пустых строк
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
        
        return positions
    
    def _extract_article(self, row: pd.Series, columns: Dict[str, Optional[int]]) -> Optional[str]:
        """
        Extract article from row, checking both article fields.
        
        Args:
            row: DataFrame row
            columns: Dictionary with column indices
            
        Returns:
            Article string or None
        """
        # Сначала проверяем Артикул 2
        if columns['article2'] is not None and len(row) > columns['article2']:
            val = str(row[columns['article2']]).strip()
            if val and val != 'nan':
                return val
        
        # Затем проверяем основной Артикул
        if columns['article'] is not None and len(row) > columns['article']:
            val = str(row[columns['article']]).strip()
            if val and val != 'nan':
                return val
        
        return None
    
    def _extract_string_field(self, row: pd.Series, col_idx: Optional[int]) -> str:
        """
        Extract string field from row by column index.
        
        Args:
            row: DataFrame row
            col_idx: Column index
            
        Returns:
            String value or empty string
        """
        if col_idx is not None and len(row) > col_idx:
            val = str(row[col_idx]).strip()
            if val and val != 'nan':
                return val
        return ""
    
    def _parse_quantity(self, value) -> float:
        """
        Parse quantity value from various formats.
        
        Handles different number formats (comma/dot decimal separator,
        spaces as thousand separators).
        
        Args:
            value: Raw value from Excel cell
            
        Returns:
            Float value or 0.0 if parsing fails
        """
        if not value or value == 'nan':
            return 0.0
        try:
            s = str(value).strip().replace(',', '.').replace(' ', '')
            s = ''.join(c for c in s if c.isdigit() or c == '.' or c == '-')
            return float(s) if s else 0.0
        except Exception:
            return 0.0
    
    def _is_total_row(self, row: pd.Series) -> bool:
        """
        Check if row is a total/summary row.
        
        Args:
            row: DataFrame row
            
        Returns:
            True if row contains 'итого' (total), False otherwise
        """
        row_str = ' '.join([
            str(v).lower() 
            for v in row[:10] 
            if pd.notna(v) and str(v) != 'nan'
        ])
        return 'итого' in row_str
