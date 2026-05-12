"""Заглушка сервиса настроек."""

import logging
from typing import Any, Dict

from gui.services.interfaces.settings_service import ISettingsService


logger = logging.getLogger(__name__)


class StubSettingsService(ISettingsService):
    """Заглушка сервиса настроек. Хранит в памяти."""

    def __init__(self) -> None:
        self._settings: Dict[str, Any] = {
            "theme": "System",
            "window_width": 1200,
            "window_height": 800,
            "queue_columns": ["article", "article2", "name", "address"],
            "column_order": ["article", "article2", "name", "address"],
        }
        logger.info("[StubSettingsService] Инициализация")

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._settings[key] = value

    def save(self) -> None:
        logger.info(f"[StubSettingsService] Сохранение: {self._settings}")

    def load(self) -> None:
        logger.info(f"[StubSettingsService] Загрузка: {self._settings}")
