# DB Manager Module

Версия: **0.1.0**

## Назначение
Универсальный менеджер для работы с различными источниками данных (SQLite, PostgreSQL, CSV, XML, XLS/XLSX) с возможностью миграции между ними.

## Установка
```bash
# Модуль является частью проекта
from libs.db_manager import DBManager, DataSourceType, DataRecord
```

## Использование

### Подключение к SQLite
```python
from libs.db_manager import DBManager, DataSourceType, SQLiteDataSource, DataRecord

manager = DBManager()

# Регистрация источника
sqlite_source = SQLiteDataSource("data.db")
manager.register_source(DataSourceType.SQLITE, sqlite_source)

# Активация источника
if manager.set_active_source(DataSourceType.SQLITE):
    print("Подключено к SQLite")
```

### CRUD операции
```python
# Создание записи
record = DataRecord(
    article="ABC123",
    barcode="4601234567890",
    name_original="Наименование на оригинальном языке",
    name_sticker="Сокращенное наименование",
    tags=["model_x", "category_y"]
)

# Запись
manager.write(record)

# Чтение всех записей
all_records = manager.read_all()

# Чтение по ID
record = manager.read_by_id(1)

# Обновление
record.name_sticker = "Новое название"
manager.update(record)

# Удаление
manager.delete(1)
```

### Расширенные поля
Модель `DataRecord` поддерживает:
- `article` - канонический артикул
- `barcode` - штрих-код
- `name_original` - наименование на оригинальном языке
- `name_sticker` - наименование для стикеров
- `article_old` - старый артикул
- `articles_alternative` - список альтернативных артикулов
- `tags` - теги (модели оборудования, категории)
- `metadata` - дополнительные метаданные (dict)

### Миграции между источниками
```python
# Чтение из CSV
csv_source = CSVDataSource("import.csv")
manager.register_source(DataSourceType.CSV, csv_source)
manager.set_active_source(DataSourceType.CSV)
records = manager.read_all()

# Запись в SQLite
manager.set_active_source(DataSourceType.SQLITE)
for record in records:
    manager.write(record)
```

## API

### Классы

#### `DBManager`
Основной класс управления источниками данных.

Методы:
- `register_source(source_type, source)` - зарегистрировать источник
- `set_active_source(source_type)` - установить активный источник
- `read_all()` - прочитать все записи
- `read_by_id(id)` - прочитать по ID
- `write(record)` - записать запись
- `update(record)` - обновить запись
- `delete(id)` - удалить запись
- `execute_query(query, params)` - выполнить SQL запрос

#### `DataRecord`
Модель данных с расширенными полями.

#### `DataSourceType`
Перечисление типов источников: `SQLITE`, `POSTGRES`, `CSV`, `XML`, `XLSX`, `XLS`, `SQL`.

#### Источники данных
- `SQLiteDataSource` - ✅ Реализовано
- `PostgresDataSource` - ⏳ В разработке
- `CSVDataSource` - ⏳ В разработке
- `XMLDataSource` - ⏳ В разработке
- `XLSXDataSource` - ⏳ В разработке

## План доработки (v0.2.0)

- [ ] Реализовать `CSVDataSource` (чтение/запись CSV)
- [ ] Реализовать `PostgresDataSource` (подключение через psycopg2)
- [ ] Реализовать `XMLDataSource` (парсинг XML)
- [ ] Реализовать `XLSXDataSource` (чтение Excel через openpyxl)
- [ ] Добавить систему миграций схемы БД
- [ ] Добавить пул соединений для PostgreSQL
- [ ] Реализовать транзакции

## Известные проблемы

1. Только SQLite полностью реализован
2. Остальные источники данных выбрасывают `NotImplementedError`
3. Нет автоматической миграции схемы при изменении модели данных

## Пример полной работы

```python
from libs.db_manager import (
    DBManager, DataSourceType, 
    SQLiteDataSource, DataRecord
)

# Инициализация
manager = DBManager()
source = SQLiteDataSource("warehouse.db")
manager.register_source(DataSourceType.SQLITE, source)
manager.set_active_source(DataSourceType.SQLITE)

# Добавление товара
item = DataRecord(
    article="WH-001",
    barcode="4601234567890",
    name_original="Widget Model X",
    name_sticker="Widget X",
    article_old="OLD-001",
    tags=["widget", "model_x"]
)
item.add_alternative_article("ALT-WH-001")
item.add_tag("new_arrival")

manager.write(item)

# Поиск и обновление
found = manager.read_by_id(item.id)
if found:
    found.name_sticker = "Widget X v2"
    manager.update(found)

# Закрытие
manager.close_all()
```

## Лицензия
Часть проекта module-extractor
