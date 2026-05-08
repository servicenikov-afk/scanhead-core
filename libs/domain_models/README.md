# Domain Models Module

Доменные модели для складских операций.

## Установка

```python
from libs.domain_models import Product, CountItem, InventoryItem
```

## Использование

### Product - Модель товара

```python
product = Product(
    article="12345",
    name="Товар 1",
    barcodes=["4601234567890", "4609876543210"],
    address="A-01-01"
)

# Проверка соответствия кода
if product.matches_article_or_barcode("12345"):
    print("Найден по артикулу")

if product.matches_article_or_barcode("4601234567890"):
    print("Найден по штрих-коду")
```

### CountItem - Позиция подсчета

```python
item = CountItem(
    article="12345",
    name="Товар 1",
    quantity=10.0,
    address="A-01-01"
)

# Добавление количества
item.add(5)      # quantity = 15.0
item.add(2.5)    # quantity = 17.5
```

### InventoryItem - Позиция инвентаризации

```python
item = InventoryItem(
    article="12345",
    name="Товар 1",
    expected=100.0,
    actual=95.0,
    address="A-01-01"
)

# Свойства
print(item.diff)        # -5.0
print(item.diff_abs)    # 5.0
print(item.status)      # "⚠ Недосдача: 5.00"
print(item.status_color) # "orange"

# Методы
item.add(5)           # actual = 100.0
item.set_actual(110)  # actual = 110.0
```

## Особенности

- Все модели реализованы как dataclasses для простоты и читаемости
- InventoryItem предоставляет вычисляемые свойства для анализа расхождений
- Поддержка Optional полей для гибкости использования

## Зависимости

Нет внешних зависимостей. Только стандартная библиотека Python.
