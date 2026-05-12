"""Интерфейс сервиса изображений."""

from abc import ABC, abstractmethod
from typing import Callable, Optional

try:
    from PIL import Image
except ImportError:
    Image = None


class IImageService(ABC):
    """Интерфейс сервиса загрузки изображений."""

    @abstractmethod
    def load_image_async(self, url: str, callback: Callable[[Optional[object]], None]) -> None:
        """Асинхронная загрузка изображения."""
        pass

    @abstractmethod
    def get_placeholder(self) -> object:
        """Получение изображения-заглушки."""
        pass
