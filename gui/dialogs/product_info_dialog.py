import tkinter as tk
from typing import Optional
from dataclasses import dataclass

from customtkinter import CTkFrame, CTkLabel, CTkButton, CTkTabview, CTkScrollableFrame, CTkCanvas, CTkFont
from PIL import Image

from gui.framework.dialog_base import DialogHandler
from gui.services.product_details_service import ProductDetailsService
from gui.services.error_handling_services import ErrorHandlingService
from gui.services.main_services import MainServices
from libs.data.product import Product
from libs.data.product_details import ProductDetails
from libs.i18n.i18n import I18n


# === ЗАГЛУШКИ ДЛЯ ОТСУТСТВУЮЩИХ ЗАВИСИМОСТЕЙ ===

# Заглушка для ProductDetailsCallbacks
class ProductDetailsCallbacks:
    def update_product_details_tabs(self, details):
        pass

# Заглушка для ProductInfo (dataclass-подобная)
@dataclass
class ProductInfo:
    product_id: str = ""
    product_name: str = ""
    model: str = ""

# Заглушка для ProductDetailsWidgets
class ProductDetailsWidgets:
    def __init__(self):
        self.lbl_css_loading: Optional[CTkLabel] = None
        self.lbl_product_name: Optional[CTkLabel] = None
        self.lbl_price: Optional[CTkLabel] = None
        self.lbl_availability: Optional[CTkLabel] = None

# Заглушка для ProductDetailsWidgetsBuilder
class ProductDetailsWidgetsBuilder:
    def __init__(self, master, product_details_callbacks):
        self.master = master
        self.callbacks = product_details_callbacks
    
    def build_widgets(self) -> ProductDetailsWidgets:
        widgets = ProductDetailsWidgets()
        # Создаём виджет загрузки напрямую
        # Предполагаем, что _font_size доступен или устанавливаем значение по умолчанию
        _font_size = 14 # Устанавливаем значение по умолчанию, если _font_size не определено
        widgets.lbl_css_loading = CTkLabel(self.master, text="⏳ Загрузка...", font=CTkFont(size=_font_size))
        return widgets


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
        # Исправлено: callbacks теперь может быть None и используется заглушка
        callbacks: Optional[ProductDetailsCallbacks] = None,
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
        # Исправлено: Используем заглушку, если callbacks не предоставлен
        self.__callbacks = callbacks or ProductDetailsCallbacks()

        self.configure_window(
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
        # Прямая инициализация виджетов вместо использования builder'а
        self.__product_details_widgets = ProductDetailsWidgets()
        # Предполагаем, что _font_size доступен или устанавливаем значение по умолчанию
        _font_size = 14 # Устанавливаем значение по умолчанию, если _font_size не определено
        self.__product_details_widgets.lbl_css_loading = CTkLabel(
            self, text="⏳ Загрузка...", font=CTkFont(size=_font_size)
        )
        self._lbl_css_loading = self.__product_details_widgets.lbl_css_loading
        self._lbl_css_loading.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def _fetch_product_details(self):
        """Запрос данных о товаре."""
        self.__product_details_service.get_product_details(
            # Исправлено: Используем self.__product.article вместо product_id
            product_id=self.__product.article, callback=self.on_details_loaded
        )

    def on_details_loaded(self, details: Optional[ProductDetails]):
        """
        Обработчик загрузки данных о товаре.

        Args:
            details: Объект ProductDetails или None в случае ошибки.
        """
        # Убираем индикатор загрузки, если он существует и виджет существует
        if self._lbl_css_loading and self._lbl_css_loading.winfo_exists():
            self._lbl_css_loading.grid_forget()

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
            # Добавлена проверка winfo_exists() перед обращением к виджетам
            if hasattr(self.__product_details_widgets, 'lbl_product_name') and self.__product_details_widgets.lbl_product_name and self.__product_details_widgets.lbl_product_name.winfo_exists():
                self.__product_details_widgets.lbl_product_name.configure(
                    text=f"{self.__product.product_name} ({self.__product.model})"
                )
            if hasattr(self.__product_details_widgets, 'lbl_price') and self.__product_details_widgets.lbl_price and self.__product_details_widgets.lbl_price.winfo_exists():
                self.__product_details_widgets.lbl_price.configure(text=f"{details.price} {details.currency}")
            if hasattr(self.__product_details_widgets, 'lbl_availability') and self.__product_details_widgets.lbl_availability and self.__product_details_widgets.lbl_availability.winfo_exists():
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

# Проверка синтаксиса
if __name__ == "__main__":
    try:
        import sys
        sys.path.append(".") # Добавляем текущую директорию в sys.path для корректного импорта
        import gui.dialogs.product_info_dialog # Импортируем файл для проверки синтаксиса
        print("Синтаксис gui/dialogs/product_info_dialog.py корректен.")
    except ModuleNotFoundError as e:
        print(f"Ошибка ModuleNotFoundError при проверке синтаксиса: {e}")
    except ImportError as e:
        print(f"Ошибка ImportError при проверке синтаксиса: {e}")
    except Exception as e:
        print(f"Непредвиденная ошибка при проверке синтаксиса: {e}")

