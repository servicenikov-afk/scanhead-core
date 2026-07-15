# --- gui/services/product_details_service.py ---
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
import threading
from typing import Optional, Callable, List, Dict, Any
import logging
from libs.domain_models import Product
from gui.services.adapters.nomenclature_adapter import NomenclatureAdapter
from gui.services.adapters.store_adapter import StoreAdapter
from gui.services.adapters.css_export_adapter import CssExportAdapter
logger=logging.getLogger(__name__)
class ProductDetailsService:
	def __init__(self,root:Any,nomenclature_adapter:NomenclatureAdapter,store_adapter:StoreAdapter,css_adapter:CssExportAdapter):
		self._root=root
		self._nomenclature=nomenclature_adapter
		self._store=store_adapter
		self._css=css_adapter
		logger.info("[ProductDetailsService] Сервис инициализирован")
	def get_product_details(self,article:str,callback:Optional[Callable[[Optional[Product]],None]]=None)->Optional[Product]:
		def _fetch_thread():
			try:
				product=self._fetch_all_data(article)
				if callback:
					self._root.after(0,lambda:callback(product))
				return product
			except Exception as e:
				logger.error(f"[ProductDetailsService] Ошибка получения данных: {e}",exc_info=True)
				if callback:
					self._root.after(0,lambda:callback(None))
				return None
		if callback:
			thread=threading.Thread(target=_fetch_thread,daemon=True)
			thread.start()
		else:return _fetch_thread()
	def _fetch_all_data(self,article:str)->Optional[Product]:
		logger.debug(f"[DEBUG_TEMP] ProductDetailsService._fetch_all_data для {article}")
		nom_data=self._get_nomenclature_data(article)
		if not nom_data:
			logger.warning(f"[ProductDetailsService] Товар {article} не найден в номенклатуре")
			return None
		logger.debug(f"[DEBUG_TEMP] Nomenclature data: {nom_data}")
		storage_locations=self._get_storage_locations(article)
		logger.debug(f"[DEBUG_TEMP] Storage locations для {article}: {storage_locations} (кол-во: {len(storage_locations)})")
		manufacturer_info=self._get_manufacturer_info(article)
		logger.debug(f"[DEBUG_TEMP] Manufacturer info для {article}: {len(manufacturer_info)} записей")
		product=Product(
			article=nom_data['article'],
			name=nom_data['name'],
			barcodes=nom_data.get('barcodes',[]),
			address=storage_locations[0] if storage_locations else None,
			unit=nom_data.get('unit'),
			description=nom_data.get('description'),
			category=manufacturer_info[0].get('category1') if manufacturer_info else None,
			manufacturer_info=manufacturer_info,
			storage_locations=storage_locations,
			models=list(set(item['product_model'] for item in manufacturer_info if item.get('product_model')))
		)
		logger.info(f"[DEBUG_TEMP] Продукт собран: article={product.article}, storage_locations={product.storage_locations}")
		return product
	def _get_nomenclature_data(self,article:str)->Optional[Dict[str,Any]]:
		try:
			products=self._nomenclature.search(article)
			if products:
				product=products[0]
				return{'article':product.article,'name':product.name,'barcodes':product.barcodes,'unit':getattr(product,'unit',None),'description':getattr(product,'description',None)}
			conn=self._nomenclature._get_connection()
			cursor=conn.cursor()
			cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
			table_row=cursor.fetchone()
			if not table_row:return None
			table_name=table_row['name']
			cursor.execute(f"SELECT article,name,barcodes,unit FROM {table_name} WHERE article=? OR JSON_EXTRACT(barcodes,'$') LIKE ?",(article,f'%{article}%'))
			row=cursor.fetchone()
			if row:
				import json
				barcodes_raw=row['barcodes']
				barcodes=json.loads(barcodes_raw) if barcodes_raw else []
				return{'article':row['article'],'name':row['name'],'barcodes':barcodes,'unit':row['unit'],'description':None}
			return None
		except Exception as e:
			logger.error(f"[ProductDetailsService] Ошибка чтения nomenclature: {e}")
			return None
	def _get_storage_locations(self,article:str)->List[str]:
		try:
			locations=self._store.get_all_locations(article)
			logger.debug(f"[ProductDetailsService] Найдено {len(locations)} адресов для {article}")
			return locations
		except Exception as e:
			logger.error(f"[ProductDetailsService] Ошибка чтения store: {e}")
			return []
	def _get_manufacturer_info(self,article:str)->List[Dict[str,Any]]:
		try:
			info=self._css.get_by_article(article)
			logger.debug(f"[ProductDetailsService] Найдено {len(info)} записей производителя для {article}")
			return info
		except Exception as e:
			logger.error(f"[ProductDetailsService] Ошибка чтения css_export: {e}")
			return []
	def get_enriched_product_sync(self,article:str)->Optional[Product]:
		return self.get_product_details(article,callback=None)