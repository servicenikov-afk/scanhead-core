# --- gui/main_window.py ---
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
import logging
from typing import Any
import os
import customtkinter as ctk
from PIL import Image
from gui.tabs.search_address_tab import SearchAddressTab
from gui.tabs.inventory_tab import InventoryTab
from gui.dialogs.settings_dialog import SettingsDialog
from services.di_container import DIContainer
from services.interfaces import ISearchService, ISettingsService, IHotkeyService
logger=logging.getLogger(__name__)
class MainWindow(ctk.CTkFrame):
	def __init__(self,master:Any,di_container:DIContainer):
		super().__init__(master)
		self._container=di_container
		self._search_service=self._container.get(ISearchService)
		self._settings_service=self._container.get(ISettingsService)
		self._hotkey_service=self._container.get(IHotkeyService)
		logger.info("[MainWindow] Инициализация главного окна")
		self._img_help=self._load_icon("help32.png",size=(20,20))
		self._img_settings=self._load_icon("settings32.png",size=(20,20))
		self._create_ui()
		self.after(100,self._maximize_window)
		self.after(300,self._bind_global_hotkeys)
		logger.info("[MainWindow] Главное окно инициализировано")
	def _maximize_window(self)->None:
		try:
			if hasattr(self.master,'state'):
				self.master.state('zoomed')
				logger.info("[MainWindow] Окно развёрнуто (Windows)")
		except Exception as e:
			logger.warning(f"[MainWindow] Не удалось развернуть окно через state(): {e}")
			try:
				self.master.attributes('-zoomed',True)
				logger.info("[MainWindow] Окно развёрнуто через attributes()")
			except Exception as e2:
				logger.warning(f"[MainWindow] Не удалось развернуть окно через attributes(): {e2}")
				try:
					screen_width=self.master.winfo_screenwidth()
					screen_height=self.master.winfo_screenheight()
					self.master.geometry(f"{screen_width}x{screen_height}+0+0")
					logger.info(f"[MainWindow] Окно развёрнуто вручную: {screen_width}x{screen_height}")
				except Exception as e3:
					logger.error(f"[MainWindow] Все способы разворачивания окна не сработали: {e3}")
	def _load_icon(self,filename:str,size:tuple=(20,20))->ctk.CTkImage|None:
		try:
			icons_dir=os.path.join(os.path.dirname(os.path.dirname(__file__)),"data","icons")
			img_path=os.path.join(icons_dir,filename)
			if os.path.exists(img_path):
				return ctk.CTkImage(light_image=Image.open(img_path),dark_image=Image.open(img_path),size=size)
		except Exception as e:
			logger.warning(f"[MainWindow] Не удалось загрузить {filename}: {e}")
		return None
	def _create_ui(self)->None:
		top_bar=ctk.CTkFrame(self,fg_color="transparent")
		top_bar.pack(side="top",fill="x",padx=2,pady=2)
		left_btns=ctk.CTkFrame(top_bar,fg_color="transparent")
		left_btns.pack(side="left")
		self._btn_help=ctk.CTkButton(left_btns,text="?",width=28,height=28,command=self._open_help)
		self._btn_help.pack(side="left",padx=2)
		self._btn_settings=ctk.CTkButton(left_btns,text="⚙",width=28,height=28,command=self._open_settings)
		self._btn_settings.pack(side="left",padx=2)
		self._notebook=ctk.CTkTabview(top_bar,height=36,corner_radius=8)
		self._notebook.pack(side="right")
		self._notebook.add("  🔍 Поиск | Адрес   ")
		self._notebook.add("  📋 Инвентаризация   ")
		self._content=ctk.CTkFrame(self,fg_color="transparent")
		self._content.pack(side="top",fill="both",expand=True,padx=2,pady=2)
		self._search_tab=SearchAddressTab(self._content,self._container)
		self._search_tab.pack(fill="both",expand=True)
		self._inventory_tab=InventoryTab(self._content,self._container)
		self._inventory_tab.pack_forget()
		self._notebook.configure(command=self._on_tab_change)
		logger.debug("[MainWindow] UI создан")
	def _on_tab_change(self)->None:
		selected=self._notebook.get()
		if "Поиск" in selected:
			self._search_tab.pack(fill="both",expand=True)
			self._inventory_tab.pack_forget()
		elif "Инвентаризация" in selected:
			self._inventory_tab.pack(fill="both",expand=True)
			self._search_tab.pack_forget()
		logger.debug(f"[MainWindow] Переключена вкладка: {selected}")
	def _on_search_result(self,products:list)->None:
		logger.info(f"[MainWindow] Получены результаты поиска: {len(products)} товаров")
		self._search_tab.update_products(products)
	def _open_settings(self)->None:
		logger.info("[MainWindow] Открытие настроек")
		dialog=SettingsDialog(self,settings_service=self._settings_service,on_settings_changed=self._on_setting_changed)
		dialog.grab_set()
	def _on_setting_changed(self,key:str,value:Any)->None:
		logger.info(f"[MainWindow] Изменена настройка {key}={value}")
		if hasattr(self,'_search_tab'):
			self._search_tab.on_setting_changed(key,value)
	def _open_help(self)->None:
		logger.info("[MainWindow] Открыта справка (заглушка)")
	def _bind_global_hotkeys(self)->None:
		if not self._hotkey_service:
			logger.warning("[MainWindow] HotkeyService не доступен")
			return
		root=self.winfo_toplevel()
		logger.info("[MainWindow] Привязка глобальных горячих клавиш к корневому окну")
		self._hotkey_service.bind_hotkey(root,'open_settings',self._open_settings)
		def show_product_info():
			if hasattr(self,'_search_tab') and hasattr(self._search_tab,'_product_details'):
				product=self._search_tab.get_current_product()
				if product and hasattr(self._search_tab._product_details,'_on_info_click'):
					self._search_tab._product_details._on_info_click()
		self._hotkey_service.bind_hotkey(root,'show_product_info',show_product_info)
		def add_to_queue():
			if hasattr(self,'_search_tab'):
				product=self._search_tab.get_current_product()
				if product and hasattr(self._search_tab,'_add_product_to_queue'):
					self._search_tab._add_product_to_queue(product)
		self._hotkey_service.bind_hotkey(root,'add_to_queue',add_to_queue)
		def print_queue():
			if hasattr(self,'_search_tab') and hasattr(self._search_tab,'_print_queue'):
				self._search_tab._print_queue._print_all()
		self._hotkey_service.bind_hotkey(root,'print_queue',print_queue)
		def open_preset_editor():
			if hasattr(self,'_search_tab') and hasattr(self._search_tab,'_sticker_preview'):
				if hasattr(self._search_tab._sticker_preview,'_on_open_editor'):
					self._search_tab._sticker_preview._on_open_editor()
		self._hotkey_service.bind_hotkey(root,'open_preset_editor',open_preset_editor)
		def next_preset():
			if hasattr(self,'_search_tab') and hasattr(self._search_tab,'_sticker_preview'):
				if hasattr(self._search_tab._sticker_preview,'_on_preset_change'):
					presets=self._search_tab._sticker_preview._get_preset_names()
					current=self._search_tab._sticker_preview._preset_combo.get()
					if current in presets:
						idx=presets.index(current)
						next_idx=(idx+1)%len(presets)
						self._search_tab._sticker_preview._on_preset_change(presets[next_idx])
		self._hotkey_service.bind_hotkey(root,'next_preset',next_preset)