"""
Точка входа приложения ScanHead Combine.
Инициализирует логгер, DI-контейнер и запускает главное окно.
"""

import sys
import logging

# Инициализация Bootstrap ДО импорта остальных модулей
from libs.core.bootstrap import Bootstrap

# Инициализируем логгер через Bootstrap
Bootstrap.quick_bootstrap(level=logging.INFO)
logger = logging.getLogger(__name__)

# Теперь импортируем остальные модули
import customtkinter as ctk
from services.di_container import DIContainer
from gui.main_window import MainWindow


def main():
    """Главная функция приложения."""
    logger.info("=" * 60)
    logger.info("Запуск приложения ScanHead Combine")
    logger.info("=" * 60)
    
    # Создаём DI-контейнер и регистрируем заглушки
    logger.info("Инициализация DI-контейнера...")
    container = DIContainer()
    container.register_default_services()
    logger.info("DI-контейнер готов")
    
    # Создаём главное приложение CTk
    logger.info("Создание главного окна...")
    app = ctk.CTk()
    app.title("ScanHead Combine")
    app.geometry("1200x800")
    
    # Настраиваем тему
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    # Создаём главное окно с внедрением зависимостей
    main_window = MainWindow(app, container)
    main_window.pack(fill="both", expand=True)
    
    # Запускаем главный цикл
    logger.info("Запуск главного цикла приложения...")
    app.mainloop()
    
    logger.info("Приложение завершено")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"Критическая ошибка приложения: {e}")
        sys.exit(1)
