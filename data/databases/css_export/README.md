# CSS Export Database - Coffee Machine Spare Parts Catalog

## 📦 Описание

Единая база данных запасных частей для кофемашин Franke, собранная из 19 файлов CSS Export.  
Содержит **24 678 записей** о совместимости деталей с различными моделями, их расположении и применении.

**Расположение БД:** `/data/databases/css_export/css_export.db`

## 🗂️ Структура таблицы `spare_parts`

| Колонка | Тип | Описание | Пример |
|---------|-----|----------|--------|
| `product_model` | TEXT | Модель кофемашины | `Mytico III / Vario (FCS4080)` |
| `position` | TEXT | Позиция в спецификации | `552.0000.048` |
| `art_no` | TEXT | **Артикул детали** (ключевое поле) | `560.0000.048` |
| `name` | TEXT | Наименование детали | `Einschraub-Verbinder 1/4 x 3/8` |
| `usage_path` | TEXT | Полный путь использования | `Option >> Water tank External / Flojet pump` |
| `category1` | TEXT | Уровень 1 иерархии | `Option` |
| `category2` | TEXT | Уровень 2 иерархии | `Water tank External / Flojet pump` |
| `category3` | TEXT | Уровень 3 иерархии (самый детальный) | `NULL` |
| `production_date_from` | TEXT | Начало производства (если указано) | `03. December 2025` |
| `production_date_to` | TEXT | Конец производства (если указано) | `02. December 2025` |
| `serial_from` | TEXT | Серийный номер ОТ | `3400000384220` |
| `serial_to` | TEXT | Серийный номер ДО | `3400000384219` |

## 🔍 Примеры SQL-запросов

### 1. Поиск детали по артикулу

```sql
-- Полная информация о детали для всех моделей
SELECT * FROM spare_parts 
WHERE art_no = '560.0001.513';
```

### 2. Для каких моделей подходит деталь

```sql
SELECT DISTINCT product_model, name, usage_path 
FROM spare_parts 
WHERE art_no = '560.0002.240';
```

### 3. Все детали конкретной модели

```sql
SELECT art_no, name, category1, category2 
FROM spare_parts 
WHERE product_model LIKE '%Mytico III%'
ORDER BY art_no;
```

### 4. Где используется деталь (по категориям)

```sql
SELECT product_model, name, category1, category2, category3
FROM spare_parts 
WHERE art_no = '560.0002.240'
ORDER BY product_model;
```

### 5. Детали в определённой категории

```sql
-- Все клапаны (Valves)
SELECT product_model, art_no, name 
FROM spare_parts 
WHERE category3 = 'Valves'
LIMIT 50;
```

### 6. Опции и аксессуары

```sql
-- Все детали для опции "Water tank External"
SELECT art_no, name, product_model 
FROM spare_parts 
WHERE usage_path LIKE '%Water tank External%';
```

### 7. Статистика по моделям

```sql
-- Количество деталей на модель
SELECT product_model, COUNT(*) as parts_count
FROM spare_parts 
GROUP BY product_model 
ORDER BY parts_count DESC;
```

### 8. Поиск по дате производства

```sql
-- Детали, которые действуют с определённой даты
SELECT art_no, name, production_date_from, serial_from
FROM spare_parts 
WHERE production_date_from IS NOT NULL;
```

### 9. Уникальные артикулы (без дублирования по моделям)

```sql
SELECT DISTINCT art_no, name, COUNT(*) as models_count
FROM spare_parts 
GROUP BY art_no 
ORDER BY models_count DESC
LIMIT 20;
```

### 10. Полнотекстовый поиск (если создан FTS-индекс)

```sql
-- Поиск по названию детали
SELECT art_no, name, product_model 
FROM spare_parts 
WHERE name LIKE '%pump%';
```

### Python + sqlite3

```python
import sqlite3

conn = sqlite3.connect('data/databases/css_export/css_export.db')
cursor = conn.cursor()

# Поиск по артикулу
cursor.execute("SELECT * FROM spare_parts WHERE art_no = ?", ('560.0000.048',))
rows = cursor.fetchall()

for row in rows:
    print(f"Модель: {row[0]}, Название: {row[3]}")

conn.close()
```

### Экспорт в Excel

```python
import pandas as pd
import sqlite3

conn = sqlite3.connect('data/databases/css_export/css_export.db')
df = pd.read_sql_query("SELECT * FROM spare_parts", conn)
df.to_excel("css_export_catalog.xlsx", index=False)
conn.close()
```

## 📊 Модели в базе данных

| Модель | Количество записей |
|--------|-------------------|
| A600 (FCS4043) | 2 762 |
| A800 (FCS4050) | 2 365 |
| A1000 (FCS4050) | 1 826 |
| Spectra S | 1 717 |
| SB1200 (FCS4074) | 1 570 |
| FM series (FCS4026) | 1 559 |
| Evolution | 1 557 |
| Evolution Plus | 1 507 |
| A400 (FCS4060) | 1 595 |
| Spectra S (FCS4041) | 1 399 |
| A300 (FCS4070) | 1 016 |
| Mytico III / Vario (FCS4080) | 1 045 |
| S700 (FCS4067) | 1 005 |
| A200 (FCS4039) | 907 |
| Pura | 796 |
| Spectra X | 766 |
| Mytico II / Due (FCS4080) | 708 |
| Spectra X-XL | 566 |
| Water treatment | 12 |

## 🔧 Создание дополнительных индексов

Для ускорения поиска:

```sql
-- Индекс для поиска по артикулу
CREATE INDEX idx_art_no ON spare_parts (art_no);

-- Индекс для поиска по модели
CREATE INDEX idx_model ON spare_parts (product_model);

-- Составной индекс
CREATE INDEX idx_art_model ON spare_parts (art_no, product_model);
```

## 📝 Примечания

1. **Поле `usage_path`** содержит полный иерархический путь использования детали
2. **Поля с датами** заполняются только для деталей с ограничениями по производству
3. **Один артикул** может встречаться несколько раз (для разных моделей или расположений)
4. **Water treatment** — специальный файл с фильтрами и аксессуарами для водоподготовки

**Версия:** 1.0  
**Дата создания:** 2026-05-17  
**Количество записей:** 24 678  
**Количество моделей:** 20
**Сама база в GitHub не выложена, только описание.**