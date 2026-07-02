# --- services/stubs/__init__.py ---
# Stub service - verify existing implementations and remove stubs when no longer needed
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
import logging
from typing import Callable, List, Optional, Any
from PIL import Image
from libs.domain_models import Product, Address, InventoryItem
from services.interfaces import ISearchService, IProductRepository, IImageService, IPrinterService, ISettingsService, IInventoryService
logger=logging.getLogger(__name__)
class StubSearchService(ISearchService):
	def __init__(self):
		self._test_products=[
			Product(article="ART001",name="Тестовый товар 1",barcodes=["4600000000001","4600000000002"],address="A01 — Стеллаж 1, Полка A",storage_locations=["A01 — Стеллаж 1, Полка A"]),
			Product(article="ART002",name="Тестовый товар 2",barcodes=["4600000000003"],address="B02 — Стеллаж 2, Полка B",storage_locations=["B02 — Стеллаж 2, Полка B"])
		]
	def search_async(self,query:str,callback:Callable[[List[Product]],None])->None:
		logger.info(f"[StubSearchService] Поиск по запросу: '{query}'")
		import threading,time
		def worker():
			time.sleep(0.1)
			results=[p for p in self._test_products if query.lower() in p.article.lower() or query.lower() in p.name.lower()]
			callback(results)
		threading.Thread(target=worker,daemon=True).start()
	def get_product_by_id(self,product_id:int)->Optional[Product]:
		logger.info(f"[StubSearchService] Получение товара по ID: {product_id}")
		for product in self._test_products:
			if product.id==product_id:return product
		return None
class StubProductRepository(IProductRepository):
	def update_field(self,product_id:int,field_name:str,value:Any)->bool:
		logger.info(f"[StubProductRepository] Обновление поля {field_name}={value} для товара {product_id}")
		return True
	def get_address_for_product(self,product_id:int)->Optional[Address]:
		logger.info(f"[StubProductRepository] Получение адреса для товара {product_id}")
		return Address(code="TEST01",description="Тестовый адрес хранения")
class StubImageService(IImageService):
	def load_image_async(self,url:str,callback:Callable[[Optional[Any]],None])->None:
		logger.info(f"[StubImageService] Загрузка изображения из {url}")
		callback(None)
	def get_placeholder(self)->Any:
		logger.info("[StubImageService] Получение заглушки изображения")
		return Image.new('RGB',(200,200),color='#808080')
class StubPrinterService(IPrinterService):
	def generate_sticker(self,product:Product,preset:dict)->Any:
		logger.info(f"[StubPrinterService] Генерация стикера для товара {product.article}")
		return Image.new('RGB',(400,300),color='white')
	def print_sticker(self,image:Any,copies:int=1)->bool:
		logger.info(f"[StubPrinterService] Печать стикера, копий: {copies}")
		return True
	def print_queue(self,products:List[Product],one_by_one:bool=False)->bool:
		logger.info(f"[StubPrinterService] Печать очереди, товаров: {len(products)}, по одному: {one_by_one}")
		return True
class StubSettingsService(ISettingsService):
	def __init__(self):
		self._settings={'theme':'Dark','language':'ru','columns_visible':['article','article2','name','address'],'columns_order':['article','article2','name','address'],'address_format':{'enabled':True,'separator':'-','custom_separator':'','levels':['Блок','Стеллаж','Секция','Ряд','Ячейка'],'display_mode':'with_labels'}}
	def get_setting(self,key:str,default:Any=None)->Any:
		logger.debug(f"[StubSettingsService] Получение настройки: {key}")
		return self._settings.get(key,default)
	def set_setting(self,key:str,value:Any)->None:
		logger.debug(f"[StubSettingsService] Сохранение настройки: {key}={value}")
		self._settings[key]=value
	def get_column_config(self)->dict:
		return{'visible':self._settings.get('columns_visible',[]),'order':self._settings.get('columns_order',[])}
	def set_column_config(self,config:dict)->None:
		self._settings['columns_visible']=config.get('visible',[])
		self._settings['columns_order']=config.get('order',[])
class StubInventoryService(IInventoryService):
	def import_inventory(self,file_path:str)->bool:
		logger.info(f"[StubInventoryService] Импорт инвентаризации из {file_path}")
		return True
	def export_report(self,file_path:str)->bool:
		logger.info(f"[StubInventoryService] Экспорт отчёта в {file_path}")
		return True
	def start_scanning(self)->None:
		logger.info("[StubInventoryService] Запуск сканирования")
	def stop_scanning(self)->None:
		logger.info("[StubInventoryService] Остановка сканирования")