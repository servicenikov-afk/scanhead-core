# Data Exporters Module

Модуль для экспорта данных в различные форматы (Excel, CSV).

## Установка

```python
from libs.data_exporters import ExcelExporter, CSVExporter
```

## Использование

### Экспорт в Excel

```python
from pathlib import Path

data = [
    {'Артикул': '123', 'Наименование': 'Товар 1', 'Количество': 10},
    {'Артикул': '456', 'Наименование': 'Товар 2', 'Количество': 20.5}
]

filepath = Path('output.xlsx')
if ExcelExporter.export(data, filepath):
    print("Экспорт успешен")
```

### Экспорт в CSV

```python
from pathlib import Path

data = [
    {'Артикул': '123', 'Наименование': 'Товар 1', 'Количество': 10},
    {'Артикул': '456', 'Наименование': 'Товар 2', 'Количество': 20.5}
]

filepath = Path('output.csv')
if CSVExporter.export(data, filepath):
    print("Экспорт успешен")
```

## Особенности

- **Excel**: Автоматическое форматирование числовых колонок (колонки содержащие слова "остаток", "разница", "количество")
- **CSV**: Кодировка UTF-8 с BOM для корректного отображения кириллицы в Excel

## Зависимости

- pandas (для Excel)
- openpyxl (для Excel)
- csv (стандартная библиотека, для CSV)
