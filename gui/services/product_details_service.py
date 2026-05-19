"""Сервис агрегации детальной информации о товаре из трёх источников."""
import threading
from typing import Optional, Callable, List, Dict, Any
import logging

from libs.domain_models import Product
from gui.services.adapters.nomenclature_adapter import NomenclatureAdapter
from gui.services.adapters.store_adapter import StoreAdapter
from gui.services.adapters.css_export_adapter import CssExportAdapter

logger = logging.getLogger(__name__)


class ProductDetailsService:
    """
    Сервис для получения полной информации о товаре из трёх баз данных.
    
    Агрегирует данные из:
    - nomenclature.db (основная номенклатура, русские названия)
    - store.db (адреса хранения на складе)
    - css_export.db (запчасти Franke, модели оборудования)
    """
    
    def __init__(
        self,
        nomenclature_adapter: NomenclatureAdapter,
        store_adapter: StoreAdapter,
        css_adapter: CssExportAdapter
    ):
        self._nomenclature = nomenclature_adapter
        self._store = store_adapter
        self._css = css_adapter
        logger.info("[ProductDetailsService] Сервис инициализирован")
    
    def get_product_details(
        self, 
        article: str,
        callback: Optional[Callable[[Optional[Product]], None]] = None
    ) -> Optional[Product]:
        """
        Получить детальную информацию о товаре по артикулу.
        
        :param article: Артикул товара для поиска
        :param callback: Опциональный callback для асинхронного результата
        :return: Product с заполненными полями или None
        """
        def _fetch_thread():
            try:
                product = self._fetch_all_data(article)
                if callback:
                    callback(product)
                return product
            except Exception as e:
                logger.error(f"[ProductDetailsService] Ошибка получения данных: {e}")
                if callback:
                    callback(None)
                return None
        
        if callback:
            # Асинхронный режим
            thread = threading.Thread(target=_fetch_thread, daemon=True)
            thread.start()
        else:
            # Синхронный режим
            return _fetch_thread()
    
    def _fetch_all_data(self, article: str) -> Optional[Product]:
        """Собрать все данные о товаре из трёх источников."""
        logger.debug(f"[ProductDetailsService] Запрос данных для {article}")
        
        # 1. Получаем данные из nomenclature.db (основные)
        nom_data = self._get_nomenclature_data(article)
        if not nom_data:
            logger.warning(f"[ProductDetailsService] Товар {article} не найден в номенклатуре")
            return None
        
        # 2. Получаем адреса хранения из store.db
        storage_locations = self._get_storage_locations(article)
        
        # 3. Получаем информацию от производителя из css_export.db
        manufacturer_info = self._get_manufacturer_info(article)
        
        # Собираем всё в единую модель
        product = Product(
            article=nom_data['article'],
            name=nom_data['name'],
            barcodes=nom_data.get('barcodes', []),
            address=storage_locations[0] if storage_locations else None,
            unit=nom_data.get('unit'),
            description=nom_data.get('description'),
            category=manufacturer_info[0].get('category1') if manufacturer_info else None,
            manufacturer_info=manufacturer_info,
            storage_locations=storage_locations,
            models=list(set(item['product_model'] for item in manufacturer_info if item.get('product_model')))
        )
        
        logger.info(f"[ProductDetailsService] Данные для {article} собраны: "
                   f"{len(storage_locations)} адресов, {len(manufacturer_info)} записей производителя")
        return product
    
    def _get_nomenclature_data(self, article: str) -> Optional[Dict[str, Any]]:
        """Получить данные из nomenclature.db."""
        try:
            # Используем поиск по артикулу через адаптер
            products = self._nomenclature.search(article)
            if products:
                product = products[0]
                return {
                    'article': product.article,
                    'name': product.name,
                    'barcodes': product.barcodes,
                    'unit': getattr(product, 'unit', None),
                    'description': getattr(product, 'description', None)
                }
            
            # Если не найдено через search, пробуем прямой запрос
            conn = self._nomenclature._get_connection()
            cursor = conn.cursor()
            
            # Динамически определяем имя таблицы
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
            table_row = cursor.fetchone()
            if not table_row:
                return None
            table_name = table_row['name']
            
            # Ищем по canonical_article или в alternative_articles
            cursor.execute(f"""
                SELECT canonical_article, name_ru, alternative_articles, unit
                FROM {table_name}
                WHERE canonical_article = ?
                OR JSON_EXTRACT(alternative_articles, '$') LIKE ?
            """, (article, f'%{article}%'))
            
            row = cursor.fetchone()
            if row:
                import json
                alt_articles_raw = row['alternative_articles']
                alt_articles = json.loads(alt_articles_raw) if alt_articles_raw else []
                
                return {
                    'article': row['canonical_article'],
                    'name': row['name_ru'],
                    'barcodes': alt_articles,
                    'unit': row['unit'],
                    'description': None  # В nomenclature.db нет поля description
                }
            
            return None
        except Exception as e:
            logger.error(f"[ProductDetailsService] Ошибка чтения nomenclature: {e}")
            return None
    
    def _get_storage_locations(self, article: str) -> List[str]:
        """Получить все адреса хранения из store.db."""
        try:
            locations = self._store.get_all_locations(article)
            logger.debug(f"[ProductDetailsService] Найдено {len(locations)} адресов для {article}")
            return locations
        except Exception as e:
            logger.error(f"[ProductDetailsService] Ошибка чтения store: {e}")
            return []
    
    def _get_manufacturer_info(self, article: str) -> List[Dict[str, Any]]:
        """Получить информацию от производителя из css_export.db."""
        try:
            info = self._css.get_by_article(article)
            logger.debug(f"[ProductDetailsService] Найдено {len(info)} записей производителя для {article}")
            return info
        except Exception as e:
            logger.error(f"[ProductDetailsService] Ошибка чтения css_export: {e}")
            return []
    
    def get_enriched_product_sync(self, article: str) -> Optional[Product]:
        """Синхронная версия получения данных (для использования в диалогах)."""
        return self.get_product_details(article, callback=None)
