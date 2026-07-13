#--- services/config_manager_adapter.py ---
#⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
import logging
from pathlib import Path
from typing import Any, Optional
from services.interfaces import ISettingsService
from libs.config_manager import ConfigManager
logger=logging.getLogger(__name__)
class ConfigManagerSettingsAdapter(ISettingsService):
	def __init__(self,config_path:Optional[str]=None):
		if config_path is None:config_path=str(Path(__file__).parent.parent/"config"/"app_config.json")
		Path(config_path).parent.mkdir(parents=True,exist_ok=True)
		default_config={'theme':'Dark','language':'ru','columns_visible':['article','article2','name','address'],'columns_order':['article','article2','name','address'],'search_font_size':18,'search_autofocus':True,'search_autofocus_delay':1.0,'search_autoclear_enabled':True,'search_autoclear_delay':3.0,'address_format':{'enabled':True,'separator':'-','custom_separator':'','levels':['Блок','Стеллаж','Секция','Ряд','Ячейка'],'display_mode':'with_labels'},'sticker_presets':{'default':{'sticker':{'width_mm':58,'height_mm':35,'orientation':'portrait','background_color':'#FFFFFF','border':True,'dpi':300},'fonts':{'name_size':7,'article_size':8,'address_size':6},'layout':{'show_barcode':True,'show_qr':False,'article_position':'top','show_address':True,'address_position':'bottom'},'article':{'enabled':True,'size':8,'align':'center','bold':True,'offset_x':0,'offset_y':15},'name':{'enabled':True,'size':7,'align':'center','max_lines':5,'bold':False,'italic':False,'offset_x':0,'offset_y':20},'address':{'enabled':True,'size':6,'align':'right','bold':False,'italic':False,'offset_x':0,'offset_y':-165},'barcode':{'enabled':True,'type':'auto','position':'bottom','qr_size_mm':16,'code128_width_mm':56,'code128_height_mm':5,'show_text':True,'text_size':5,'offset_x':0,'offset_y':-25,'text_offset_x':0,'text_offset_y':-11,'text_scale_x':1.0,'text_scale_y':5.0}}},'current_preset_name':'default'}
		self._config=ConfigManager(config_path=config_path,default_config=default_config)
		logger.info(f"[ConfigManagerSettingsAdapter] Инициализация: {config_path}")
	def get_setting(self,key:str,default:Any=None)->Any:
		logger.debug(f"[ConfigManagerSettingsAdapter] get: {key}")
		return self._config.get(key,default)
	def set_setting(self,key:str,value:Any)->None:
		logger.debug(f"[ConfigManagerSettingsAdapter] set: {key}={value}")
		self._config.set(key,value)
	def get_column_config(self)->dict:
		return {'visible':self._config.get('columns_visible',[]),'order':self._config.get('columns_order',[])}
	def set_column_config(self,config:dict)->None:
		self._config.set('columns_visible',config.get('visible',[]))
		self._config.set('columns_order',config.get('order',[]))
	def save(self)->None:
		self._config.save()
		logger.info("[ConfigManagerSettingsAdapter] Конфигурация сохранена в файл")