# --- gui/tabs/search_address_tab.py ---
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
import logging
from typing import Any, List, Optional
import customtkinter as ctk
from libs.domain_models import Product
from services.di_container import DIContainer
from services.interfaces import ISearchService, IProductRepository, IPrinterService, ISettingsService
from gui.search_bar import SearchBar
from gui.product_details import ProductDetails
from gui.print_queue import PrintQueue
from gui.sticker_preview import StickerPreview
logger = logging.getLogger(__name__)
class SearchAddressTab(ctk.CTkFrame):
	def __init__(self, master: Any, di_container: DIContainer):
		super().__init__(master)
		self._container = di_container
		self._current_products: List[Product] = []
		logger.info("[SearchAddressTab] Инициализация вкладки")
		self.grid_rowconfigure(0, weight=0)
		self.grid_rowconfigure(1, weight=3)
		self.grid_rowconfigure(2, weight=1)
		self.grid_columnconfigure(0, weight=3, uniform="bottom")
		self.grid_columnconfigure(1, weight=1, uniform="bottom")
		self._create_search_bar()
		self._create_details_panel()
		self._create_bottom_panel()
		logger.info("[SearchAddressTab] Вкладка инициализирована")
	def _create_search_bar(self) -> None:
		search_frame = ctk.CTkFrame(self, fg_color="transparent")
		search_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=2, pady=(2, 5))
		search_frame.grid_columnconfigure(0, weight=1)
		settings_service = self._container.get(ISettingsService)
		config = {
			"search_font_size": settings_service.get_setting("search_font_size", 18),
			"search_autofocus": settings_service.get_setting("search_autofocus", True),
			"search_autofocus_delay": settings_service.get_setting("search_autofocus_delay", 1.0),
			"search_autoclear_enabled": settings_service.get_setting("search_autoclear_enabled", True),
			"search_autoclear_delay": settings_service.get_setting("search_autoclear_delay", 3.0),
		}
		self._search_bar = SearchBar(
			search_frame,
			search_service=self._container.get(ISearchService),
			on_search_result=self._on_search_result,
			config=config
		)
		self._search_bar.grid(row=0, column=0, sticky="ew")
		logger.debug(f"[SearchAddressTab] Поисковая строка создана с конфигом: {config}")
	def _create_details_panel(self) -> None:
		details_frame = ctk.CTkFrame(self)
		details_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=3, pady=3)
		details_frame.grid_rowconfigure(0, weight=1)
		details_frame.grid_columnconfigure(0, weight=1)
		settings_service = self._container.get(ISettingsService)
		font_size = settings_service.get_setting("search_font_size", 18)
		from libs.utils import AddressFormatConfig, AddressFormatter
		address_config_dict = settings_service.get_setting("address_format", {})
		address_config = AddressFormatConfig.from_dict(address_config_dict) if address_config_dict else AddressFormatConfig()
		address_formatter = AddressFormatter(config=address_config)
		self._product_details = ProductDetails(
			details_frame,
			product_repo=self._container.get(IProductRepository),
			on_add_to_queue=self._add_product_to_queue,
			font_size=font_size,
			details_service=self._container.get("product_details_service") if self._container.has("product_details_service") else None,
			address_formatter=address_formatter
		)
		self._product_details.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)
	def _create_bottom_panel(self) -> None:
		self._print_queue = PrintQueue(
			self,
			product_repo=self._container.get(IProductRepository),
			printer_service=self._container.get(IPrinterService),
			settings_service=self._container.get(ISettingsService)
		)
		self._print_queue.grid(row=2, column=0, sticky="nsew", padx=3, pady=3)
		self._sticker_preview = StickerPreview(
			self,
			printer_service=self._container.get(IPrinterService),
			settings_service=self._container.get(ISettingsService),
			search_service=self._container.get(ISearchService)
		)
		self._sticker_preview.grid(row=2, column=1, sticky="nsew", padx=3, pady=3)
	def _on_search_result(self, products: List[Product]) -> None:
		if self._container.has("product_details_service") and products:
			details_service = self._container.get("product_details_service")
			logger.debug(f"[DEBUG_TEMP] Получено {len(products)} товаров из БД")
			for i, p in enumerate(products[:3]):
				logger.debug(f"[DEBUG_TEMP] Товар[{i}]: {p.article}, адресов в raw: {len(p.storage_locations) if hasattr(p, 'storage_locations') else 0}")
			enriched_products = products.copy()
			pending_count = len(products)
			def on_details_loaded(product: Optional[Product], index: int):
				if product:
					enriched_products[index] = product
					logger.debug(f"[DEBUG_TEMP] Обогащён товар[{index}]: {product.article}, адресов: {len(product.storage_locations) if product.storage_locations else 0}")
					if product.storage_locations:
						logger.debug(f"[DEBUG_TEMP] Адреса товара[{index}]: {product.storage_locations[:3]}")
				else:
					logger.debug(f"[DEBUG_TEMP] Не удалось обогатить товар на позиции {index}")
				nonlocal pending_count
				pending_count -= 1
				if pending_count == 0:
					logger.info(f"[DEBUG_TEMP] Все товары обогащены, обновляем UI ({len(enriched_products)} шт.)")
					for i, p in enumerate(enriched_products[:3]):
						logger.debug(f"[DEBUG_TEMP] Итоговый товар[{i}]: {p.article}, адресов: {len(p.storage_locations) if p.storage_locations else 0}")
					self.update_products(enriched_products)
			for i, product in enumerate(products):
				details_service.get_product_details(
					product.article,
					callback=lambda p, idx=i: on_details_loaded(p, idx)
				)
		else:
			logger.debug(f"[DEBUG_TEMP] Сервис обогащения недоступен или товаров нет, передаём как есть")
			self.update_products(products)
	def _add_product_to_queue(self, product: Product) -> None:
		logger.info(f"[SearchAddressTab] Добавление товара {product.article} в очередь")
		self._print_queue.add_item(product)
	def update_products(self, products: List[Product]) -> None:
		self._current_products = products
		logger.info(f"[SearchAddressTab] Обновление товаров, найдено: {len(products)}")
		if products:
			self._product_details.set_product(products[0])
			self._sticker_preview.set_product(products[0])
		else:
			self._product_details.clear()
			self._sticker_preview.clear()
	def get_current_product(self) -> Product | None:
		return self._product_details.get_current_product()
	def on_setting_changed(self, key: str, value: Any) -> None:
		if key.startswith("search_"):
			self._search_bar.apply_settings({key: value})
			logger.info(f"[SearchAddressTab] Применена настройка {key}={value}")