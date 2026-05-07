# modules/config_manager.py

import json
from pathlib import Path
from typing import Any, Dict

class ConfigManager:
    """Менеджер конфигурации приложения"""
    
    DEFAULT_CONFIG = {
        'paths': {
            'default_output_folder': str(Path.home() / "Desktop" / "Stickers"),
            'default_input_folder': str(Path.home() / "Desktop"),
            'database_url': 'https://partsd.hardserver.ru/data/zero_inventory.csv',
            'auto_load_database': True,
            'csv_path': str(Path.home() / "AppData" / "Local" / "StickerMakerV3" / "nomenclature.csv"),
            'address_csv_path': str(Path.home() / "AppData" / "Local" / "StickerMakerV3" / "addresses.csv"),
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
    
    def __init__(self, config_path=None):
        if config_path is None:
            self.config_path = Path.home() / "AppData" / "Local" / "StickerMakerV3" / "config.json"
        else:
            self.config_path = Path(config_path)
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return self._merge_configs(self.DEFAULT_CONFIG, json.load(f))
            except Exception:
                return self.DEFAULT_CONFIG.copy()
        else:
            self.save()
            return self.DEFAULT_CONFIG.copy()
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        for key, value in user.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                default[key] = self._merge_configs(default[key], value)
            else:
                default[key] = value
        return default
    
    def get(self, key_path: str, default=None) -> Any:
        keys, value = key_path.split('.'), self.config
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        keys, data = key_path.split('.'), self.config
        for key in keys[:-1]:
            data = data.setdefault(key, {})
        data[keys[-1]] = value
    
    def save(self) -> bool:
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False