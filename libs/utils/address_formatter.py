"""
AddressFormatter - Сервис форматирования адресов хранения.

Управляет парсингом, форматированием и валидацией адресов
на основе конфигурации формата.
"""

import json
from typing import List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class AddressFormatConfig:
    """Конфигурация формата адреса.
    
    Attributes:
        enabled: Включено ли использование форматированного адреса
        separator: Разделитель между уровнями (-, /, _, . или свой)
        custom_separator: Пользовательский разделитель (если separator == 'custom')
        levels: Список названий уровней (например, ["Блок", "Стеллаж", "Секция"])
        display_mode: Режим отображения ('compact' или 'with_labels')
    """
    enabled: bool = False
    separator: str = "-"
    custom_separator: str = ""
    levels: List[str] = field(default_factory=lambda: ["Блок", "Стеллаж", "Секция"])
    display_mode: str = "compact"  # 'compact' или 'with_labels'
    
    def get_actual_separator(self) -> str:
        """Получить актуальный разделитель."""
        if self.separator == "custom":
            return self.custom_separator or "-"
        return self.separator
    
    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {
            "enabled": self.enabled,
            "separator": self.separator,
            "custom_separator": self.custom_separator,
            "levels": self.levels,
            "display_mode": self.display_mode
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AddressFormatConfig':
        """Десериализация из словаря."""
        return cls(
            enabled=data.get("enabled", False),
            separator=data.get("separator", "-"),
            custom_separator=data.get("custom_separator", ""),
            levels=data.get("levels", ["Блок", "Стеллаж", "Секция"]),
            display_mode=data.get("display_mode", "compact")
        )


class AddressFormatter:
    """
    Сервис форматирования адресов хранения.
    
    Предоставляет методы для:
    - Парсинга строки адреса в список значений
    - Форматирования списка значений в строку
    - Валидации адреса на соответствие конфигурации
    - Проверки совместимости существующих адресов
    """
    
    def __init__(self, config: Optional[AddressFormatConfig] = None):
        """
        Инициализация форматтера.
        
        Args:
            config: Конфигурация формата. Если None, используется дефолтная.
        """
        self._config = config or AddressFormatConfig()
    
    @property
    def config(self) -> AddressFormatConfig:
        """Получение текущей конфигурации."""
        return self._config
    
    @config.setter
    def config(self, value: AddressFormatConfig) -> None:
        """Установка новой конфигурации."""
        self._config = value
    
    def parse(self, address_str: str) -> List[str]:
        """
        Разбивает строку адреса на список значений по разделителю.
        
        Args:
            address_str: Строка адреса (например, "A-01-05")
            
        Returns:
            Список значений (например, ["A", "01", "05"])
        """
        if not address_str:
            return []
        
        separator = self._config.get_actual_separator()
        if not separator:
            return [address_str]
        
        return address_str.split(separator)
    
    def format(self, values_list: List[str]) -> str:
        """
        Собирает строку адреса из списка значений.
        
        Args:
            values_list: Список значений (например, ["A", "01", "05"])
            
        Returns:
            Отформатированная строка (например, "A-01-05")
        """
        if not values_list:
            return ""
        
        separator = self._config.get_actual_separator()
        return separator.join(str(v) for v in values_list)
    
    def format_with_labels(self, values_list: List[str]) -> List[Tuple[str, str]]:
        """
        Форматирует адрес как список пар (название_уровня, значение).
        
        Args:
            values_list: Список значений
            
        Returns:
            Список кортежей (label, value), например:
            [("Блок", "A"), ("Стеллаж", "01"), ("Секция", "05")]
        """
        result = []
        for i, value in enumerate(values_list):
            if i < len(self._config.levels):
                label = self._config.levels[i]
            else:
                label = f"Уровень {i + 1}"
            result.append((label, value))
        return result
    
    def validate(self, values_list: List[str]) -> Tuple[bool, str]:
        """
        Проверяет, соответствует ли список значений конфигурации.
        
        Args:
            values_list: Список значений для проверки
            
        Returns:
            Кортеж (is_valid, message):
            - is_valid: True если валидно
            - message: Сообщение об ошибке или успехе
        """
        if not self._config.enabled:
            return True, "Форматирование отключено"
        
        expected_count = len(self._config.levels)
        actual_count = len(values_list)
        
        if actual_count != expected_count:
            return (
                False, 
                f"Ожидалось {expected_count} уровней, получено {actual_count}"
            )
        
        # Проверка на пустые значения (опционально можно разрешить)
        empty_levels = [
            self._config.levels[i] 
            for i, v in enumerate(values_list) 
            if not v.strip() and i < len(self._config.levels)
        ]
        
        if empty_levels:
            return False, f"Пустые значения: {', '.join(empty_levels)}"
        
        return True, "Валидация пройдена"
    
    def is_compatible(self, address_str: str) -> Tuple[bool, str]:
        """
        Проверяет, можно ли распарсить существующий адрес по текущим настройкам.
        
        Args:
            address_str: Строка адреса из БД
            
        Returns:
            Кортеж (is_compatible, message):
            - is_compatible: True если адрес совместим
            - message: Пояснение
        """
        if not self._config.enabled:
            return True, "Форматирование отключено"
        
        if not address_str:
            return False, "Пустой адрес"
        
        parsed = self.parse(address_str)
        expected_count = len(self._config.levels)
        actual_count = len(parsed)
        
        if actual_count != expected_count:
            return (
                False, 
                f"Адрес содержит {actual_count} уровней, ожидается {expected_count}"
            )
        
        return True, "Адрес совместим с форматом"
    
    def parse_json_to_list(self, json_str: str) -> List[str]:
        """
        Парсит JSON-строку из БД в список адресов.
        
        Args:
            json_str: JSON-строка (например, '["A-01-05", "B-02-03"]')
            
        Returns:
            Список строк адресов
        """
        if not json_str:
            return []
        
        try:
            data = json.loads(json_str)
            if isinstance(data, list):
                return [str(item) for item in data]
            elif isinstance(data, str):
                return [data]
            return []
        except json.JSONDecodeError:
            # Если не JSON, пробуем как простую строку
            return [json_str]
    
    def format_list_to_json(self, addresses: List[str]) -> str:
        """
        Форматирует список адресов в JSON-строку для записи в БД.
        
        Args:
            addresses: Список строк адресов
            
        Returns:
            JSON-строка
        """
        return json.dumps(addresses, ensure_ascii=False)
    
    def get_level_names(self) -> List[str]:
        """Получить список названий уровней."""
        return self._config.levels.copy()
    
    def add_level(self, name: str) -> None:
        """Добавить новый уровень."""
        if len(self._config.levels) >= 10:
            raise ValueError("Максимум 10 уровней")
        if name.strip():
            self._config.levels.append(name.strip())
    
    def remove_level(self, index: int) -> None:
        """Удалить уровень по индексу."""
        if 0 <= index < len(self._config.levels):
            self._config.levels.pop(index)
    
    def update_level(self, index: int, new_name: str) -> None:
        """Обновить название уровня."""
        if 0 <= index < len(self._config.levels) and new_name.strip():
            self._config.levels[index] = new_name.strip()
