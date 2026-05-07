# exporters/excel_exporter.py (обновленный)
import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ExcelExporter:
    """Экспорт данных в Excel"""
    
    @staticmethod
    def export(data: List[Dict[str, Any]], filepath: Path) -> bool:
        """Экспортирует данные в Excel с форматированием чисел"""
        try:
            df = pd.DataFrame(data)
            
            # Форматируем числовые колонки
            for col in df.columns:
                if 'остаток' in col.lower() or 'разница' in col.lower() or 'количество' in col.lower():
                    df[col] = df[col].apply(lambda x: f"{x:.3f}".rstrip('0').rstrip('.') if isinstance(x, (int, float)) else x)
            
            df.to_excel(filepath, index=False, engine='openpyxl')
            logger.info(f"Экспортировано в Excel: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Ошибка экспорта в Excel: {e}")
            return False