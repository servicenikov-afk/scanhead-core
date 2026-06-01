"""Модуль, отвечающий за отображение деталей продукта."""

import logging
from typing import Optional, Dict, Any, List

import customtkinter as ctk
from PIL import Image

from gui.framework.dialog_base import DialogHandler
from gui.framework.items_list_base import ItemsListBase
from gui.services.product_details_service import ProductDetailsService
from gui.services.product_repo_service import ProductRepoService # Реальный импорт
from gui.shared.product_formatter import ProductFormatter # Реальный импорт

from libs.domain_models import Product # Реальный импорт
from libs.domain_models.product_details import ProductDetails # Реальный импорт
from libs.i18n.i18n import I18n

# Удаляем импорты несуществующих модулей
# from gui.dialogs.common.dialog_list_base import DialogListBase # Нет
# from gui.dialogs.product_details.common.dialog_base import DialogBase # Нет
# from gui.services.error_handling_services import ErrorHandlingService # Нет
# from gui.services.main_services import MainServices # Нет

# --- Импорты для ProductInfoDialog ---
# Предполагаем, что ProductInfoDialog теперь находится в gui/dialogs/product_info_dialog.py
# и принимает Product из libs.domain_models
from gui.dialogs.product_info_dialog import ProductInfoDialog # Реальный импорт


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
        product_repo: ProductRepoService,
        details_service: ProductDetailsService,
        # store_adapter: Any, # Удалено
        # nomenclature_adapter: Any, # Удалено
        # css_adapter: Any, # Удалено
        # address_formatter: Any, # Удалено
        app_modes: Dict[str, bool],
        font_size: int = 14,
        **kwargs
    ):
        """
        Инициализация виджета ProductDetails.

        Args:
            master: Родительский виджет.
            product_repo: Сервис для работы с репозиторием продуктов.
            details_service: Сервис для получения детальной информации о продуктах.
            app_modes: Словарь с режимами приложения.
            font_size: Размер шрифта для виджетов.
            **kwargs: Дополнительные аргументы.
        """
        super().__init__(master, app_modes=app_modes, **kwargs)
        
        self._product_repo = product_repo
        self._details_service = details_service
        self._font_size = font_size
        
        # Инициализацияformatter
        self._product_formatter = ProductFormatter() # Предполагаем, что ProductFormatter существует

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
        self._product_details_cache: Dict[str, ProductDetails] = {}

        self._build_list_widgets()
        self._build_details_widgets()
        
        # Загружаем продукты при старте
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
        # --- Верхняя часть — информация о товаре ---
        details_header = ctk.CTkFrame(self._frame_details, fg_color="transparent")
        details_header.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 0))
        details_header.grid_columnconfigure(0, weight=1)

        # --- Обложка продукта (если есть) ---
        self._lbl_product_image = ctk.CTkLabel(details_header, text="", width=150, height=150)
        self._lbl_product_image.grid(row=0, column=0, pady=(0, 10), sticky="n")

        # --- Информация о цене и наличии ---
        self._lbl_product_price = ctk.CTkLabel(
            details_header, text="Цена:", font=ctk.CTkFont(size=self._font_size, weight="bold")
        )
        self._lbl_product_price.grid(row=1, column=0, sticky="nw")
        self._lbl_product_availability = ctk.CTkLabel(
            details_header, text="Наличие:", font=ctk.CTkFont(size=self._font_size, weight="bold")
        )
        self._lbl_product_availability.grid(row=2, column=0, sticky="nw")

        # --- Кнопка "Подробнее" ---
        self._btn_more_info = ctk.CTkButton(
            details_header, text="Подробнее", command=self._on_info_click,
            font=ctk.CTkFont(size=self._font_size - 2)
        )
        # Кнопка будет отображаться только если есть дополнительная информация
        # self._btn_more_info.grid(row=3, column=0, sticky="ew", pady=(10, 0))

        # --- Нижняя часть — вкладки с деталями ---
        self._tab_details = ctk.CTkTabview(self._frame_details, font=ctk.CTkFont(size=self._font_size - 1))
        self._tab_details.grid(row=1, column=0, sticky="nsew", padx=10, pady=(10, 10))
        self._tab_details.grid_columnconfigure(0, weight=1)
        self._tab_details.grid_rowconfigure(0, weight=1)
        
        # --- Добавляем вкладку "Описание" ---
        self._tab_description = self._tab_details.add("Описание")
        self._tab_details.tab("Описание").grid_columnconfigure(0, weight=1)
        self._tab_details.tab("Описание").grid_rowconfigure(0, weight=1)
        
        self._txt_description = ctk.CTkTextbox(
            self._tab_details.tab("Описание"), wrap="word",
            font=ctk.CTkFont(size=self._font_size),
            fg_color="transparent",
            state="disabled" # Доступен только для чтения
        )
        self._txt_description.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # --- Добавляем вкладку "Характеристики" ---
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
        
        # --- Добавляем вкладку "Адреса" ---
        self._tab_addresses = self._tab_details.add("Адреса")
        self._tab_details.tab("Адреса").grid_columnconfigure(0, weight=1)

        self._lbl_addresses = ctk.CTkLabel(
            self._tab_details.tab("Адреса"), text="",
            font=ctk.CTkFont(size=self._font_size),
            justify="left", wraplength=300
        )
        self._lbl_addresses.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    # --- Методы для загрузки данных ---

    def load_products(self, query: Optional[str] = None):
        """
        Загрузка списка продуктов из репозитория.

        Args:
            query: Строка поиска (не используется в этой версии).
        """
        try:
            self._product_list = self._product_repo.get_products(query=query) # Используем реальный метод
            self._list_widget.set_items(self._product_list)
            self._list_widget.update_view()
            
            # Если есть продукты, выбираем первый
            if self._product_list:
                first_product = self._product_list[0]
                self._list_widget.select_item(first_product)
                self.on_product_select(first_product)
                self.set_current_product(first_product) # Устанавливаем текущий продукт
            else:
                self.clear_details() # Очищаем детали, если продуктов нет
                
        except Exception as e:
            logger.error(f"Ошибка загрузки продуктов: {e}")
            # TODO: Показать сообщение об ошибке пользователю

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
        # Загружаем детали продукта, если их нет в кэше
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
                self._product_details_cache[product.article] = details
                self.update_product_details_tabs(details) # Обновляем UI
            else:
                logger.warning(f"Детальная информация для продукта {product.article} не найдена.")
                self.clear_details() # Очищаем, если деталей нет
                
        except Exception as e:
            logger.error(f"Ошибка загрузки деталей продукта {product.article}: {e}")
            # TODO: Показать сообщение об ошибке пользователю
            self.clear_details() # Очищаем детали в случае ошибки

    def update_product_details_tabs(self, details: ProductDetails):
        """
        Обновляет содержимое вкладок детальной информации.
        
        Args:
            details: Объект ProductDetails.
        """
        # --- Обновляем виджеты деталей ---
        # Изображение
        if details.image_path:
            try:
                img = Image.open(details.image_path)
                img.thumbnail((150, 150))
                self._lbl_product_image.configure(image=ctk.CTkImage(img, size=(150, 150)))
            except Exception as e:
                logger.error(f"Ошибка загрузки изображения {details.image_path}: {e}")
                self._lbl_product_image.configure(image=None)
        else:
            self._lbl_product_image.configure(image=None)

        # Цена и наличие
        price_text = self._product_formatter.format_price(details.price, details.currency) if details.price else "N/A"
        stock_text = I18n.get("product_details.availability.in_stock", "product_details.availability.in_stock", details.stock) if details.stock > 0 else I18n.get("product_details.availability.out_of_stock", "product_details.availability.out_of_stock")
        
        self._lbl_product_price.configure(text=f"Цена: {price_text}")
        self._lbl_product_availability.configure(text=f"Наличие: {stock_text}")
        
        # Кнопка "Подробнее" — активируем, если есть описание или характеристики
        has_details = bool(details.description or details.characteristics)
        self._btn_more_info.grid(row=3, column=0, sticky="ew", pady=(10, 0)) if has_details else self._btn_more_info.grid_forget()

        # --- Обновляем вкладки ---
        # Описание
        self._txt_description.configure(state="normal") # Разрешаем редактирование
        self._txt_description.delete("1.0", "end")
        self._txt_description.insert("1.0", details.description or "Нет описания.")
        self._txt_description.configure(state="disabled") # Запрещаем редактирование

        # Характеристики
        chars_text = ""
        if details.characteristics:
            for key, value in details.characteristics.items():
                chars_text += f"- {key}: {value}\n"
        else:
            chars_text = "Нет характеристик."
        self._lbl_characteristics.configure(text=chars_text)

        # Адреса
        addresses_text = "\n".join(details.storage_locations) if details.storage_locations else "Нет адресов хранения."
        self._lbl_addresses.configure(text=addresses_text)

    def _update_details_widgets(self):
        """Обновляет виджеты деталей на основе текущего продукта."""
        if self._current_product:
            # Попробуем загрузить детали из кэша
            details = self._product_details_cache.get(self._current_product.article)
            if details:
                self.update_product_details_tabs(details)
            else:
                # Если в кэше нет, пробуем загрузить
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
            # --- МИНИМАЛЬНЫЙ ВЫЗОВ ДИАЛОГА ---
            # Используем реальный объект Product из libs.domain_models
            # И font_size из текущего виджета
            dialog = ProductInfoDialog(
                master=self,
                product=self._current_product,
                font_size=self._font_size
            )
            dialog.grab_set() # Делаем диалог модальным
            dialog.wait_window() # Ждем закрытия диалога
            # --- КОНЕЦ МИНИМАЛЬНОГО ВЫЗОВА ---

            # Удален старый блок формирования product_data (dict)
            # Убран вызов несуществующих сервисов
            # dialog = ProductInfoDialog(
            #     self,
            #     product=product_data,  # dict, а не Product
            #     nomenclature_adapter=self._product_repo,
            #     store_adapter=self._product_repo,
            #     css_adapter=None,
            #     font_size=self._font_size,
            #     details_service=self._details_service,
            #     address_formatter=self._address_formatter
            # )
            # dialog.grab_set()
            # dialog.wait_window()

# --- Конец файла gui/product_details.py ---