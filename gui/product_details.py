"""Модуль, отвечающий за отображение деталей продукта."""

import logging
from typing import Optional, Dict, Any, List, Callable
from PIL import Image
import customtkinter as ctk

from gui.framework.list_base import ItemsListBase
from services.interfaces import IProductRepository
from gui.services.product_details_service import ProductDetailsService
from libs.utils import AddressFormatter, AddressFormatConfig
from libs.domain_models import Product
# from libs.domain_models.product_details import ProductDetails  # Удален, т.к. файла не существует
# from libs.i18n.i18n import I18n  # Удален, т.к. модуль не найден


logger = logging.getLogger(__name__)


class ProductDetails(ItemsListBase):
    """
    Виджет для отображения списка продуктов с возможностью выбора.
    Содержит боковую панель с деталями выбранного продукта.
    """

    def __init__(
        self,
        master: Any,
        *,
        product_repo: IProductRepository,
        details_service: ProductDetailsService,
        address_formatter: AddressFormatter,
        # app_modes: Dict[str, bool],  # Удален obsolete параметр
        font_size: int = 14,
        **kwargs
    ):
        """
        Инициализация виджета ProductDetails.

        Args:
            master: Родительский виджет.
            product_repo: Сервис для работы с репозиторием продуктов (интерфейс).
            details_service: Сервис для получения детальной информации о продуктах.
            address_formatter: Форматтер адресов.
            # app_modes: Словарь с режимами приложения. (obsolete)
            font_size: Размер шрифта для виджетов.
            **kwargs: Дополнительные аргументы.
        """
        # super().__init__(master, app_modes=app_modes, **kwargs) # Удалена ссылка на app_modes
        super().__init__(master, **kwargs) 
        
        self._product_repo = product_repo
        self._details_service = details_service
        self._address_formatter = address_formatter
        self._font_size = font_size
        
        # --- Инициализация виджетов ---
        self._frame_list = ctk.CTkFrame(self, fg_color="transparent")
        self._frame_list.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        self._frame_list.grid_rowconfigure(0, weight=1)
        self._frame_list.grid_columnconfigure(0, weight=1)

        self._frame_details = ctk.CTkFrame(self, width=300, fg_color="gray80")
        self._frame_details.grid(row=0, column=1, sticky="ns", padx=(5, 10), pady=10)
        self._frame_details.grid_rowconfigure(0, weight=1)
        self._frame_details.grid_columnconfigure(0, weight=0)
        self._frame_details.grid_propagate(False) # Фиксируем ширину

        # --- Данные ---
        self._product_list: List[Product] = []
        self._current_product: Optional[Product] = None
        # Заменяем ProductDetails на Dict[str, Any] для кэша
        self._product_details_cache: Dict[str, Dict[str, Any]] = {} 

        self._build_list_widgets()
        self._build_details_widgets()
        
        self.load_products()

    def _build_list_widgets(self):
        """Сборка виджетов для списка продуктов."""
        self._list_widget = ItemsListBase(
            self._frame_list,
            columns=("article", "name", "price"),
            column_widths=(80, 250, 100),
            column_texts=("Артикул", "Наименование", "Цена"),
            item_select_callback=self.on_product_select,
            font_size=self._font_size,
        )
        self._list_widget.pack(fill="both", expand=True)

    def _build_details_widgets(self):
        """Сборка виджетов для деталей продукта."""
        details_header = ctk.CTkFrame(self._frame_details, fg_color="transparent")
        details_header.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 0))
        details_header.grid_columnconfigure(0, weight=1)

        self._lbl_product_image = ctk.CTkLabel(details_header, text="", width=150, height=150)
        self._lbl_product_image.grid(row=0, column=0, pady=(0, 10), sticky="n")

        self._lbl_product_price = ctk.CTkLabel(
            details_header, text="Цена:", font=ctk.CTkFont(size=self._font_size, weight="bold")
        )
        self._lbl_product_price.grid(row=1, column=0, sticky="nw")
        self._lbl_product_availability = ctk.CTkLabel(
            details_header, text="Наличие:", font=ctk.CTkFont(size=self._font_size, weight="bold")
        )
        self._lbl_product_availability.grid(row=2, column=0, sticky="nw")

        self._btn_more_info = ctk.CTkButton(
            details_header, text="Подробнее", command=self._on_info_click,
            font=ctk.CTkFont(size=self._font_size - 2)
        )

        self._tab_details = ctk.CTkTabview(self._frame_details, font=ctk.CTkFont(size=self._font_size - 1))
        self._tab_details.grid(row=1, column=0, sticky="nsew", padx=10, pady=(10, 10))
        self._tab_details.grid_columnconfigure(0, weight=1)
        self._tab_details.grid_rowconfigure(0, weight=1)
        
        self._tab_description = self._tab_details.add("Описание")
        self._tab_details.tab("Описание").grid_columnconfigure(0, weight=1)
        self._tab_details.tab("Описание").grid_rowconfigure(0, weight=1)
        
        self._txt_description = ctk.CTkTextbox(
            self._tab_details.tab("Описание"), wrap="word",
            font=ctk.CTkFont(size=self._font_size),
            fg_color="transparent",
            state="disabled"
        )
        self._txt_description.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self._tab_characteristics = self._tab_details.add("Характеристики")
        self._tab_details.tab("Характеристики").grid_columnconfigure(1, weight=1)

        self._lbl_characteristics_title = ctk.CTkLabel(
            self._tab_details.tab("Характеристики"), text="Характеристики:",
            font=ctk.CTkFont(size=self._font_size, weight="bold")
        )
        self._lbl_characteristics_title.grid(row=0, column=0, columnspan=2, sticky="nw", padx=5, pady=(5, 10))

        self._lbl_characteristics = ctk.CTkLabel(
            self._tab_details.tab("Характеристики"), text="",
            font=ctk.CTkFont(size=self._font_size),
            justify="left", wraplength=300
        )
        self._lbl_characteristics.grid(row=1, column=0, columnspan=2, sticky="nw", padx=5)
        
        self._tab_addresses = self._tab_details.add("Адреса")
        self._tab_details.tab("Адреса").grid_columnconfigure(0, weight=1)

        self._lbl_addresses = ctk.CTkLabel(
            self._tab_details.tab("Адреса"), text="",
            font=ctk.CTkFont(size=self._font_size),
            justify="left", wraplength=300
        )
        self._lbl_addresses.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    def load_products(self, query: Optional[str] = None):
        """
        Загрузка списка продуктов из репозитория.

        Args:
            query: Строка поиска (не используется в этой версии).
        """
        try:
            self._product_list = self._product_repo.get_products(query=query)
            self._list_widget.set_items(self._product_list)
            self._list_widget.update_view()
            
            if self._product_list:
                first_product = self._product_list[0]
                self._list_widget.select_item(first_product)
                self.on_product_select(first_product)
                self.set_current_product(first_product)
            else:
                self.clear_details()
                
        except Exception as e:
            logger.error(f"Ошибка загрузки продуктов: {e}")

    def set_current_product(self, product: Product):
        """Устанавливает текущий выбранный продукт."""
        self._current_product = product
        self._update_details_widgets()
        
    def on_product_select(self, product: Product):
        """
        Обработчик выбора продукта из списка.
        
        Args:
            product: Выбранный объект продукта.
        """
        self.set_current_product(product)
        if product.article not in self._product_details_cache:
            self._fetch_product_details(product)

    def _fetch_product_details(self, product: Product):
        """
        Загружает детальную информацию о продукте и обновляет UI.
        
        Args:
            product: Объект продукта, для которого нужно загрузить детали.
        """
        try:
            # Используем product_details_service для получения данных
            # Убедимся, что используем правильный идентификатор продукта
            details = self._details_service.get_product_details(product.article)
            if details:
                # Сохраняем детали в кэш, используя Dict[str, Any]
                self._product_details_cache[product.article] = details 
                self.update_product_details_tabs(details)
            else:
                logger.warning(f"Детальная информация для продукта {product.article} не найдена.")
                self.clear_details()
                
        except Exception as e:
            logger.error(f"Ошибка загрузки деталей продукта {product.article}: {e}")
            self.clear_details()

    def update_product_details_tabs(self, details: Dict[str, Any]): # Изменен тип на Dict[str, Any]
        """
        Обновляет содержимое вкладок детальной информации.
        
        Args:
            details: Словарь с деталями продукта.
        """
        # Изображение
        # Предполагаем, что 'image_path' есть в словаре details
        image_path = details.get("image_path")
        if image_path:
            try:
                img = Image.open(image_path)
                img.thumbnail((150, 150))
                self._lbl_product_image.configure(image=ctk.CTkImage(img, size=(150, 150)))
            except Exception as e:
                logger.error(f"Ошибка загрузки изображения {image_path}: {e}")
                self._lbl_product_image.configure(image=None)
        else:
            self._lbl_product_image.configure(image=None)

        # Цена и наличие
        # Используем AddressFormatter для форматирования цены, предполагая наличие метода format_price
        price = details.get("price")
        currency = details.get("currency")
        # Проверяем, существует ли метод format_price в AddressFormatter
        if hasattr(self._address_formatter, 'format_price'):
            price_text = self._address_formatter.format_price(price, currency) if price else "N/A"
        else:
            # Если метода нет, форматируем напрямую
            price_text = f"{price} {currency}" if price else "N/A"
            
        stock = details.get("stock", 0) # По умолчанию 0, если ключ отсутствует
        # Заменяем I18n.get на строку, т.к. I18n сервис недоступен
        # stock_text = I18n.get("product_details.availability.in_stock", "product_details.availability.in_stock", stock) if stock > 0 else I18n.get("product_details.availability.out_of_stock", "product_details.availability.out_of_stock")
        stock_text = "В наличии" if stock > 0 else "Нет в наличии" # TODO: Интегрировать сервис i18n
        
        self._lbl_product_price.configure(text=f"Цена: {price_text}")
        self._lbl_product_availability.configure(text=f"Наличие: {stock_text}")
        
        # Проверяем наличие description и characteristics в словаре details
        has_details = bool(details.get("description") or details.get("characteristics"))
        self._btn_more_info.grid(row=3, column=0, sticky="ew", pady=(10, 0)) if has_details else self._btn_more_info.grid_forget()

        # Описание
        self._txt_description.configure(state="normal")
        self._txt_description.delete("1.0", "end")
        self._txt_description.insert("1.0", details.get("description", "Нет описания."))
        self._txt_description.configure(state="disabled")

        # Характеристики
        characteristics = details.get("characteristics", {})
        chars_text = ""
        if characteristics:
            for key, value in characteristics.items():
                chars_text += f"- {key}: {value}\n"
        else:
            chars_text = "Нет характеристик."
        self._lbl_characteristics.configure(text=chars_text)

        # Адреса
        storage_locations = details.get("storage_locations", [])
        addresses_text = "\n".join(storage_locations) if storage_locations else "Нет адресов хранения."
        self._lbl_addresses.configure(text=addresses_text)

    def _update_details_widgets(self):
        """Обновляет виджеты деталей на основе текущего продукта."""
        if self._current_product:
            # Получаем детали из кэша, используя Dict[str, Any]
            details = self._product_details_cache.get(self._current_product.article)
            if details:
                self.update_product_details_tabs(details)
            else:
                self._fetch_product_details(self._current_product)
        else:
            self.clear_details()

    def clear_details(self):
        """Очищает область деталей."""
        self._lbl_product_image.configure(image=None)
        self._lbl_product_price.configure(text="Цена: N/A")
        self._lbl_product_availability.configure(text="Наличие: N/A")
        self._txt_description.configure(state="normal")
        self._txt_description.delete("1.0", "end")
        self._txt_description.insert("1.0", "Нет данных.")
        self._txt_description.configure(state="disabled")
        self._lbl_characteristics.configure(text="Нет данных.")
        self._lbl_addresses.configure(text="Нет данных.")
        self._btn_more_info.grid_forget()

    # --- Обработчики событий ---

    def _on_info_click(self):
        """
        Обработчик нажатия кнопки 'Подробнее'.
        Открывает диалог ProductInfoDialog с детальной информацией.
        """
        if self._current_product:
            # Передаем _current_product (тип Product) в диалог
            # Если ProductInfoDialog ожидает Dict[str, Any], нужно будет преобразовать
            dialog = ProductInfoDialog(
                master=self,
                product=self._current_product, # Передаем Product
                font_size=self._font_size
            )
            dialog.grab_set()
            dialog.wait_window()

# --- Конец файла gui/product_details.py ---