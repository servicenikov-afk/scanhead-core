"""CSV Exporter - Экспорт данных в CSV

Модуль предоставляет функциональность для экспорта данных в формат CSV
с кодировкой UTF-8 с BOM для корректного отображения кириллицы в Excel.
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Any


logger = logging.getLogger(__name__)


class CSVExporter:
    """Экспорт данных в CSV
    
    Предоставляет методы для экспорта списка словарей в CSV файл
    с кодировкой UTF-8 с BOM.
    """
    
    @staticmethod
    def export(data: List[Dict[str, Any]], filepath: Path) -> bool:
        """Экспортирует данные в CSV
        
        Args:
            data: Список словарей с данными для экспорта
            filepath: Путь к файлу для сохранения
            
        Returns:
            True если экспорт успешен, False иначе
        """
        try:
            if not data:
                return False
            
            with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"Экспортировано в CSV: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка экспорта в CSV: {e}")
            return False
