#!/usr/bin/env python3
"""
ScanHead Combine - Главное приложение.
Точка входа для GUI-каркаса.
"""

import sys
import logging
import json
from pathlib import Path

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


config = load_config()

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

    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    from gui.main_window import MainWindow
    from services.di_container import DIContainer
    from services.interfaces import (
        ISearchService, IProductRepository, IImageService,
        ISettingsService, IPrinterService, IInventoryService
    )
    from services.stubs import (
        StubSearchService, StubProductRepository, StubImageService,
        StubSettingsService, StubPrinterService, StubInventoryService
    )

    use_mocks = config.get("use_mock_data", False)
    
    logger.info(f"[DEBUG] CONFIG_PATH: {CONFIG_PATH}")
    logger.info(f"[DEBUG] use_mock_data: {use_mocks}")

    container = DIContainer()

    if use_mocks:
        logger.info("[Main] Использование моков для тестовых данных")
        from gui.services.adapters.json_mock_loader import JsonMockLoader
        
        mock_path = config.get("mock_data_path", "data/mocks")
        mock_loader = JsonMockLoader(mock_path)
        
        search_service = SearchServiceWithMocks(mock_loader)
        container.register(ISearchService, search_service)
        container.register(IProductRepository, StubProductRepository())
    else:
        logger.info("[Main] Использование реальных баз данных")
        from gui.services.adapters.nomenclature_adapter import NomenclatureAdapter
        from gui.services.adapters.store_adapter import StoreAdapter
        
        db_path = config.get("db_paths", {}).get("nomenclature", "nomenclature.db")
        search_service = NomenclatureAdapter(db_path)
        
        store_db_path = config.get("db_paths", {}).get("store", "store.db")
        store_adapter = StoreAdapter(store_db_path)
        
        container.register(ISearchService, search_service)
        container.register(IProductRepository, store_adapter)

    container.register(IImageService, StubImageService())
    container.register(ISettingsService, StubSettingsService())
    container.register(IPrinterService, StubPrinterService())
    container.register(IInventoryService, StubInventoryService())

    logger.info("Сервисы зарегистрированы в DI-контейнере")

    root = ctk.CTk()
    root.title("ScanHead Combine")
    
    settings = container.get(ISettingsService)
    width = settings.get_setting("window_width", 1200)
    height = settings.get_setting("window_height", 800)
    root.geometry(f"{width}x{height}")

    app = MainWindow(root, di_container=container)
    app.pack(fill="both", expand=True)
    
    logger.info("Главное окно создано")
    logger.info("Запуск главного цикла...")

    try:
        root.mainloop()
    except KeyboardInterrupt:
        logger.info("Приложение завершено пользователем")
    finally:
        settings_service = container.get(ISettingsService)
        if hasattr(settings_service, 'save'):
            settings_service.save()
        logger.info("Настройки сохранены")
        logger.info("=" * 60)


class SearchServiceWithMocks:
    """Адаптер поиска с использованием JsonMockLoader."""
    
    def __init__(self, mock_loader):
        self._mock_loader = mock_loader
        self._logger = logging.getLogger(__name__)
    
    def search_async(self, query: str, callback) -> None:
        """Асинхронный поиск по мокам."""
        import threading
        import time
        
        def worker():
            time.sleep(0.1)
            results = []
            if query:
                query_lower = query.lower()
                for product in self._mock_loader.load_products():
                    if (query_lower in (product.article or "").lower() or 
                        query_lower in (product.name or "").lower()):
                        results.append(product)
            callback(results)
        
        threading.Thread(target=worker, daemon=True).start()
    
    def get_product_by_id(self, product_id: int):
        """Получение товара по ID (в моках не реализовано)."""
        self._logger.warning("get_product_by_id не реализован для моков")
        return None


if __name__ == "__main__":
    main()
