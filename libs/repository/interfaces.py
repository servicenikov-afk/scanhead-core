"""
Абстрактные репозитории для доступа к данным.

Этот модуль определяет интерфейсы (контракты) для работы с данными.
Реализации конкретных СУБД (SQLite, PostgreSQL) должны наследовать эти классы
и реализовывать их методы.

Это обеспечивает соблюдение принципа инверсии зависимостей (DIP):
бизнес-логика зависит от абстракций, а не от деталей реализации БД.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Any, Dict
from pathlib import Path

# Импортируем доменные модели, чтобы использовать их в типах
try:
    from libs.domain_models import Product, InventoryItem, Address, CountItem
except ImportError:
    # Фоллбэк для случаев, когда модули еще не установлены в окружении
    # В реальном проекте лучше использовать строгую зависимость
    Product = Any
    InventoryItem = Any
    Address = Any
    CountItem = Any


class BaseRepository(ABC):
    """Базовый класс для всех репозиториев."""

    def __init__(self, db_path: Optional[Path] = None, connection: Any = None):
        """
        Инициализация репозитория.

        :param db_path: Путь к файлу базы данных (для SQLite).
        :param connection: Существующее соединение с БД (опционально).
        """
        self.db_path = db_path
        self._connection = connection
        self._local_connection = False

    @abstractmethod
    def connect(self) -> None:
        """Установить соединение с базой данных."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Закрыть соединение с базой данных."""
        pass

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


class ProductRepository(BaseRepository):
    """
    Репозиторий для работы с номенклатурой (товарами/продуктами).

    Отвечает за поиск, создание, обновление и удаление товаров,
    а также за работу с артикулами и штрих-кодами.
    """

    @abstractmethod
    def get_by_article(self, article: str) -> Optional[Product]:
        """
        Найти товар по артикулу.

        :param article: Артикульный номер (нормализованный).
        :return: Объект Product или None, если не найдено.
        """
        pass

    @abstractmethod
    def get_by_barcode(self, barcode: str) -> Optional[Product]:
        """
        Найти товар по штрих-коду.

        :param barcode: Штрих-код (EAN13, Code128 и т.д.).
        :return: Объект Product или None, если не найдено.
        """
        pass

    @abstractmethod
    def search_by_name(self, query: str, limit: int = 20) -> List[Product]:
        """
        Поиск товаров по названию (частичное совпадение).

        :param query: Строка поиска.
        :param limit: Максимальное количество результатов.
        :return: Список найденных товаров.
        """
        pass

    @abstractmethod
    def get_all(self, limit: Optional[int] = None) -> List[Product]:
        """
        Получить список всех товаров.

        :param limit: Ограничение количества записей.
        :return: Список всех товаров.
        """
        pass

    @abstractmethod
    def save(self, product: Product) -> bool:
        """
        Сохранить товар (создать или обновить).

        :param product: Объект товара для сохранения.
        :return: True если успешно, иначе False.
        """
        pass

    @abstractmethod
    def delete(self, article: str) -> bool:
        """
        Удалить товар по артикулу.

        :param article: Артикульный номер.
        :return: True если успешно, иначе False.
        """
        pass

    @abstractmethod
    def exists(self, article: str) -> bool:
        """
        Проверить существование товара по артикулу.

        :param article: Артикульный номер.
        :return: True если существует, иначе False.
        """
        pass


class InventoryRepository(BaseRepository):
    """
    Репозиторий для работы с документами инвентаризации.

    Отвечает за сохранение и загрузку результатов пересчета товаров.
    """

    @abstractmethod
    def create_document(self, name: str, date: Optional[str] = None) -> int:
        """
        Создать новый документ инвентаризации.

        :param name: Название документа.
        :param date: Дата документа (строка или datetime).
        :return: ID созданного документа.
        """
        pass

    @abstractmethod
    def add_item(self, doc_id: int, item: InventoryItem) -> bool:
        """
        Добавить позицию в документ инвентаризации.

        :param doc_id: ID документа.
        :param item: Позиция инвентаризации.
        :return: True если успешно, иначе False.
        """
        pass

    @abstractmethod
    def get_document_items(self, doc_id: int) -> List[InventoryItem]:
        """
        Получить все позиции документа.

        :param doc_id: ID документа.
        :return: Список позиций.
        """
        pass

    @abstractmethod
    def finalize_document(self, doc_id: int) -> bool:
        """
        Завершить документ инвентаризации (заблокировать редактирование).

        :param doc_id: ID документа.
        :return: True если успешно, иначе False.
        """
        pass

    @abstractmethod
    def get_statistics(self, doc_id: int) -> Dict[str, Any]:
        """
        Получить статистику по документу (кол-во позиций, расхождения и т.д.).

        :param doc_id: ID документа.
        :return: Словарь со статистикой.
        """
        pass


class AddressRepository(BaseRepository):
    """
    Репозиторий для работы с адресами хранения.

    Отвечает за привязку товаров к местам хранения (ячейкам, полкам).
    """

    @abstractmethod
    def get_by_address(self, address_code: str) -> List[Product]:
        """
        Получить список товаров на указанном адресе.

        :param address_code: Код адреса (например, "А-01-02").
        :return: Список товаров.
        """
        pass

    @abstractmethod
    def get_product_addresses(self, article: str) -> List[Address]:
        """
        Получить все адреса, где хранится указанный товар.

        :param article: Артикульный номер.
        :return: Список объектов Address.
        """
        pass

    @abstractmethod
    def move_product(self, article: str, from_address: str, to_address: str, quantity: int) -> bool:
        """
        Переместить товар с одного адреса на другой.

        :param article: Артикульный номер.
        :param from_address: Адрес источника.
        :param to_address: Адрес назначения.
        :param quantity: Количество для перемещения.
        :return: True если успешно, иначе False.
        """
        pass

    @abstractmethod
    def add_address(self, address: Address) -> bool:
        """
        Добавить новый адрес хранения.

        :param address: Объект адреса.
        :return: True если успешно, иначе False.
        """
        pass

    @abstractmethod
    def delete_address(self, address_code: str) -> bool:
        """
        Удалить адрес хранения.

        :param address_code: Код адреса.
        :return: True если успешно, иначе False.
        """
        pass


class CountRepository(BaseRepository):
    """
    Репозиторий для работы с результатами пересчета (оперативный учет).

    Отличается от InventoryRepository тем, что хранит временные данные
    текущего пересчета без создания полноценного документа.
    """

    @abstractmethod
    def start_session(self, session_id: str) -> bool:
        """
        Начать новую сессию пересчета.

        :param session_id: Уникальный идентификатор сессии.
        :return: True если успешно, иначе False.
        """
        pass

    @abstractmethod
    def add_count(self, session_id: str, item: CountItem) -> bool:
        """
        Добавить результат пересчета в сессию.

        :param session_id: ID сессии.
        :param item: Результат пересчета.
        :return: True если успешно, иначе False.
        """
        pass

    @abstractmethod
    def get_session_counts(self, session_id: str) -> List[CountItem]:
        """
        Получить все результаты пересчета в сессии.

        :param session_id: ID сессии.
        :return: Список результатов.
        """
        pass

    @abstractmethod
    def clear_session(self, session_id: str) -> bool:
        """
        Очистить сессию пересчета.

        :param session_id: ID сессии.
        :return: True если успешно, иначе False.
        """
        pass

    @abstractmethod
    def merge_duplicates(self, session_id: str) -> bool:
        """
        Объединить дубликаты позиций в сессии (суммировать количества).

        :param session_id: ID сессии.
        :return: True если успешно, иначе False.
        """
        pass
