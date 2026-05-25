#!/usr/bin/env python3
"""
ScanHead Combine - Главное приложение.
Точка входа для GUI-каркаса.

Примечание: Приложение работает ТОЛЬКО с реальными базами данных.
Моки удалены как неактуальные. Реальные БД находятся на тестовой машине
и не загружаются в репозиторий ввиду конфиденциальности данных.
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
        StubImageService, StubSettingsService, StubPrinterService, StubInventoryService
    )

    # Используем ТОЛЬКО реальные базы данных
    # Моки удалены как неактуальные. Реальные БД находятся на тестовой машине
    # и соответствуют описанию в data/databases/*/README.md
    logger.info("[Main] Использование реальных баз данных")
    from gui.services.adapters.nomenclature_adapter import NomenclatureAdapter
    from gui.services.adapters.store_adapter import StoreAdapter
    from gui.services.adapters.css_export_adapter import CssExportAdapter
    from gui.services.product_details_service import ProductDetailsService
    
    db_path = config.get("db_paths", {}).get("nomenclature", "data/databases/nomenclature/nomenclature.db")
    nomenclature_adapter = NomenclatureAdapter(db_path)
    
    store_db_path = config.get("db_paths", {}).get("store", "data/databases/store/store.db")
    store_adapter = StoreAdapter(store_db_path)
    
    css_db_path = config.get("db_paths", {}).get("css_export", "data/databases/css_export/css_export.db")
    css_adapter = CssExportAdapter(css_db_path)
    
    # Создаём сервис детальной информации
    details_service = ProductDetailsService(
        nomenclature_adapter=nomenclature_adapter,
        store_adapter=store_adapter,
        css_adapter=css_adapter
    )
    
    container.register(ISearchService, nomenclature_adapter)
    container.register(IProductRepository, store_adapter)
    container.register("product_details_service", details_service)

    container.register(IImageService, StubImageService())
    container.register(ISettingsService, StubSettingsService())
    container.register(IPrinterService, StubPrinterService())
    container.register(IInventoryService, StubInventoryService())

    logger.info("Сервисы зарегистрированы в DI-контейнере")

    root = ctk.CTk()
    root.title("ScanHead Combine")
    
    # Главное окно: максимизированное, но не fullscreen (чтобы избежать проблем с геометрией)
    root.state('zoomed')  # Для Windows - разворачивает на весь экран
    
    # Альтернатива для кроссплатформенности:
    # root.attributes('-fullscreen', False)
    # root.geometry("+0+0")
    # root.state('normal')

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


if __name__ == "__main__":
    main()
