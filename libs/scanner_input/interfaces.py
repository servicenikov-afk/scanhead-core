"""
Абстрактный интерфейс для поставщиков штрих-кодов.

Определяет контракт, который должны реализовывать все типы сканеров:
- HID-сканеры
- Камеры
- Файловые источники
- Симуляторы
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional


class ScannerProvider(ABC):
    """
    Базовый класс для всех источников штрих-кодов.
    
    Атрибуты:
        _callback: Функция обратного вызова, вызываемая при успешном сканировании.
        _is_active: Флаг активности сканера.
    """

    def __init__(self):
        self._callback: Optional[Callable[[str], None]] = None
        self._is_active: bool = False

    @abstractmethod
    def start_listening(self) -> None:
        """
        Запуск прослушивания источника штрих-кодов.
        
        Должен быть реализован в наследниках.
        """
        pass

    @abstractmethod
    def stop_listening(self) -> None:
        """
        Остановка прослушивания источника штрих-кодов.
        
        Должен быть реализован в наследниках.
        """
        pass

    def set_callback(self, callback: Callable[[str], None]) -> None:
        """
        Установка функции обратного вызова для обработанных штрих-кодов.
        
        Args:
            callback: Функция, принимающая строку со штрих-кодом.
        """
        self._callback = callback

    def _notify_callback(self, code: str) -> None:
        """
        Уведомление подписчика о новом штрих-коде.
        
        Args:
            code: Обработанный штрих-код.
        """
        if self._callback and self._is_active:
            self._callback(code)

    @property
    def is_active(self) -> bool:
        """Проверка активности сканера."""
        return self._is_active
