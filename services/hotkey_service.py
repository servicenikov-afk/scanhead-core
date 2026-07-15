# --- services/hotkey_service.py ---
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
import logging
from typing import Dict, Callable, Any
from services.interfaces import IHotkeyService, ISettingsService
logger=logging.getLogger(__name__)
DEFAULT_HOTKEYS={
	'open_settings':'F10',
	'show_product_info':'F1',
	'add_to_queue':'Control-Return',
	'next_preset':'Control-plus',
	'open_preset_editor':'F12',
	'print_queue':'Control-p',
}
class HotkeyService(IHotkeyService):
	def __init__(self,settings_service:ISettingsService):
		self._settings_service=settings_service
		self._hotkeys=self._load_hotkeys()
		logger.info(f"[HotkeyService] Инициализация с {len(self._hotkeys)} горячими клавишами")
	def _load_hotkeys(self)->Dict[str,str]:
		saved=self._settings_service.get_setting('hotkeys',{})
		hotkeys=DEFAULT_HOTKEYS.copy()
		hotkeys.update(saved)
		return hotkeys
	def get_hotkey(self,action:str)->str:
		return self._hotkeys.get(action,DEFAULT_HOTKEYS.get(action,''))
	def set_hotkey(self,action:str,hotkey:str)->None:
		self._hotkeys[action]=hotkey
		self._settings_service.set_setting('hotkeys',self._hotkeys)
		logger.info(f"[HotkeyService] Установлена горячая клавиша: {action} = {hotkey}")
	def get_all_hotkeys(self)->Dict[str,str]:
		return self._hotkeys.copy()
	def bind_hotkey(self,widget:Any,action:str,callback:Callable)->None:
		hotkey=self.get_hotkey(action)
		if hotkey:
			widget.bind(f'<{hotkey}>',lambda e:callback())
			logger.debug(f"[HotkeyService] Привязана горячая клавиша: {hotkey} → {action}")
	def unbind_hotkey(self,widget:Any,action:str)->None:
		hotkey=self.get_hotkey(action)
		if hotkey:
			widget.unbind(f'<{hotkey}>')
			logger.debug(f"[HotkeyService] Отвязана горячая клавиша: {hotkey}")