"""
Интерфейсы сервисов для внедрения зависимостей (DI).
Все бизнес-сервисы реализуют эти интерфейсы.
"""

from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Any
from libs.domain_models.models import Product, Address


class ISearchService(ABC):
    """Сервис поиска товаров."""
    
    @abstractmethod
    def search_async(self, query: str, callback: Callable[[List[Product]], None]) -> None:
        """
        Асинхронный поиск товаров по запросу.
        
        :param query: Строка поиска (артикул, название, штрих-код)
        :param callback: Функция обратного вызова с результатами поиска
        """
        pass
    
    @abstractmethod
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """
        Получение товара по ID.
        
        :param product_id: Идентификатор товара
        :return: Товар или None, если не найден
        """
        pass


class IProductRepository(ABC):
    """Репозиторий для операций с товарами."""
    
    @abstractmethod
    def update_field(self, product_id: int, field_name: str, value: Any) -> bool:
        """
        Универсальное обновление поля товара.
        
        :param product_id: Идентификатор товара
        :param field_name: Имя поля для обновления
        :param value: Новое значение
        :return: True если успешно, False иначе
        """
        pass
    
    @abstractmethod
    def get_address_for_product(self, product_id: int) -> Optional[Address]:
        """
        Получение адреса хранения для товара.
        
        :param product_id: Идентификатор товара
        :return: Адрес или None
        """
        pass


class IImageService(ABC):
    """Сервис загрузки изображений (заглушка для будущих версий)."""
    
    @abstractmethod
    def load_image_async(self, url: str, callback: Callable[[Optional[Any]], None]) -> None:
        """
        Асинхронная загрузка изображения.
        
        :param url: URL изображения
        :param callback: Функция обратного вызова с изображением или None
        """
        pass
    
    @abstractmethod
    def get_placeholder(self) -> Any:
        """
        Получение изображения-заглушки.
        
        :return: Изображение-заглушка
        """
        pass


class IPrinterService(ABC):
    """Сервис печати этикеток."""
    
    @abstractmethod
    def generate_sticker(self, product: Product, preset: dict) -> Any:
        """
        Генерация изображения стикера.
        
        :param product: Товар для печати
        :param preset: Пресет оформления
        :return: Изображение стикера (PIL.Image)
        """
        pass
    
    @abstractmethod
    def print_sticker(self, image: Any, copies: int = 1) -> bool:
        """
        Печать стикера.
        
        :param image: Изображение для печати
        :param copies: Количество копий
        :return: True если успешно
        """
        pass
    
    @abstractmethod
    def print_queue(self, products: List[Product], one_by_one: bool = False) -> bool:
        """
        Печать очереди товаров.
        
        :param products: Список товаров для печати
        :param one_by_one: Если True - печатать по одному с диалогом, иначе - одним PDF
        :return: True если успешно
        """
        pass


class ISettingsService(ABC):
    """Сервис настроек приложения."""
    
    @abstractmethod
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Получение настройки по ключу."""
        pass
    
    @abstractmethod
    def set_setting(self, key: str, value: Any) -> None:
        """Сохранение настройки."""
        pass
    
    @abstractmethod
    def get_column_config(self) -> dict:
        """Получение конфигурации колонок таблицы."""
        pass
    
    @abstractmethod
    def set_column_config(self, config: dict) -> None:
        """Сохранение конфигурации колонок таблицы."""
        pass


class IInventoryService(ABC):
    """Сервис инвентаризации (заглушка для будущего функционала)."""
    
    @abstractmethod
    def import_inventory(self, file_path: str) -> bool:
        """Импорт файла инвентаризации."""
        pass
    
    @abstractmethod
    def export_report(self, file_path: str) -> bool:
        """Экспорт отчёта инвентаризации."""
        pass
    
    @abstractmethod
    def start_scanning(self) -> None:
        """Запуск режима сканирования."""
        pass
    
    @abstractmethod
    def stop_scanning(self) -> None:
        """Остановка режима сканирования."""
        pass