
import tkinter as tk
from typing import Optional

from customtkinter import CTkFrame, CTkLabel, CTkButton, CTkTabview, CTkScrollableFrame, CTkCanvas
from PIL import Image

from gui.dialogs.common.dialog_handling import DialogHandler
from gui.dialogs.common.error_message_dialog import ErrorMessageDialog
from gui.dialogs.common.messages_box import MessagesBox
from gui.dialogs.product_details.common.callbacks import ProductDetailsCallbacks
from gui.dialogs.product_details.common.common import ProductInfo, ProductDetailsWidgets
from gui.dialogs.product_details.common.product_details_widgets_builder import ProductDetailsWidgetsBuilder
from gui.dialogs.product_details.services.product_details_service import ProductDetailsService
from gui.services.error_handling_services import ErrorHandlingService
from gui.services.main_services import MainServices
from libs.data.product import Product
from libs.data.product_details import ProductDetails
from libs.i18n.i18n import I18n


class ProductInfoDialog(DialogHandler):
    """Диалог для отображения подробной информации о товаре."""

    _instance = None

    def __init__(
        self,
        master: any,
        product: Product,
        main_services: MainServices,
        product_details_service: ProductDetailsService,
        error_handling_service: ErrorHandlingService,
        callbacks: ProductDetailsCallbacks,
    ):
        """
        Инициализация диалога.

        Args:
            master: Родительский виджет.
            product: Объект продукта, для которого отображается информация.
            main_services: Сервисы основного приложения.
            product_details_service: Сервис для получения данных о товаре.
            error_handling_service: Сервис для обработки ошибок.
            callbacks: Коллбэки для взаимодействия с другими частями приложения.
        """
        super().__init__(master=master, app_modes=main_services.app_modes)
        self.__product = product
        self.__main_services = main_services
        self.__product_details_service = product_details_service
        self.__error_handling_service = error_handling_service
        self.__callbacks = callbacks

        self.__dialog_handler = DialogHandler(master=self, app_modes=main_services.app_modes)
        self.__product_details_widgets: ProductDetailsWidgets = ProductDetailsWidgets()

        self.__dialog_handler.configure_window(
            title=f"{product.product_name} ({product.model})",
            resizable=True,
            width=1200,
            height=800,
        )
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.__build_widgets()
        self._fetch_product_details()

    def __build_widgets(self):
        """Сборка виджетов диалога."""
        product_details_widgets_builder = ProductDetailsWidgetsBuilder(
            master=self,
            product_details_callbacks=self.__callbacks,
        )
        self.__product_details_widgets = product_details_widgets_builder.build_widgets()

        self._lbl_css_loading = self.__product_details_widgets.lbl_css_loading
        self._lbl_css_loading.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def _fetch_product_details(self):
        """Запрос данных о товаре."""
        self.__product_details_service.get_product_details(
            product_id=self.__product.product_id, callback=self.on_details_loaded
        )

    def on_details_loaded(self, details: Optional[ProductDetails]):
        """
        Обработчик загрузки данных о товаре.

        Args:
            details: Объект ProductDetails или None в случае ошибки.
        """
        self._lbl_css_loading.grid_forget()  # Убираем индикатор загрузки

        if details is None:
            # Устанавливаем текст ошибки, если данные не были загружены
            # Проверяем, существует ли виджет перед обновлением
            if self._lbl_css_loading and self._lbl_css_loading.winfo_exists():
                self._lbl_css_loading.configure(text="Не удалось загрузить данные")
            # Отображаем сообщение об ошибке для пользователя
            self.__error_handling_service.show_error_message(
                title=I18n.get(
                    "product_details.error.title",
                    "product_details.error.title",
                    self.__product.product_name,
                ),
                message=I18n.get(
                    "product_details.error.message",
                    "product_details.error.message",
                    self.__product.product_name,
                ),
            )
            # Закрываем диалог, так как не можем отобразить информацию
            self.destroy()

        else:
            # Данные успешно загружены, отображаем их
            self.__product_details_widgets.lbl_product_name.configure(
                text=f"{self.__product.product_name} ({self.__product.model})"
            )
            self.__product_details_widgets.lbl_price.configure(text=f"{details.price} {details.currency}")
            self.__product_details_widgets.lbl_availability.configure(
                text=I18n.get(
                    "product_details.availability.in_stock",
                    "product_details.availability.in_stock",
                    details.stock,
                )
                if details.stock > 0
                else I18n.get(
                    "product_details.availability.out_of_stock",
                    "product_details.availability.out_of_stock",
                )
            )

            self.__callbacks.update_product_details_tabs(details)

            # Убираем виджет загрузки, если он всё ещё существует
            if self._lbl_css_loading and self._lbl_css_loading.winfo_exists():
                self._lbl_css_loading.grid_forget()

    def destroy(self):
        """Переопределённый метод destroy для очистки ресурсов."""
        # Удаляем все виджеты, связанные с этим диалогом
        for widget in self.winfo_children():
            widget.destroy()
        super().destroy()

    @classmethod
    def show_dialog(
        cls,
        master: any,
        product: Product,
        main_services: MainServices,
        product_details_service: ProductDetailsService,
        error_handling_service: ErrorHandlingService,
        callbacks: ProductDetailsCallbacks,
    ):
        """
        Отображает диалог информации о товаре.

        Args:
            master: Родительский виджет.
            product: Объект продукта.
            main_services: Сервисы основного приложения.
            product_details_service: Сервис получения данных о товаре.
            error_handling_service: Сервис обработки ошибок.
            callbacks: Коллбэки для взаимодействия.
        """
        if cls._instance is not None:
            cls._instance.destroy()
            cls._instance = None

        cls._instance = cls(
            master,
            product,
            main_services,
            product_details_service,
            error_handling_service,
            callbacks,
        )
        cls._instance.grab_set()

