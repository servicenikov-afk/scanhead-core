# --- services/di_container.py ---
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
import logging
from typing import Dict, Type, Any, Optional
from services.interfaces import ISearchService, IProductRepository, IImageService, IPrinterService, ISettingsService, IInventoryService, IHotkeyService
from services.stubs import StubSearchService, StubProductRepository, StubImageService, StubPrinterService, StubSettingsService, StubInventoryService
logger=logging.getLogger(__name__)
class DIContainer:
	def __init__(self):
		self._services:Dict[Type,Any]={}
		logger.info("[DIContainer] Инициализация контейнера зависимостей")
	def register(self,interface:Type,implementation:Any)->None:
		self._services[interface]=implementation
		service_name=interface.__name__ if hasattr(interface,'__name__') else str(interface)
		logger.debug(f"[DIContainer] Зарегистрирован сервис: {service_name}")
	def get(self,interface:Type)->Any:
		if interface not in self._services:raise KeyError(f"Сервис {interface} не зарегистрирован")
		return self._services[interface]
	def has(self,interface:Type)->bool:
		return interface in self._services
	def register_default_services(self)->None:
		logger.info("[DIContainer] Регистрация заглушек сервисов по умолчанию")
		self.register(ISearchService,StubSearchService())
		self.register(IProductRepository,StubProductRepository())
		self.register(IImageService,StubImageService())
		self.register(IPrinterService,StubPrinterService())
		self.register(ISettingsService,StubSettingsService())
		self.register(IInventoryService,StubInventoryService())
		logger.info("[DIContainer] Все заглушки сервисов зарегистрированы")
	def register_real_services(self,config:dict)->None:
		logger.warning("[DIContainer] register_real_services ещё не реализован")