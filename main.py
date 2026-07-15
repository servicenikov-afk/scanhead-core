# --- main.py ---
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
import sys
import logging
import json
from pathlib import Path
CONFIG_PATH=Path(__file__).parent/"config"/"app_config.json"
def load_config()->dict:
	if CONFIG_PATH.exists():
		with open(CONFIG_PATH,"r",encoding="utf-8")as f:return json.load(f)
	return{"app_name":"ScanHead Combine","log_level":"INFO"}
config=load_config()
from libs.core import quick_bootstrap
quick_bootstrap(app_name=config.get("app_name","ScanHead Combine"),log_level=getattr(logging,config.get("log_level","DEBUG")))
logger=logging.getLogger(__name__)
def main()->None:
	logger.info("="*60)
	logger.info("ScanHead Combine - Запуск приложения")
	logger.info("="*60)
	try:import customtkinter as ctk
	except ImportError:
		logger.error("customtkinter не установлен. Выполните: pip install customtkinter")
		sys.exit(1)
	try:
		from PIL import ImageTk,Image
		PIL_AVAILABLE=True
	except ImportError:
		PIL_AVAILABLE=False
		logger.warning("PIL/Pillow не установлен. Изображения будут недоступны.")
	ctk.set_appearance_mode("System")
	ctk.set_default_color_theme("blue")
	from gui.main_window import MainWindow
	from services.di_container import DIContainer
	from services.interfaces import(ISearchService,IProductRepository,IImageService,ISettingsService,IPrinterService,IInventoryService,IHotkeyService)
	from services.stubs import StubImageService,StubInventoryService
	from services.config_manager_adapter import ConfigManagerSettingsAdapter
	from services.printer_service import RealPrinterService
	from services.hotkey_service import HotkeyService
	logger.info("[Main] Использование реальных баз данных")
	from gui.services.adapters.nomenclature_adapter import NomenclatureAdapter
	from gui.services.adapters.store_adapter import StoreAdapter
	from gui.services.adapters.css_export_adapter import CssExportAdapter
	from gui.services.product_details_service import ProductDetailsService
	db_path=config.get("db_paths",{}).get("nomenclature","data/databases/nomenclature/nomenclature.db")
	nomenclature_adapter=NomenclatureAdapter(db_path)
	store_db_path=config.get("db_paths",{}).get("store","data/databases/store/store.db")
	store_adapter=StoreAdapter(store_db_path)
	css_db_path=config.get("db_paths",{}).get("css_export","data/databases/css_export/css_export.db")
	css_adapter=CssExportAdapter(css_db_path)
	root=ctk.CTk()
	root.title("ScanHead Combine")
	root.state('zoomed')
	details_service=ProductDetailsService(root=root,nomenclature_adapter=nomenclature_adapter,store_adapter=store_adapter,css_adapter=css_adapter)
	container=DIContainer()
	container.register(ISearchService,nomenclature_adapter)
	container.register(IProductRepository,store_adapter)
	container.register("product_details_service",details_service)
	container.register(IImageService,StubImageService())
	settings_service=ConfigManagerSettingsAdapter()
	container.register(ISettingsService,settings_service)
	container.register(IPrinterService,RealPrinterService(root,settings_service))
	container.register(IInventoryService,StubInventoryService())
	container.register(IHotkeyService,HotkeyService(settings_service))
	logger.info("[Main] Зарегистрирован HotkeyService")
	logger.info("Сервисы зарегистрированы в DI-контейнере")
	def _handle_tcl_error(exc_type,exc_value,exc_tb):
		if issubclass(exc_type,tk.TclError)and"invalid command name"in str(exc_value):
			logger.warning(f"TclError suppressed: {exc_value}")
			return
		root.report_callback_exception(exc_type,exc_value,exc_tb)
	import tkinter as tk
	root.report_callback_exception=_handle_tcl_error
	app=MainWindow(root,di_container=container)
	app.pack(fill="both",expand=True)
	logger.info("Главное окно создано")
	logger.info("Запуск главного цикла...")
	try:root.mainloop()
	except KeyboardInterrupt:logger.info("Приложение завершено пользователем")
	finally:
		settings_service=container.get(ISettingsService)
		if hasattr(settings_service,'save'):settings_service.save();logger.info("Настройки сохранены")
	logger.info("="*60)
if __name__=="__main__":main()