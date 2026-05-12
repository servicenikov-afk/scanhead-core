"""
DI-контейнер для управления зависимостями.
Централизованная регистрация и получение сервисов.
"""

import logging
from typing import Dict, Type, Any, Optional

from services.interfaces import (
    ISearchService,
    IProductRepository,
    IImageService,
    IPrinterService,
    ISettingsService,
    IInventoryService,
)
from services.stubs import (
    StubSearchService,
    StubProductRepository,
    StubImageService,
    StubPrinterService,
    StubSettingsService,
    StubInventoryService,
)

logger = logging.getLogger(__name__)


class DIContainer:
    """
    Контейнер внедрения зависимостей (Dependency Injection).
    
    Пример использования:
        container = DIContainer()
        container.register_default_services()  # Регистрируем заглушки
        
        search_service = container.get(ISearchService)
        printer_service = container.get(IPrinterService)
    """
    
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        logger.info("[DIContainer] Инициализация контейнера зависимостей")
    
    def register(self, interface: Type, implementation: Any) -> None:
        """
        Регистрация сервиса.
        
        :param interface: Интерфейс (абстрактный класс)
        :param implementation: Реализация сервиса
        """
        self._services[interface] = implementation
        logger.debug(f"[DIContainer] Зарегистрирован сервис: {interface.__name__}")
    
    def get(self, interface: Type) -> Any:
        """
        Получение сервиса по интерфейсу.
        
        :param interface: Интерфейс для поиска
        :return: Реализация сервиса
        :raises KeyError: Если сервис не зарегистрирован
        """
        if interface not in self._services:
            raise KeyError(f"Сервис {interface.__name__} не зарегистрирован")
        return self._services[interface]
    
    def has(self, interface: Type) -> bool:
        """Проверка наличия зарегистрированного сервиса."""
        return interface in self._services
    
    def register_default_services(self) -> None:
        """
        Регистрация всех заглушек по умолчанию.
        Используется для разработки GUI без реальной бизнес-логики.
        """
        logger.info("[DIContainer] Регистрация заглушек сервисов по умолчанию")
        
        self.register(ISearchService, StubSearchService())
        self.register(IProductRepository, StubProductRepository())
        self.register(IImageService, StubImageService())
        self.register(IPrinterService, StubPrinterService())
        self.register(ISettingsService, StubSettingsService())
        self.register(IInventoryService, StubInventoryService())
        
        logger.info("[DIContainer] Все заглушки сервисов зарегистрированы")
    
    def register_real_services(self, config: dict) -> None:
        """
        Регистрация реальных сервисов из libs/.
        
        :param config: Конфигурация для инициализации сервисов
        (путь к БД, настройки сканера и т.д.)
        
        TODO: Реализовать при подключении реальной бизнес-логики
        """
        logger.warning("[DIContainer] register_real_services ещё не реализован")
        # Здесь будет код создания реальных сервисов:
        # from libs.repository.sqlite_product_repository import SQLiteProductRepository
        # from libs.scanner_input import HidScanner
        # ...
        pass
