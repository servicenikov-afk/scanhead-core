#!/usr/bin/env python3
"""
ScanHead Combine - Главное приложение.
Точка входа для GUI-каркаса.
"""

import sys
import logging

# Добавляем workspace в path
sys.path.insert(0, '/workspace')

# Инициализация логгирования через Bootstrap
from libs.core import quick_bootstrap

quick_bootstrap(app_name="ScanHead Combine", log_level=logging.INFO)

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

    # Импорт сервисов-заглушек
    from gui.services.stubs.search_service_stub import StubSearchService
    from gui.services.stubs.product_repo_stub import StubProductRepository
    from gui.services.stubs.image_service_stub import StubImageService
    from gui.services.stubs.settings_service_stub import StubSettingsService
    from gui.services.stubs.printer_service_stub import StubPrinterService

    # Импорт главного окна
    from gui.main_window import MainWindow

    # Создание DI-контейнера (сервисы)
    services = {
        "search_service": StubSearchService(),
        "product_repo": StubProductRepository(),
        "image_service": StubImageService(),
        "settings_service": StubSettingsService(),
        "printer_service": StubPrinterService(),
    }

    logger.info("Сервисы инициализированы (заглушки)")

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
