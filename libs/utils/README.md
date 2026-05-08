# Utils Module (libs/utils)

Набор вспомогательных утилит общего назначения.

## Состав

### fuzzy_search.py
Модуль нечеткого поиска и фильтрации списков.

**Функции:**
- `filter_items(items, query, mode='fuzzy')` — фильтрация списка по запросу
- Поддерживаемые режимы:
  - `exact` — точное совпадение
  - `contains` — содержит подстроку
  - `startswith` — начинается с подстроки
  - `fuzzy` — нечеткий поиск (эвристика)
  - `regex` — регулярное выражение

**Пример использования:**
```python
from libs.utils import filter_items

products = ["iPhone 13", "Samsung Galaxy", "iPad Pro"]
result = filter_items(products, "iphone", mode="fuzzy")
# ["iPhone 13"]
```

### file_naming.py
Генератор имен файлов по шаблонам.

**Класс `FileNameGenerator`:**
Поддерживает переменные в шаблоне:
- `{date}` — дата (YYYY-MM-DD)
- `{time}` — время (HH-MM-SS)
- `{type}` — тип файла
- `{counter}` — автоинкрементный счетчик
- `{custom}` — пользовательские переменные

**Пример использования:**
```python
from libs.utils import FileNameGenerator

gen = FileNameGenerator()
name = gen.generate("inventory_{date}_{type}", type="report")
# "inventory_2024-05-08_report"
```

## Зависимости
- Стандартная библиотека Python (re, datetime, typing, pathlib)

## Примечания
- Модули не зависят от GUI и БД
- Подходит для использования в любых типах приложений
