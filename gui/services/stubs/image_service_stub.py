"""Заглушка сервиса изображений."""

import logging
import threading
import time
from typing import Callable, Optional

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

from gui.services.interfaces.image_service import IImageService


logger = logging.getLogger(__name__)


class StubImageService(IImageService):
    """Заглушка сервиса изображений."""

    def __init__(self) -> None:
        self._placeholder: Optional[object] = None
        if PIL_AVAILABLE:
            self._placeholder = Image.new('RGB', (200, 200), color='#CCCCCC')

    def load_image_async(self, url: str, callback: Callable[[Optional[object]], None]) -> None:
        """Эмуляция загрузки изображения."""
        logger.info(f"[StubImageService] Загрузка: {url}")

        def worker() -> None:
            time.sleep(0.2)
            callback(None)

        threading.Thread(target=worker, daemon=True).start()

    def get_placeholder(self) -> object:
        """Возвращает заглушку."""
        if self._placeholder is None and PIL_AVAILABLE:
            self._placeholder = Image.new('RGB', (200, 200), color='#CCCCCC')
        return self._placeholder or object()
