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
            "current_preset": {},  # Пресет по умолчанию для превью стикера
        }
        logger.info("[StubSettingsService] Инициализация")

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Алиас для get(). Получение значения настройки."""
        return self.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._settings[key] = value

    def set_setting(self, key: str, value: Any) -> None:
        """Алиас для set(). Установка значения настройки."""
        self._settings[key] = value
        logger.debug(f"[StubSettingsService] set_setting: {key} = {value}")

    def save(self) -> None:
        logger.info(f"[StubSettingsService] Сохранение: {self._settings}")

    def load(self) -> None:
        logger.info(f"[StubSettingsService] Загрузка: {self._settings}")

    def get_column_config(self) -> Dict[str, Any]:
        """Возвращает конфигурацию колонок очереди."""
        config = self._settings.get("queue_columns", ["article", "article2", "name", "address"])
        order = self._settings.get("column_order", config)
        logger.info(f"[StubSettingsService] get_column_config: columns={config}, order={order}")
        return {"columns": config, "order": order}

    def save_column_config(self, columns: list, order: list) -> None:
        """Сохраняет конфигурацию колонок очереди."""
        self._settings["queue_columns"] = columns
        self._settings["column_order"] = order
        logger.info(f"[StubSettingsService] save_column_config: columns={columns}, order={order}")
