"""Excel Exporter - Экспорт данных в Excel

Модуль предоставляет функциональность для экспорта данных в формат Excel
с автоматическим форматированием числовых колонок.
"""

import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Any


logger = logging.getLogger(__name__)


class ExcelExporter:
    """Экспорт данных в Excel
    
    Предоставляет методы для экспорта списка словарей в Excel файл
    с автоматическим форматированием числовых значений.
    """
    
    @staticmethod
    def export(data: List[Dict[str, Any]], filepath: Path) -> bool:
        """Экспортирует данные в Excel с форматированием чисел
        
        Args:
            data: Список словарей с данными для экспорта
            filepath: Путь к файлу для сохранения
            
        Returns:
            True если экспорт успешен, False иначе
        """
        try:
            df = pd.DataFrame(data)
            
            # Форматируем числовые колонки
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ['остаток', 'разница', 'количество']):
                    df[col] = df[col].apply(
                        lambda x: f"{x:.3f}".rstrip('0').rstrip('.') 
                        if isinstance(x, (int, float)) else x
                    )
            
            df.to_excel(filepath, index=False, engine='openpyxl')
            logger.info(f"Экспортировано в Excel: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка экспорта в Excel: {e}")
            return False
