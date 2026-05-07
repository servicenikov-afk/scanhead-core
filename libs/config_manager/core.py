"""
Ядро модуля ConfigManager.

Предоставляет базовый класс для управления конфигурацией приложения.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """
    Менеджер конфигурации приложения.
    
    Позволяет загружать, сохранять и манипулировать JSON-конфигурацией
    с поддержкой дефолтных значений и рекурсивного слияния.
    
    Attributes:
        config_path: Путь к файлу конфигурации.
        config: Словарь с текущей конфигурацией.
        DEFAULT_CONFIG: Класс-переменная с дефолтной конфигурацией.
    
    Example:
        >>> config = ConfigManager()
        >>> config.get('paths.default_output_folder')
        '/home/user/Desktop/Stickers'
        >>> config.set('behavior.skip_errors', False)
        >>> config.save()
    """
    
    DEFAULT_CONFIG: Dict[str, Any] = {
        'paths': {
            'default_output_folder': '',
            'default_input_folder': '',
            'database_url': '',
            'auto_load_database': True,
            'csv_path': '',
            'address_csv_path': '',
        },
        'sticker': {
            'width_mm': 40,
            'height_mm': 20,
            'orientation': 'portrait',
            'border': False,
            'background_color': '#FFFFFF',
            'dpi': 300
        },
        'elements': {
            'article': {
                'enabled': True,
                'font_size': 7,
                'bold': True,
                'align': 'center',
                'color': '#000000',
                'offset_x': 0,
                'offset_y': -20,
                'font_family': 'Arial'
            },
            'address': {
                'enabled': False,
                'font_size': 6,
                'bold': False,
                'italic': False,
                'border': True,
                'background_color': '#FFFFFF',
                'align': 'right',
                'color': '#606060',
                'offset_x': 0,
                'offset_y': 0,
                'font_family': 'Arial'
            },
            'name': {
                'enabled': True,
                'font_size': 8,
                'bold': False,
                'italic': False,
                'align': 'left',
                'color': '#000000',
                'max_lines': 3,
                'offset_x': 0,
                'offset_y': 0,
                'font_family': 'Arial'
            },
            'quantity': {
                'enabled': False,
                'font_size': 6,
                'bold': False,
                'italic': True,
                'align': 'center',
                'color': '#666666',
                'offset_x': 0,
                'offset_y': 0,
                'font_family': 'Arial'
            }
        },
        'barcode': {
            'enabled': True,
            'type': 'auto',
            'size_mm': 10,
            'code128_width_mm': 25,
            'code128_height_mm': 10,
            'show_text': False,
            'text_size': 3,
            'text_offset_x': 0,
            'text_offset_y': 0,
            'position': 'top_right',
            'border': False,
            'offset_x': 0,
            'offset_y': 0,
            'auto_rules': {
                'fallback_to_qr': True,
                'skip_if_invalid': False
            }
        },
        'behavior': {
            'confirm_before_process': True,
            'overwrite_files': True,
            'open_after_process': False,
            'skip_errors': True
        },
        'fonts': {
            'default_font': 'Arial',
            'fallback_fonts': ['Calibri', 'Tahoma', 'Verdana']
        }
    }
    
    def __init__(self, config_path: Optional[str] = None, default_config: Optional[Dict[str, Any]] = None):
        """
        Инициализация ConfigManager.
        
        Args:
            config_path: Путь к файлу конфигурации. Если None, используется путь по умолчанию.
            default_config: Кастомная дефолтная конфигурация. Если None, используется DEFAULT_CONFIG.
        """
        if config_path is None:
            self.config_path = Path.home() / "AppData" / "Local" / "StickerMakerV3" / "config.json"
        else:
            self.config_path = Path(config_path)
        
        self._default_config = default_config if default_config is not None else self.DEFAULT_CONFIG
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Загрузка конфигурации из файла с рекурсивным слиянием с дефолтными значениями.
        
        Returns:
            Словарь с конфигурацией.
        """
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return self._merge_configs(
                        self._deep_copy(self._default_config), 
                        json.load(f)
                    )
            except Exception:
                return self._deep_copy(self._default_config)
        else:
            self.save()
            return self._deep_copy(self._default_config)
    
    @staticmethod
    def _deep_copy(obj: Any) -> Any:
        """Глубокое копирование объекта (словаря/списка)."""
        if isinstance(obj, dict):
            return {k: ConfigManager._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [ConfigManager._deep_copy(item) for item in obj]
        else:
            return obj
    
    @staticmethod
    def _merge_configs(default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Рекурсивное слияние пользовательской конфигурации с дефолтной.
        
        Args:
            default: Дефолтная конфигурация.
            user: Пользовательская конфигурация.
        
        Returns:
            Слитая конфигурация.
        """
        result = ConfigManager._deep_copy(default)
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigManager._merge_configs(result[key], value)
            else:
                result[key] = ConfigManager._deep_copy(value)
        return result
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Получение значения по точечному пути.
        
        Args:
            key_path: Путь к значению в формате 'section.subsection.key'.
            default: Значение по умолчанию, если ключ не найден.
        
        Returns:
            Значение конфигурации или default.
        
        Example:
            >>> config.get('sticker.width_mm')
            40
            >>> config.get('nonexistent.key', 'fallback')
            'fallback'
        """
        keys = key_path.split('.')
        value = self.config
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Установка значения по точечному пути.
        
        Args:
            key_path: Путь к значению в формате 'section.subsection.key'.
            value: Новое значение.
        
        Example:
            >>> config.set('behavior.skip_errors', False)
        """
        keys = key_path.split('.')
        data = self.config
        for key in keys[:-1]:
            data = data.setdefault(key, {})
        data[keys[-1]] = value
    
    def save(self) -> bool:
        """
        Сохранение текущей конфигурации в файл.
        
        Returns:
            True если сохранение успешно, иначе False.
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def reload(self) -> None:
        """Перезагрузка конфигурации из файла."""
        self.config = self._load_config()
