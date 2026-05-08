# Config Module (libs/config)

Управление конфигурацией и пресетами приложения.

## Состав

### preset_manager.py
Менеджер пресетов печати и настроек пользователя.

**Возможности:**
- Сохранение/загрузка пресетов в JSON
- Валидация структуры пресета
- Поддержка пользовательских метаданных

**Пример использования:**
```python
from libs.config import PresetManager

manager = PresetManager("presets.json")

# Сохранить пресет
manager.save_preset(
    name="A4_Labels",
    settings={"paper_size": "A4", "columns": 3, "font_size": 12}
)

# Загрузить пресет
preset = manager.load_preset("A4_Labels")
```

## Зависимости
- Стандартная библиотека Python (json, pathlib, typing)

## Примечания
- Файл пресетов хранится в формате JSON
- Подходит для хранения любых настроек приложения
