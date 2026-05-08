"""
Модуль инициализации и настройки приложения (Bootstrap).

Предоставляет единую точку входа для настройки:
- Логгера
- Обработчика глобальных исключений
- Путей и конфигурации
- Валидации окружения
"""

import logging
import sys
import traceback
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from datetime import datetime


class BootstrapConfig:
    """Конфигурация для инициализации приложения."""
    
    def __init__(
        self,
        app_name: str = "ScanHead App",
        log_level: int = logging.INFO,
        log_file: Optional[Path] = None,
        log_format: Optional[str] = None,
        enable_exception_handler: bool = True,
        exception_callback: Optional[Callable[[Exception], None]] = None,
    ):
        """
        Инициализация конфигурации bootstrap.
        
        Args:
            app_name: Имя приложения (используется в логах и заголовках)
            log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Путь к файлу логов (если None, логи только в консоль)
            log_format: Формат строки логов (по умолчанию стандартный)
            enable_exception_handler: Включить перехват глобальных исключений
            exception_callback: Callback для обработки неперехваченных исключений
        """
        self.app_name = app_name
        self.log_level = log_level
        self.log_file = log_file
        self.log_format = log_format or (
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.enable_exception_handler = enable_exception_handler
        self.exception_callback = exception_callback


class Bootstrap:
    """
    Менеджер инициализации приложения.
    
    Пример использования:
        config = BootstrapConfig(
            app_name="My Inventory App",
            log_level=logging.DEBUG,
            log_file=Path("app.log"),
        )
        
        bootstrap = Bootstrap(config)
        bootstrap.run()
        
        logger = logging.getLogger(__name__)
        logger.info("Приложение запущено")
    """
    
    def __init__(self, config: BootstrapConfig):
        self.config = config
        self._logger: Optional[logging.Logger] = None
        self._initialized = False
    
    def run(self) -> None:
        """
        Выполнить полную инициализацию приложения.
        
        Вызывает все необходимые методы настройки в правильном порядке.
        """
        if self._initialized:
            self._logger.warning("Приложение уже инициализировано")
            return
        
        self._setup_logging()
        
        if self.config.enable_exception_handler:
            self._setup_exception_handler()
        
        self._validate_environment()
        
        self._initialized = True
        
        if self._logger:
            self._logger.info(f"Приложение '{self.config.app_name}' инициализировано")
    
    def _setup_logging(self) -> None:
        """Настроить систему логирования."""
        # Создаем logger для приложения
        self._logger = logging.getLogger(self.config.app_name)
        self._logger.setLevel(self.config.log_level)
        
        # Очищаем существующие handlers (чтобы не дублировать при перезапуске)
        self._logger.handlers.clear()
        
        # Создаем formatter
        formatter = logging.Formatter(self.config.log_format)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.config.log_level)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)
        
        # File handler (если указан файл)
        if self.config.log_file:
            try:
                # Создаем директорию для лога, если её нет
                self.config.log_file.parent.mkdir(parents=True, exist_ok=True)
                
                file_handler = logging.FileHandler(self.config.log_file, encoding='utf-8')
                file_handler.setLevel(self.config.log_level)
                file_handler.setFormatter(formatter)
                self._logger.addHandler(file_handler)
                
                self._logger.debug(f"Логирование в файл: {self.config.log_file}")
            except Exception as e:
                print(f"Warning: Не удалось создать файл логов {self.config.log_file}: {e}", file=sys.stderr)
        
        # Устанавливаем как default logger для root
        logging.basicConfig(
            level=self.config.log_level,
            format=self.config.log_format,
            handlers=[console_handler] + (
                [logging.FileHandler(self.config.log_file, encoding='utf-8')] 
                if self.config.log_file else []
            ),
            force=True  # Перезаписываем существующую конфигурацию
        )
    
    def _setup_exception_handler(self) -> None:
        """Настроить перехват глобальных исключений."""
        
        def global_exception_handler(exc_type, exc_value, exc_traceback):
            """Обработчик неперехваченных исключений."""
            # Игнорируем KeyboardInterrupt (Ctrl+C)
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            # Формируем сообщение об ошибке
            error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            
            # Логируем ошибку
            if self._logger:
                self._logger.critical(f"Неперехваченное исключение:\n{error_msg}")
            else:
                print(f"CRITICAL ERROR:\n{error_msg}", file=sys.stderr)
            
            # Вызываем callback, если указан
            if self.config.exception_callback:
                try:
                    self.config.exception_callback(exc_value)
                except Exception as callback_error:
                    if self._logger:
                        self._logger.error(f"Ошибка в exception callback: {callback_error}")
        
        # Устанавливаем обработчик
        sys.excepthook = global_exception_handler
        
        if self._logger:
            self._logger.debug("Глобальный обработчик исключений установлен")
    
    def _validate_environment(self) -> None:
        """Проверить окружение на соответствие требованиям."""
        warnings = []
        errors = []
        
        # Проверка версии Python
        if sys.version_info < (3, 8):
            errors.append(f"Требуется Python 3.8+, текущая версия: {sys.version}")
        
        # Проверка прав на запись в рабочую директорию
        working_dir = Path.cwd()
        if not os.access(working_dir, os.W_OK):
            warnings.append(f"Нет прав на запись в рабочую директорию: {working_dir}")
        
        # Проверка переменных окружения (можно расширить)
        required_env_vars = []  # Добавить при необходимости
        for var in required_env_vars:
            if var not in os.environ:
                warnings.append(f"Переменная окружения '{var}' не установлена")
        
        # Вывод результатов проверки
        if warnings and self._logger:
            for warning in warnings:
                self._logger.warning(f"Предупреждение окружения: {warning}")
        
        if errors:
            for error in errors:
                if self._logger:
                    self._logger.critical(f"Критическая ошибка окружения: {error}")
                else:
                    print(f"CRITICAL: {error}", file=sys.stderr)
            raise EnvironmentError("\n".join(errors))
        
        if self._logger:
            self._logger.debug("Проверка окружения пройдена")
    
    @property
    def logger(self) -> Optional[logging.Logger]:
        """Получить logger приложения."""
        return self._logger
    
    @property
    def is_initialized(self) -> bool:
        """Проверить, инициализировано ли приложение."""
        return self._initialized


# Утилиты для быстрой инициализации

def quick_bootstrap(
    app_name: str = "ScanHead App",
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
) -> Bootstrap:
    """
    Быстрая инициализация приложения с настройками по умолчанию.
    
    Args:
        app_name: Имя приложения
        log_level: Уровень логирования
        log_file: Путь к файлу логов (опционально)
        
    Returns:
        Настроенный экземпляр Bootstrap
    """
    config = BootstrapConfig(
        app_name=app_name,
        log_level=log_level,
        log_file=Path(log_file) if log_file else None,
    )
    
    bootstrap = Bootstrap(config)
    bootstrap.run()
    
    return bootstrap


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Получить logger для модуля.
    
    Args:
        name: Имя logger (обычно __name__ модуля)
        
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(name)
    return logging.getLogger()


# Импорт для совместимости
import os

__all__ = [
    "Bootstrap",
    "BootstrapConfig",
    "quick_bootstrap",
    "get_logger",
]
