# Article Normalizer Module

Версия: **0.1.0**

## Назначение
Модуль для нормализации, валидации и обработки артикулов товаров.

## Установка
```bash
# Модуль является частью проекта и не требует отдельной установки
from libs.article_normalizer import ArticleNormalizer
```

## Использование

### Базовая нормализация
```python
normalizer = ArticleNormalizer()
article = normalizer.normalize(" 123-abc ")
# Результат: "123ABC"
```

### Валидация
```python
is_valid = normalizer.validate("123ABC", min_length=3, max_length=20)
# Результат: True
```

### Конфигурация
```python
# Отключить удаление спецсимволов
normalizer = ArticleNormalizer(remove_special_chars=False)

# Не приводить к верхнему регистру
normalizer = ArticleNormalizer(to_upper=False)
```

## API

### Класс `ArticleNormalizer`

#### Методы
- `normalize(article: str) -> str` - Нормализовать артикул
- `validate(article: str, min_length: int, max_length: int) -> bool` - Проверить валидность
- `extract_prefix(article: str) -> Optional[str]` - Извлечь префикс (TODO)
- `extract_base(article: str) -> str` - Извлечь базовую часть

#### Параметры инициализации
- `remove_special_chars: bool = True` - Удалять специальные символы
- `to_upper: bool = True` - Приводить к верхнему регистру

## Известные проблемы и план доработки

### Текущие ограничения
1. **Отсутствует поддержка префиксов**: Метод `extract_prefix` выбрасывает `NotImplementedError`
2. **Простая логика очистки**: Не учитываются специфические форматы артикулов разных производителей
3. **Нет кэширования**: При массовой обработке одинаковые артикулы обрабатываются повторно

### План доработки (v0.2.0)
- [ ] Реализовать определение и извлечение префиксов
- [ ] Добавить поддержку пользовательских правил нормализации
- [ ] Внедрить кэширование результатов
- [ ] Добавить поддержку различных форматов (EAN, UPC, внутренние артикулы)

### Баги, требующие исправления
- Артикулы с кириллицей могут обрабатываться некорректно при `to_upper=True`
- Дефисы внутри артикула могут быть как разделителями, так и частью кода

## Тестирование
```python
def test_normalize():
    normalizer = ArticleNormalizer()
    assert normalizer.normalize(" 123-abc ") == "123ABC"
    assert normalizer.normalize("") == ""
    assert normalizer.validate("123") is True
    assert normalizer.validate("") is False
```

## Лицензия
Часть проекта module-extractor
