# --- services/interfaces/__init__.py ---
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Any
from libs.domain_models import Product, Address
class ISearchService(ABC):
	@abstractmethod
	def search_async(self,query:str,callback:Callable[[List[Product]],None])->None:pass
	@abstractmethod
	def get_product_by_id(self,product_id:int)->Optional[Product]:pass
class IProductRepository(ABC):
	@abstractmethod
	def update_field(self,product_id:int,field_name:str,value:Any)->bool:pass
	@abstractmethod
	def get_address_for_product(self,product_id:int)->Optional[Address]:pass
class IImageService(ABC):
	@abstractmethod
	def load_image_async(self,url:str,callback:Callable[[Optional[Any]],None])->None:pass
	@abstractmethod
	def get_placeholder(self)->Any:pass
class IPrinterService(ABC):
	@abstractmethod
	def generate_sticker(self,product:Product,preset:dict)->Any:pass
	@abstractmethod
	def print_sticker(self,image:Any,copies:int=1)->bool:pass
	@abstractmethod
	def print_queue(self,products:List[Product],one_by_one:bool=False)->bool:pass
class ISettingsService(ABC):
	@abstractmethod
	def get_setting(self,key:str,default:Any=None)->Any:pass
	@abstractmethod
	def set_setting(self,key:str,value:Any)->None:pass
	@abstractmethod
	def get_column_config(self)->dict:pass
	@abstractmethod
	def set_column_config(self,config:dict)->None:pass
class IInventoryService(ABC):
	@abstractmethod
	def import_inventory(self,file_path:str)->bool:pass
	@abstractmethod
	def export_report(self,file_path:str)->bool:pass
	@abstractmethod
	def start_scanning(self)->None:pass
	@abstractmethod
	def stop_scanning(self)->None:pass