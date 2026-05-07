# Data Validator Module

Версия: **0.1.0**

## Назначение
Централизованная валидация данных с поддержкой кастомных правил, сбором всех ошибок и различными уровнями серьезности.

## Установка
```bash
from libs.data_validator import DataValidator, ValidationRule, ValidationResult, ValidationSeverity
```

## Использование

### Базовая валидация
```python
from libs.data_validator import DataValidator, ValidationRule

validator = DataValidator()

# Добавление правил
validator.add_rule(ValidationRule(
    name="article_required",
    field="article",
    validator=lambda x: bool(x and x.strip()),
    error_message="Артикул обязателен"
))

validator.add_rule(ValidationRule(
    name="barcode_length",
    field="barcode",
    validator=lambda x: len(x) == 13 if x else True,
    error_message="Штрих-код должен содержать 13 цифр",
    skip_if_empty=True
))

# Проверка данных
data = {"article": "  ", "barcode": "123"}
report = validator.validate(data)

if not report.is_valid:
    for error in report.errors:
        print(f"{error.field}: {error.message}")
```

### Уровни серьезности
```python
from libs.data_validator import ValidationSeverity

# Предупреждение (не блокирует сохранение)
validator.add_rule(ValidationRule(
    name="name_length_warning",
    field="name",
    validator=lambda x: len(x) > 5 if x else True,
    error_message="Наименование очень короткое",
    severity=ValidationSeverity.WARNING
))

# Критическая ошибка
validator.add_rule(ValidationRule(
    name="article_format_critical",
    field="article",
    validator=lambda x: x.isalnum(),
    error_message="Артикул содержит недопустимые символы",
    severity=ValidationSeverity.CRITICAL
))
```

### Кастомные валидаторы
```python
def check_article_barcode_consistency(data):
    """Проверить соответствие артикула и штрих-кода."""
    results = []
    
    article = data.get("article", "")
    barcode = data.get("barcode", "")
    
    # Пример: если артикул начинается с "IMPORT", штрих-код обязателен
    if article.startswith("IMPORT") and not barcode:
        results.append(ValidationResult.fail(
            field="barcode",
            message="Для импортных товаров штрих-код обязателен",
            severity=ValidationSeverity.ERROR
        ))
    
    return results

validator.add_custom_validator("article_barcode_check", check_article_barcode_consistency)
```

### Валидация с исключением
```python
try:
    validator.validate_or_raise(data, exception_class=ValueError)
except ValueError as e:
    print(f"Ошибка валидации: {e}")
```

## API

### Классы

#### `DataValidator`
Основной класс валидатора.

Методы:
- `add_rule(rule)` - добавить правило
- `remove_rule(name)` - удалить правило
- `add_custom_validator(name, func)` - добавить кастомный валидатор
- `validate(data)` - проверить данные, вернуть ValidationReport
- `validate_or_raise(data, exception_class)` - проверить и выбросить исключение

#### `ValidationRule`
Правило валидации.

Параметры:
- `name` - имя правила
- `field` - поле для проверки
- `validator` - функция-валидатор (принимает значение, возвращает bool)
- `error_message` - сообщение об ошибке
- `severity` - уровень серьезности (ERROR, WARNING, CRITICAL, INFO)
- `skip_if_empty` - пропускать пустые значения

#### `ValidationResult`
Результат одной проверки.

Свойства:
- `field` - проверенное поле
- `is_valid` - результат проверки
- `message` - сообщение
- `severity` - уровень серьезности
- `value` - проверенное значение

#### `ValidationReport`
Отчет о валидации.

Свойства:
- `is_valid` - пройдена ли валидация (нет ERROR/CRITICAL)
- `errors` - список всех ошибок
- `warnings` - список предупреждений
- `critical_errors` - критические ошибки

Методы:
- `get_errors_by_field(field)` - ошибки конкретного поля
- `summary()` - краткая сводка

### Уровни серьезности (`ValidationSeverity`)

| Уровень | Описание | Влияет на is_valid |
|---------|----------|-------------------|
| INFO | Информационное сообщение | Нет |
| WARNING | Предупреждение | Нет |
| ERROR | Ошибка | Да |
| CRITICAL | Критическая ошибка | Да |

## Пример комплексной валидации

```python
from libs.data_validator import (
    DataValidator, ValidationRule, ValidationResult, 
    ValidationSeverity
)

def create_product_validator():
    validator = DataValidator()
    
    # Обязательные поля
    validator.add_rule(ValidationRule(
        name="article_required",
        field="article",
        validator=lambda x: bool(x and x.strip()),
        error_message="Артикул обязателен"
    ))
    
    # Формат артикула
    validator.add_rule(ValidationRule(
        name="article_format",
        field="article",
        validator=lambda x: all(c.isalnum() or c in '-_' for c in x) if x else True,
        error_message="Артикул может содержать только буквы, цифры, дефис и подчеркивание"
    ))
    
    # Длина наименования (предупреждение)
    validator.add_rule(ValidationRule(
        name="name_min_length",
        field="name_original",
        validator=lambda x: len(x) >= 3 if x else True,
        error_message="Наименование слишком короткое",
        severity=ValidationSeverity.WARNING
    ))
    
    # Кастомная проверка
    def check_tags(data):
        results = []
        tags = data.get("tags", [])
        if len(tags) > 10:
            results.append(ValidationResult.fail(
                field="tags",
                message="Слишком много тегов (максимум 10)",
                severity=ValidationSeverity.WARNING
            ))
        return results
    
    validator.add_custom_validator("tags_limit", check_tags)
    
    return validator

# Использование
validator = create_product_validator()
data = {
    "article": "PROD-123",
    "name_original": "Test",
    "tags": ["tag1", "tag2"]
}

report = validator.validate(data)
print(report.summary())

if report.warnings:
    print("Предупреждения:")
    for w in report.warnings:
        print(f"  - {w.message}")
```

## План доработки (v0.2.0)

- [ ] Добавить встроенные валидаторы (email, URL, телефон)
- [ ] Поддержка цепочек валидаторов (pipeline)
- [ ] Валидация вложенных структур данных
- [ ] Интеграция с моделями данных (DataRecord)
- [ ] Локализация сообщений об ошибках

## Лицензия
Часть проекта module-extractor
