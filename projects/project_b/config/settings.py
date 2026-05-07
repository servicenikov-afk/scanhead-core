# config/settings.py
import json
import shutil
import logging
from pathlib import Path
from typing import Any, Dict

logging.basicConfig(level=logging.DEBUG)

class Settings:
    """Управление настройками приложения"""
    
    DEFAULT_CONFIG = {
        'paths': {
            'nomenclature_csv': str(Path.home() / "AppData" / "Local" / "InventoryApp" / "nomenclature.csv"),
            'addresses_csv': str(Path.home() / "AppData" / "Local" / "InventoryApp" / "addresses.csv"),
            'export_folder': str(Path.home() / "Desktop" / "InventoryReports"),
            'sticker_maker_path': str(Path.home() / "AppData" / "Local" / "StickerMakerV3"),
        },
        'scanner': {
            'auto_add': True,
            'timeout_ms': 50,
        },
        'behavior': {
            'confirm_clear': True,
            'auto_focus': True,
            'focus_timeout': 3.0,
            'auto_copy_from_sticker_maker': True,
            'auto_fix_layout': True,
        }
    }
    
    def __init__(self, config_path: Path = None):
        if config_path is None:
            self.config_path = Path.home() / "AppData" / "Local" / "InventoryApp" / "config.json"
        else:
            self.config_path = Path(config_path)
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()
        
        # Автоматически копируем файлы из StickerMaker если нужно
        if self.get('behavior.auto_copy_from_sticker_maker', True):
            self._copy_from_sticker_maker()
    
    def _load_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    config_copy = self._deep_copy(self.DEFAULT_CONFIG)
                    return self._merge_configs(config_copy, user_config)
            except Exception as e:
                print(f"Ошибка загрузки конфигурации: {e}")
                return self._deep_copy(self.DEFAULT_CONFIG)
        else:
            self._save_config()
            return self._deep_copy(self.DEFAULT_CONFIG)
    
    def _deep_copy(self, obj):
        """Глубокое копирование словаря"""
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(v) for v in obj]
        else:
            return obj
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Рекурсивно объединяет конфигурации"""
        for key, value in user.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                default[key] = self._merge_configs(default[key], value)
            else:
                default[key] = value
        return default
    
    def _save_config(self):
        """Сохраняет конфигурацию"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
    
    def _copy_from_sticker_maker(self):
        """Копирует файлы из StickerMaker если они есть"""
        sticker_path = Path(self.get('paths.sticker_maker_path'))
        
        if not sticker_path.exists():
            return
        
        nomenclature_source = sticker_path / "nomenclature.csv"
        addresses_source = sticker_path / "addresses.csv"
        
        nomenclature_target = Path(self.get('paths.nomenclature_csv'))
        addresses_target = Path(self.get('paths.addresses_csv'))
        
        # Копируем nomenclature.csv
        if nomenclature_source.exists():
            if not nomenclature_target.exists():
                try:
                    shutil.copy2(nomenclature_source, nomenclature_target)
                    print(f"[OK] Скопирован nomenclature.csv из StickerMaker")
                except Exception as e:
                    print(f"[WARN] Не удалось скопировать nomenclature.csv: {e}")
            else:
                print(f"[INFO] nomenclature.csv уже существует, пропускаем")
        else:
            print(f"[INFO] Файл nomenclature.csv не найден в StickerMaker")
        
        # Копируем addresses.csv
        if addresses_source.exists():
            if not addresses_target.exists():
                try:
                    shutil.copy2(addresses_source, addresses_target)
                    print(f"[OK] Скопирован addresses.csv из StickerMaker")
                except Exception as e:
                    print(f"[WARN] Не удалось скопировать addresses.csv: {e}")
            else:
                print(f"[INFO] addresses.csv уже существует, пропускаем")
        else:
            print(f"[INFO] Файл addresses.csv не найден в StickerMaker")
    
    def get(self, key_path: str, default=None) -> Any:
        """Получает значение по пути"""
        keys = key_path.split('.')
        value = self.config
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """Устанавливает значение по пути"""
        keys = key_path.split('.')
        config = self.config
        for key in keys[:-1]:
            config = config.setdefault(key, {})
        config[keys[-1]] = value
        self._save_config()
    
    def get_nomenclature_path(self) -> Path:
        """Возвращает путь к файлу номенклатуры"""
        return Path(self.get('paths.nomenclature_csv'))
    
    def get_addresses_path(self) -> Path:
        """Возвращает путь к файлу адресов"""
        return Path(self.get('paths.addresses_csv'))
    
    def get_export_folder(self) -> Path:
        """Возвращает папку для экспорта"""
        return Path(self.get('paths.export_folder'))
    
    def is_auto_add(self) -> bool:
        """Возвращает, включен ли авторежим"""
        return self.get('scanner.auto_add', True)