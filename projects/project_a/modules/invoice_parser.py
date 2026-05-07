# modules/invoice_parser.py
"""
Парсер накладных Excel для Sticker Maker v3.3
"""

import pandas as pd
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import traceback

logger = logging.getLogger(__name__)


class InvoiceParser:
    """Парсер накладных из различных форматов Excel"""
    
    # Конфигурация для разных форматов накладных
    FORMATS = {
        'default': {
            'start_row': 15,
            'columns': {
                'number': 2,      # Номер позиции
                'article': 4,     # Артикул
                'name': 9,        # Наименование
                'quantity': 32,   # Количество
                'unit': 35,       # Единица измерения
            },
            'sheet_name': 0,
        },
        'alternative': {
            'start_row': 1,
            'columns': {
                'number': 0,
                'article': 1,
                'name': 2,
                'quantity': 3,
                'unit': 4,
            },
            'sheet_name': 0,
        }
    }
    
    def __init__(self, config=None):
        """Инициализация парсера"""
        self.config = config
        if config is None:
            self.config = self.FORMATS['default']
        logger.info(f"Инициализирован InvoiceParser с конфигом: {self.config}")
    
    def parse_invoice(self, file_path: str, nomenclature=None) -> List[Dict[str, Any]]:
        """
        Парсит накладную и возвращает список позиций с найденными артикулами
        
        Args:
            file_path: Путь к файлу Excel
            nomenclature: Объект NomenclatureCSV для поиска правильных артикулов
            
        Returns:
            Список словарей с позициями
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                logger.error(f"Файл не найден: {file_path}")
                return []
            
            logger.info(f"Парсинг файла: {file_path.name}")
            logger.info(f"Используется конфиг: {self.config}")
            
            # Читаем Excel файл
            df = self._read_excel_file(file_path)
            
            if df is None or df.empty:
                logger.warning("Файл пуст или не может быть прочитан")
                return []
            
            logger.info(f"DataFrame размер: {df.shape}")
            
            # Извлекаем позиции
            raw_positions = self._extract_positions(df)
            logger.info(f"Извлечено сырых позиций: {len(raw_positions)}")
            
            if not raw_positions:
                logger.warning("Не найдено позиций в файле")
                return []
            
            # Ищем правильные артикулы если есть база номенклатуры
            positions = []
            for pos in raw_positions:
                article_found = pos['article_source']
                name_found = pos['name_source']
                found_in_db = False
                
                if nomenclature and hasattr(nomenclature, 'find_article_for_invoice_position'):
                    logger.debug(f"Поиск артикула в базе: '{pos['article_source']}'")
                    correct_article, correct_name, found = nomenclature.find_article_for_invoice_position(
                        pos['article_source'],
                        pos['name_source']
                    )
                    
                    if found:
                        article_found = correct_article
                        name_found = correct_name
                        found_in_db = True
                        logger.debug(f"Найден в базе: {article_found} - {name_found[:50]}")
                
                positions.append({
                    **pos,
                    'article_found': article_found,
                    'name_found': name_found,
                    'found_in_db': found_in_db
                })
            
            logger.info(f"Итоговое количество позиций: {len(positions)}")
            return positions
            
        except Exception as e:
            logger.error(f"Ошибка парсинга {file_path}: {e}")
            traceback.print_exc()
            return []
    
    def _read_excel_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Читает Excel файл с поддержкой разных форматов"""
        file_ext = file_path.suffix.lower()
        
        try:
            logger.debug(f"Чтение файла {file_path} с расширением {file_ext}")
            
            sheet_name = self.config.get('sheet_name', 0)
            
            if file_ext == '.xlsx' or file_ext == '.xlsm':
                try:
                    df = pd.read_excel(
                        file_path,
                        engine='openpyxl',
                        header=None,
                        sheet_name=sheet_name
                    )
                except Exception as e:
                    if "no default style" in str(e).lower():
                        raise Exception("Файл Excel повреждён или имеет нестандартную структуру. Попробуйте открыть и сохранить его заново в Excel.")
                    else:
                        raise
            elif file_ext == '.xls':
                try:
                    df = pd.read_excel(
                        file_path,
                        engine='xlrd',
                        header=None,
                        sheet_name=sheet_name
                    )
                except Exception as e:
                    logger.warning(f"Не удалось прочитать xls через xlrd: {e}, пробуем openpyxl")
                    df = pd.read_excel(
                        file_path,
                        engine='openpyxl',
                        header=None,
                        sheet_name=sheet_name
                    )
            else:
                logger.error(f"Неподдерживаемый формат файла: {file_ext}")
                return None
            
            logger.debug(f"Файл прочитан, размер: {df.shape}")
            return df
            
        except Exception as e:
            logger.error(f"Ошибка чтения файла {file_path}: {e}")
            traceback.print_exc()
            return None
    
    def _extract_positions(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Извлекает позиции из DataFrame"""
        positions = []
        
        # Безопасно получаем конфигурацию
        start_row = self.config.get('start_row', 15)
        columns = self.config.get('columns', self.FORMATS['default']['columns'])
        
        start_row_idx = max(0, start_row - 1)  # Конвертируем в 0-based индекс
        
        logger.debug(f"Начальная строка: {start_row} (индекс: {start_row_idx})")
        logger.debug(f"Колонки: {columns}")
        
        for i in range(start_row_idx, len(df)):
            pos_number = self._get_cell_value(df, i, columns.get('number', 2))
            article = self._get_cell_value(df, i, columns.get('article', 4))
            name = self._get_cell_value(df, i, columns.get('name', 9))
            quantity = self._get_cell_value(df, i, columns.get('quantity', 32))
            unit = self._get_cell_value(df, i, columns.get('unit', 35))
            
            pos_number = self._clean_value(pos_number)
            article = self._clean_value(article)
            name = self._clean_value(name)
            quantity = self._clean_value(quantity, is_quantity=True)
            unit = self._clean_value(unit) or "шт"
            
            # Проверяем конец таблицы
            if not any([pos_number, article, name, quantity]):
                if i + 3 < len(df):
                    next_has_data = False
                    for j in range(1, 4):
                        next_article = self._clean_value(
                            self._get_cell_value(df, i + j, columns.get('article', 4))
                        )
                        next_name = self._clean_value(
                            self._get_cell_value(df, i + j, columns.get('name', 9))
                        )
                        if next_article or next_name:
                            next_has_data = True
                            break
                    
                    if not next_has_data:
                        logger.debug(f"Конец таблицы на строке {i+1}")
                        break
            
            # Добавляем позицию если есть данные
            if article or name:
                positions.append({
                    'position_number': pos_number,
                    'article_source': article,
                    'name_source': name,
                    'quantity': quantity,
                    'unit': unit,
                    'row_index': i + 1,
                })
                logger.debug(f"Добавлена позиция {len(positions)}: {article} - {name[:30]}")
        
        logger.info(f"Извлечено {len(positions)} позиций")
        return positions
    
    def _get_cell_value(self, df: pd.DataFrame, row: int, col: int) -> Any:
        """Безопасно получает значение ячейки"""
        try:
            col_idx = col - 1 if col > 0 else 0
            
            if 0 <= row < len(df) and 0 <= col_idx < len(df.columns):
                value = df.iat[row, col_idx]
                
                if pd.isna(value):
                    return None
                
                return value
            return None
        except Exception as e:
            logger.debug(f"Ошибка получения ячейки [{row},{col}]: {e}")
            return None
    
    def _clean_value(self, value: Any, is_quantity: bool = False) -> str:
        """Очищает значение от лишних символов"""
        if value is None or pd.isna(value):
            return ""
        
        result = str(value).strip()
        
        if result.startswith('"') and result.endswith('"'):
            result = result[1:-1]
        
        result = result.replace('\n', ' ').replace('\r', ' ')
        result = re.sub(r'\s+', ' ', result).strip()
        
        # Для артикулов берем часть до слэша (нормализация)
        if not is_quantity and '/' in result:
            parts = [part.strip() for part in result.split('/') if part.strip()]
            if parts:
                result = parts[0]
        
        # Для количества форматируем число
        if is_quantity and result:
            try:
                match = re.search(r'[\d.,]+', result)
                if match:
                    num_str = match.group().replace(',', '.')
                    num = float(num_str)
                    
                    if num.is_integer():
                        result = str(int(num))
                    else:
                        result = f"{num:.3f}".rstrip('0').rstrip('.')
            except:
                pass
        
        return result
    
    def extract_invoice_info(self, file_path: str) -> Dict[str, str]:
        """Извлекает информацию о накладной из имени файла"""
        info = {
            'file_name': Path(file_path).name,
            'invoice_number': '',
            'invoice_date': '',
            'supplier': '',
            'receiver': 'ООО "ФРАНКО"',
            'total_positions': 0,
        }
        
        try:
            file_name = Path(file_path).stem
            
            # Ищем номер накладной
            for pattern in [r'№_?(\d+)', r'_(\d+)_', r'^(\d+)_']:
                match = re.search(pattern, file_name, re.IGNORECASE)
                if match:
                    info['invoice_number'] = match.group(1)
                    break
            
            # Ищем дату
            date_patterns = [
                r'(\d{1,2})[_\s.-](\d{1,2})[_\s.-](\d{2,4})',
                r'(\d{4})[_\s.-](\d{1,2})[_\s.-](\d{1,2})',
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, file_name)
                if match:
                    if len(match.group(3)) == 4:
                        year, month, day = match.groups()
                    else:
                        day, month, year = match.groups()
                        if len(year) == 2:
                            year = f"20{year}"
                    
                    info['invoice_date'] = f"{day}.{month}.{year}"
                    break
            
        except Exception as e:
            logger.warning(f"Не удалось извлечь информацию из имени файла: {e}")
        
        return info
    
    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """Проверяет, является ли файл валидной накладной"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return False, "Файл не существует"
            
            if file_path.suffix.lower() not in ['.xls', '.xlsx', '.xlsm']:
                return False, "Неверный формат файла. Поддерживаются: .xls, .xlsx, .xlsm"
            
            df = self._read_excel_file(file_path)
            
            if df is None or df.empty:
                return False, "Не удалось прочитать файл или файл пуст"
            
            positions = self._extract_positions(df)
            
            if not positions:
                return False, "В файле не найдены позиции для обработки"
            
            return True, f"Файл валиден. Найдено позиций: {len(positions)}"
            
        except Exception as e:
            return False, f"Ошибка проверки файла: {str(e)}"
    
    def test_parse(self, file_path: str) -> List[Dict[str, Any]]:
        """Тестовый парсинг без использования номенклатуры"""
        try:
            file_path = Path(file_path)
            logger.info(f"Тестовый парсинг файла: {file_path.name}")
            
            df = self._read_excel_file(file_path)
            
            if df is None or df.empty:
                logger.warning("Файл пуст или не может быть прочитан")
                return []
            
            positions = self._extract_positions(df)
            logger.info(f"Тестовый парсинг: найдено {len(positions)} позиций")
            return positions
            
        except Exception as e:
            logger.error(f"Ошибка тестового парсинга: {e}")
            return []