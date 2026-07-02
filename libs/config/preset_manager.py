# --- libs/config/preset_manager.py ---
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
logger=logging.getLogger(__name__)
class PresetManager:
	DEFAULT_PRESET_NAME="Стандартный"
	def __init__(self,config_path:Optional[Path]=None):
		if config_path is None:
			app_data=Path.home()/"AppData"/"Local"/"StickerMakerV3"
			config_path=app_data/"presets.json"
		self.config_path=config_path
		self.presets:Dict[str,Dict[str,Any]]={}
		self.last_used:Optional[str]=None
		self.load()
	def load(self)->bool:
		if not self.config_path.exists():
			logger.info(f"Файл пресетов не найден, создаем дефолтный: {self.config_path}")
			self._create_default()
			return True
		try:
			data=json.loads(self.config_path.read_text(encoding='utf-8'))
			self.presets=data.get('presets',{})
			self.last_used=data.get('last_used')
			if not self.presets:self._create_default()
			logger.debug(f"Загружено {len(self.presets)} пресетов")
			return True
		except json.JSONDecodeError as e:
			logger.error(f"Ошибка парсинга файла пресетов: {e}")
			self._create_default()
			return False
		except Exception as e:
			logger.error(f"Ошибка загрузки пресетов: {e}")
			self._create_default()
			return False
	def save(self)->bool:
		try:
			self.config_path.parent.mkdir(parents=True,exist_ok=True)
			data={'presets':self.presets,'last_used':self.last_used}
			self.config_path.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
			logger.debug("Пресеты сохранены")
			return True
		except Exception as e:
			logger.error(f"Ошибка сохранения пресетов: {e}")
			return False
	def _create_default(self):
		self.presets={self.DEFAULT_PRESET_NAME:{"sticker.width_mm":40,"sticker.height_mm":20,"sticker.dpi":300,"sticker.border":False,"fonts.name_size":10,"fonts.article_size":12,"fonts.address_size":8,"layout.show_barcode":True,"layout.show_qr":False,"layout.show_address":True,"layout.article_position":"top","layout.address_position":"bottom","layout.quantity_position":"top_right"}}
		self.last_used=self.DEFAULT_PRESET_NAME
	def get_preset(self,name:str)->Optional[Dict[str,Any]]:
		return self.presets.get(name)
	def set_preset(self,name:str,settings:Dict[str,Any])->bool:
		self.presets[name]=settings
		self.last_used=name
		return self.save()
	def delete_preset(self,name:str)->bool:
		if name not in self.presets:return False
		if len(self.presets)<=1:
			logger.warning("Нельзя удалить последний пресет")
			return False
		del self.presets[name]
		if self.last_used==name:self.last_used=next(iter(self.presets.keys()))
		return self.save()
	def list_presets(self)->List[str]:
		return list(self.presets.keys())
	def get_last_used(self)->Optional[str]:
		return self.last_used
	def set_last_used(self,name:str):
		if name in self.presets:
			self.last_used=name
			self.save()