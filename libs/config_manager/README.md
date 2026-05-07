# Config Manager

Универсальный модуль управления конфигурацией приложения.

## Версия
0.1.0

## Описание

Модуль предоставляет класс `ConfigManager` для работы с JSON-конфигурацией:
- Загрузка и сохранение конфигов
- Рекурсивное слияние с дефолтными значениями
- Получение/установка значений по точечному пути (например, `paths.default_output_folder`)
- Поддержка кастомных дефолтных конфигураций

## Схема трафика данных

```
DEFAULT_CONFIG → загрузка из файла (если есть) → слияние → self.config → get()/set() → save()
```

## Установка

Скопируйте папку `config_manager` в ваш проект или подключите как submodule:

```bash
git submodule add https://github.com/servicenikov-afk/module-extractor.git libs/config_manager
```

## Использование

### Базовое использование

```python
from config_manager import ConfigManager

# Инициализация с путем по умолчанию
config = ConfigManager()

# Получение значения
output_folder = config.get('paths.default_output_folder')

# Установка значения
config.set('behavior.skip_errors', False)

# Сохранение изменений
config.save()
```

### Кастомный путь к конфигу

```python
config = ConfigManager(config_path='/path/to/custom/config.json')
```

### Кастомная дефолтная конфигурация

```python
my_default = {
    'app': {
        'name': 'MyApp',
        'version': '1.0.0'
    }
}
config = ConfigManager(default_config=my_default)
```

### Перезагрузка конфигурации

```python
config.reload()  # Перечитать из файла
```

## API

### Класс `ConfigManager`

#### Конструктор
```python
ConfigManager(config_path: Optional[str] = None, default_config: Optional[Dict] = None)
```

#### Методы

| Метод | Описание |
|-------|----------|
| `get(key_path, default=None)` | Получить значение по точечному пути |
| `set(key_path, value)` | Установить значение по точечному пути |
| `save()` | Сохранить конфигурацию в файл |
| `reload()` | Перезагрузить конфигурацию из файла |

#### Атрибуты

| Атрибут | Описание |
|---------|----------|
| `config_path` | Путь к файлу конфигурации |
| `config` | Текущий словарь конфигурации |
| `DEFAULT_CONFIG` | Дефолтная конфигурация (класс-переменная) |

## Структура дефолтной конфигурации

```json
{
  "paths": {
    "default_output_folder": "",
    "default_input_folder": "",
    "database_url": "",
    "auto_load_database": true,
    "csv_path": "",
    "address_csv_path": ""
  },
  "sticker": {
    "width_mm": 40,
    "height_mm": 20,
    "orientation": "portrait",
    "border": false,
    "background_color": "#FFFFFF",
    "dpi": 300
  },
  "elements": {...},
  "barcode": {...},
  "behavior": {
    "confirm_before_process": true,
    "overwrite_files": true,
    "open_after_process": false,
    "skip_errors": true
  },
  "fonts": {
    "default_font": "Arial",
    "fallback_fonts": ["Calibri", "Tahoma", "Verdana"]
  }
}
```

## Лицензия

MIT
