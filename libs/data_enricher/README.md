# Data Enricher Module

Версия: **0.1.0**

## Назначение
Преобразование "сырых" данных в полноценные бизнес-объекты с автоматическим обогащением полей.

## Установка
```bash
from libs.data_enricher import DataEnricher, EnrichmentResult
```

## Использование

### Базовое обогащение
```python
from libs.data_enricher import DataEnricher

enricher = DataEnricher()

# Добавление процессоров
enricher.add_processor("normalize_article", normalize_article_processor)
enricher.add_processor("generate_sticker_name", generate_sticker_name_processor)

# Сырые данные
raw_data = {
    "article": "  abc-123 ",
    "name_original": "Очень длинное наименование товара которое нужно сократить"
}

# Обогащение
result = enricher.enrich(raw_data)

if result.success:
    record = result.record
    print(f"Артикул: {record.article}")
    print(f"Название для стикера: {record.name_sticker}")
    print(f"Обогащено полей: {result.enriched_fields}")
else:
    print(f"Ошибки: {result.errors}")
```

### Пакетное обогащение
```python
raw_data_list = [
    {"article": " item-1 ", "name_original": "Товар 1"},
    {"article": " item-2 ", "name_original": "Товар 2 с длинным названием"},
]

results = enricher.enrich_batch(raw_data_list)

for i, result in enumerate(results):
    if result.success:
        print(f"Запись {i}: {result.record.article}")
    else:
        print(f"Запись {i}: Ошибка - {result.errors}")
```

### Кастомные процессоры
```python
def add_category_tag(raw_data, record):
    """Добавить тег категории на основе артикула."""
    if record.article.startswith("ELEC"):
        record.tags.append("electronics")
    elif record.article.startswith("MECH"):
        record.tags.append("mechanical")
    return record

enricher.add_processor("category_tagger", add_category_tag)
```

### Валидация перед обогащением
```python
def has_required_fields(raw_data):
    return bool(raw_data.get("article"))

enricher.add_validator("required_fields", has_required_fields)
```

## Стандартные процессоры

Модуль включает готовые процессоры:

| Процессор | Назначение |
|-----------|------------|
| `normalize_article_processor` | Нормализация артикула (через `article_normalizer`) |
| `generate_sticker_name_processor` | Генерация сокращенного названия для стикеров |
| `extract_tags_from_metadata_processor` | Извлечение тегов из метаданных |
| `set_default_values_processor` | Установка дат создания/обновления |

## API

### Классы

#### `DataEnricher`
Основной класс обогащения данных.

Методы:
- `add_processor(name, func)` - добавить процессор
- `remove_processor(name)` - удалить процессор
- `add_validator(name, func)` - добавить валидатор
- `enrich(raw_data)` - обогатить одну запись
- `enrich_batch(raw_data_list)` - обогатить пакет записей

#### `EnrichmentResult`
Результат обогащения.

Свойства:
- `success` - успешно ли обогащение
- `record` - обогащенная запись (DataRecord)
- `errors` - список ошибок
- `warnings` - список предупреждений
- `enriched_fields` - список обработанных процессоров

Методы класса:
- `ok(record, enriched_fields)` - создать успешный результат
- `fail(errors, warnings)` - создать результат с ошибкой

## Пример полного пайплайна

```python
from libs.data_enricher import (
    DataEnricher, EnrichmentResult,
    normalize_article_processor,
    generate_sticker_name_processor,
    set_default_values_processor
)
from libs.data_validator import DataValidator, ValidationRule

# Создание валидатора
validator = DataValidator()
validator.add_rule(ValidationRule(
    name="article_required",
    field="article",
    validator=lambda x: bool(x and x.strip()),
    error_message="Артикул обязателен"
))

# Создание обогатителя
enricher = DataEnricher()

# Добавление валидатора сырых данных
enricher.add_validator(
    "article_check",
    lambda data: validator.validate(data).is_valid
)

# Добавление процессоров
enricher.add_processor("normalize_article", normalize_article_processor)
enricher.add_processor("sticker_name", generate_sticker_name_processor)
enricher.add_processor("defaults", set_default_values_processor)

# Обработка
raw_data = {
    "article": " prod-123 ",
    "name_original": "Профессиональный инструмент для работы",
    "barcode": "4601234567890"
}

result = enricher.enrich(raw_data)

if result.success:
    record = result.record
    print(f"Готово: {record.article} -> {record.name_sticker}")
    print(f"Теги: {record.tags}")
    print(f"Создано: {record.created_at}")
else:
    print(f"Не удалось: {result.errors}")
```

## Интеграция с другими модулями

### С `db_manager`
```python
from libs.db_manager import DBManager, DataSourceType, SQLiteDataSource

manager = DBManager()
source = SQLiteDataSource("data.db")
manager.register_source(DataSourceType.SQLITE, source)
manager.set_active_source(DataSourceType.SQLITE)

# Обогащение и сохранение
result = enricher.enrich(raw_data)
if result.success:
    manager.write(result.record)
```

### С `data_validator`
```python
from libs.data_validator import DataValidator

validator = DataValidator()
# ... добавить правила ...

report = validator.validate(result.record.to_dict())
if not report.is_valid:
    for error in report.errors:
        print(f"{error.field}: {error.message}")
```

## План доработки (v0.2.0)

- [ ] Добавить процессор для автозаполнения альтернативных артикулов
- [ ] Реализовать процессор для определения категории по названию
- [ ] Добавить кэширование результатов обогащения
- [ ] Поддержка асинхронного обогащения для больших объемов
- [ ] Интеграция с внешними API для получения дополнительных данных

## Известные проблемы

1. Процессор `generate_sticker_name_processor` использует простую логику сокращения
2. Нет поддержки многоязычных наименований
3. Отсутствует приоритизация процессоров (выполняются в порядке добавления)

## Лицензия
Часть проекта module-extractor
