# --- services/config_manager_adapter.py ---
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
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
		default_config={'theme':'Dark','language':'ru','columns_visible':['article','article2','name','address'],'columns_order':['article','article2','name','address'],'search_font_size':18,'search_autofocus':True,'search_autofocus_delay':1.0,'address_format':{'enabled':True,'separator':'-','custom_separator':'','levels':['Блок','Стеллаж','Секция','Ряд','Ячейка'],'display_mode':'with_labels'},'sticker_presets':{},'current_preset_name':'default'}
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