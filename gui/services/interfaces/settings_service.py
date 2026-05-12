"""Интерфейс сервиса настроек."""

from abc import ABC, abstractmethod
from typing import Any


class ISettingsService(ABC):
    """Интерфейс сервиса управления настройками приложения."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Получение значения настройки."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Установка значения настройки."""
        pass

    @abstractmethod
    def save(self) -> None:
        """Сохранение настроек на диск."""
        pass

    @abstractmethod
    def load(self) -> None:
        """Загрузка настроек с диска."""
        pass
