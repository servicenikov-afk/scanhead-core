# Inventory Parser

Модуль для парсинга файлов инвентаризации в формате Excel.

## Возможности

- Автоматическое определение заголовков колонок
- Поддержка различных форматов Excel-файлов
- Извлечение артикулов из нескольких полей
- Парсинг количеств в различных форматах
- Определение адресов хранения
- Пропуск служебных строк (итоги, пустые строки)

## Установка

Модуль является частью ScanHead Core и не требует дополнительной установки.

## Использование

```python
from libs.inventory_parser import InventoryParser

parser = InventoryParser()
positions = parser.parse_inventory_file("path/to/inventory.xlsx")

for position in positions:
    print(f"Артикул: {position['article']}")
    print(f"Наименование: {position['name']}")
    print(f"Ожидаемое количество: {position['expected']}")
    print(f"Адрес: {position['address']}")
    print(f"Строка источника: {position['source_row']}")
    print("---")
```

## Формат возвращаемых данных

Каждая позиция представляет собой словарь со следующими полями:

- `article` (str): Артикул товара
- `name` (str): Наименование товара
- `expected` (float): Ожидаемое количество
- `address` (str): Адрес хранения
- `source_row` (int): Номер строки в исходном файле

## Зависимости

- pandas
- openpyxl (для чтения .xlsx файлов)

## Логирование

Модуль использует стандартный Python logging. Для настройки логирования:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('libs.inventory_parser')
```

## Примеры форматов файлов

Модуль поддерживает файлы с различными названиями колонок:
- "Номенклатура.Артикул 2" / "Артикул 2"
- "Артикул" / "Номенклатура.Артикул"
- "Номенклатура" (для наименования)
- "Конечный остаток" / "Конечныйостаток"
- "Адрес"
