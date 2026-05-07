# modules/database_manager.py
import logging
from typing import Dict, List, Tuple, Optional, Any
from .nomenclature import NomenclatureCSV
logger = logging.getLogger(__name__)
class DatabaseManager:
    def __init__(self, config):
        self.config = config
        self.nomenclature = NomenclatureCSV(config.get('paths.csv_path'))
    def download_database(self) -> bool:
        try:
            url = self.config.get('paths.database_url')
            path = self.config.get('paths.csv_path')
            if not url:
                return False
            ok = self.nomenclature.download_and_load(url, local_path=path)
            if ok:
                logger.info(f"CSV сохранена: {path}")
            return ok
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return False
    def load_database(self, force_download: bool = False) -> bool:
        try:
            url, path = self.config.get('paths.database_url'), self.config.get('paths.csv_path')
            if force_download or not path:
                return self.download_database()
            if self.nomenclature.load_from_file(path):
                logger.info(f"Загружено записей: {len(self.nomenclature.data)}")
                return True
            return self.download_database()
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return False
    def find_article(self, article: str, name: str = None) -> Tuple[str, str, bool]:
        if not self.nomenclature.loaded:
            return str(article).strip(), str(name or article).strip(), False
        return self.nomenclature.find_article_for_invoice_position(article, name or "")
    def get_stats(self) -> Dict[str, Any]:
        if not self.nomenclature.loaded:
            return {'status': 'not_loaded', 'records': 0, 'columns': []}
        stats = self.nomenclature.get_stats()
        stats['columns'] = ['name', 'article_correct', 'barcodes']
        if self.nomenclature.data:
            stats['sample'] = [{'article': d[1], 'name': d[0][:50]} 
                             for d in self.nomenclature.data[:5]]
        return stats