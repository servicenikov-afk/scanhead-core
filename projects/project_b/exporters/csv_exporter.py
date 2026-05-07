# exporters/csv_exporter.py
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class CSVExporter:
    """Экспорт данных в CSV"""
    
    @staticmethod
    def export(data: List[Dict[str, Any]], filepath: Path) -> bool:
        """Экспортирует данные в CSV"""
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
            return False# csv exporter 
