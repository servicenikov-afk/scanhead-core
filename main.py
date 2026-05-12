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
CONFIG_PATH = Path("/workspace/config/app_config.json")


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

    # Инициализация сервисов в зависимости от конфига
    use_mocks = config.get("use_mock_data", False)

    if use_mocks:
        logger.info("[Main] Использование моков для тестовых данных")
        from gui.services.adapters.json_mock_loader import JsonMockLoader
        from gui.services.stubs.search_service_with_mocks import SearchServiceWithMocks
        from gui.services.stubs.product_repo_stub import StubProductRepository
        from gui.services.stubs.image_service_stub import StubImageService
        from gui.services.stubs.settings_service_stub import StubSettingsService
        from gui.services.stubs.printer_service_stub import StubPrinterService

        mock_path = config.get("mock_data_path", "data/mocks")
        mock_loader = JsonMockLoader(mock_path)
        search_service = SearchServiceWithMocks(mock_loader)
    else:
        logger.info("[Main] Использование заглушек без моков")
        from gui.services.stubs.search_service_stub import StubSearchService
        from gui.services.stubs.product_repo_stub import StubProductRepository
        from gui.services.stubs.image_service_stub import StubImageService
        from gui.services.stubs.settings_service_stub import StubSettingsService
        from gui.services.stubs.printer_service_stub import StubPrinterService

        search_service = StubSearchService()

    # Создание DI-контейнера (сервисы)
    services = {
        "search_service": search_service,
        "product_repo": StubProductRepository(),
        "image_service": StubImageService(),
        "settings_service": StubSettingsService(),
        "printer_service": StubPrinterService(),
    }

    logger.info("Сервисы инициализированы")

    # Создание главного окна
    root = ctk.CTk()
    root.title("ScanHead Combine")
    
    # Применение размеров из настроек
    settings = services["settings_service"]
    width = settings.get("window_width", 1200)
    height = settings.get("window_height", 800)
    root.geometry(f"{width}x{height}")

    # Создание MainWindow с DI
    app = MainWindow(root, services=services)
    
    logger.info("Главное окно создано")
    logger.info("Запуск главного цикла...")

    # Запуск цикла
    try:
        root.mainloop()
    except KeyboardInterrupt:
        logger.info("Приложение завершено пользователем")
    finally:
        # Сохранение настроек
        settings.save()
        logger.info("Настройки сохранены")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()
