#!/usr/bin/env python3
"""
ScanHead Combine - Главное приложение.
Точка входа для GUI-каркаса.
"""

import sys
import logging
import json
from pathlib import Path

# Добавляем workspace в path
sys.path.insert(0, '/workspace')

# Импорт конфигурации
# Используем относительный путь от текущего файла для кроссплатформенности
CONFIG_PATH = Path(__file__).parent / "config" / "app_config.json"


def load_config() -> dict:
    """Загрузка конфигурации приложения."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "app_name": "ScanHead Combine",
        "use_mock_data": False,
        "mock_data_path": "data/mocks",
        "log_level": "INFO",
    }


# Загрузка конфигурации
config = load_config()

# Инициализация логгирования через Bootstrap
from libs.core import quick_bootstrap

quick_bootstrap(
    app_name=config.get("app_name", "ScanHead Combine"),
    log_level=getattr(logging, config.get("log_level", "INFO")),
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Точка входа приложения."""
    logger.info("=" * 60)
    logger.info("ScanHead Combine - Запуск приложения")
    logger.info("=" * 60)

    # Импорт зависимостей GUI
    try:
        import customtkinter as ctk
    except ImportError:
        logger.error("customtkinter не установлен. Выполните: pip install customtkinter")
        sys.exit(1)

    try:
        from PIL import ImageTk, Image
        PIL_AVAILABLE = True
    except ImportError:
        PIL_AVAILABLE = False
        logger.warning("PIL/Pillow не установлен. Изображения будут недоступны.")

    # Настройка CTk
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    # Импорт сервисов
    from gui.main_window import MainWindow
    from services.di_container import DIContainer
    from services.interfaces import ISearchService, IProductRepository

    # Инициализация сервисов в зависимости от конфига
    use_mocks = config.get("use_mock_data", False)
    
    # Отладка: выводим путь и значение
    logger.info(f"[DEBUG] CONFIG_PATH: {CONFIG_PATH}")
    logger.info(f"[DEBUG] CONFIG_PATH exists: {CONFIG_PATH.exists()}")
    logger.info(f"[DEBUG] Full config content: {config}")
    logger.info(f"[DEBUG] use_mock_data value: {use_mocks} (type: {type(use_mocks)})")

    # Создаём DI-контейнер
    container = DIContainer()

    if use_mocks:
        logger.info("[Main] Использование моков для тестовых данных")
        from gui.services.adapters.json_mock_loader import JsonMockLoader
        from services.stubs import StubSearchService, StubProductRepository
        
        # Создаём SearchServiceWithMocks как адаптер над StubSearchService + JsonMockLoader
        mock_path = config.get("mock_data_path", "data/mocks")
        mock_loader = JsonMockLoader(mock_path)
        
        # Регистрируем сервисы с моками
        search_service = SearchServiceWithMocks(mock_loader)
        container.register(ISearchService, search_service)
        container.register(IProductRepository, StubProductRepository())
    else:
        logger.info("[Main] Использование реальных баз данных")
        from gui.services.adapters.nomenclature_adapter import NomenclatureAdapter
        from gui.services.adapters.store_adapter import StoreAdapter
        
        # Инициализация адаптера номенклатуры с правильным путём
        db_path = config.get("db_paths", {}).get("nomenclature", "nomenclature.db")
        search_service = NomenclatureAdapter(db_path)
        
        # Инициализация адаптера хранилища
        store_db_path = config.get("db_paths", {}).get("store", "store.db")
        store_adapter = StoreAdapter(store_db_path)
        
        # Регистрируем реальные сервисы
        container.register(ISearchService, search_service)
        container.register(IProductRepository, store_adapter)

    # Регистрируем остальные сервисы (заглушки по умолчанию)
    from services.stubs import StubImageService, StubSettingsService, StubPrinterService, StubInventoryService
    from services.interfaces import IImageService, ISettingsService, IPrinterService, IInventoryService
    
    container.register(IImageService, StubImageService())
    container.register(ISettingsService, StubSettingsService())
    container.register(IPrinterService, StubPrinterService())
    container.register(IInventoryService, StubInventoryService())

    logger.info("Сервисы инициализированы и зарегистрированы в DI-контейнере")

    # Создание главного окна
    root = ctk.CTk()
    root.title("ScanHead Combine")
    
    # Применение размеров из настроек
    settings = container.get(ISettingsService)
    width = settings.get_setting("window_width", 1200)
    height = settings.get_setting("window_height", 800)
    root.geometry(f"{width}x{height}")

    # Передаём DI-контейнер в MainWindow
    app = MainWindow(root, di_container=container)
    app.pack(fill="both", expand=True)
    
    logger.info("Главное окно создано")
    logger.info("Запуск главного цикла...")

    # Запуск цикла
    try:
        root.mainloop()
    except KeyboardInterrupt:
        logger.info("Приложение завершено пользователем")
    finally:
        # Сохранение настроек
        settings_service = container.get(ISettingsService)
        settings_service.save()
        logger.info("Настройки сохранены")
        logger.info("=" * 60)


class SearchServiceWithMocks:
    """
    Адаптер поиска, использующий JsonMockLoader для тестовых данных.
    Реализует интерфейс ISearchService.
    """
    
    def __init__(self, mock_loader: JsonMockLoader):
        self._mock_loader = mock_loader
        self._logger = logging.getLogger(__name__)
    
    def search_async(self, query: str, callback) -> None:
        """Асинхронный поиск по мокам."""
        import threading
        import time
        
        def worker():
            time.sleep(0.1)  # Имитация задержки
            results = []
            if query:
                for product in self._mock_loader.load_products():
                    if (query.lower() in (product.article or "").lower() or 
                        query.lower() in (product.name or "").lower()):
                        results.append(product)
            callback(results)
        
        threading.Thread(target=worker, daemon=True).start()
    
    def get_product_by_id(self, product_id: int):
        """Получение товара по ID (в моках не реализовано)."""
        self._logger.warning("get_product_by_id не реализован для моков")
        return None


if __name__ == "__main__":
    main()
