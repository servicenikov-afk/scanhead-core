# Nomenclature Database - Внутренний справочник номенклатуры

## 📦 Описание

База данных внутренней номенклатуры организации, содержащая соответствие между артикулами, наименованиями и альтернативными артикулами (включая штрих-коды и артикулы производителей).

**Расположение БД:** `/data/databases/nomenclature/nomenclature.db`

**Роль:** Основной справочник при поиске деталей

## 🗂️ Структура таблицы `spare_parts`

| Колонка | Тип | Описание | Пример |
|---------|-----|----------|--------|
| `id` | INTEGER | Порядковый номер записи | `1` |
| `article` | TEXT | **Артикул** (внутренний, уникальный) | `566.0000.004` |
| `name` | TEXT | Наименование на русском языке | `Головная часть 0-70% со слайдером` |
| `barcodes` | TEXT | JSON-массив альтернативных артикулов/штрихкодов | `["1013637","566.0000.004"]` |
| `unit` | TEXT | Единица измерения | `шт` |
| `last_updated` | DATETIME | Дата последнего обновления | `2026-05-17 18:30:00` |

### Пример записи

```json
{
  "id": 2,
  "article": "566.0000.004",
  "name": "Головная часть 0-70% со слайдером, соединения G3/8",
  "barcodes": "[\"1013637\",\"566.0000.004\"]",
  "unit": "шт"
}
```

## 🔍 Примеры SQL-запросов

### 1. Поиск по артикулу

```sql
SELECT * FROM spare_parts 
WHERE article = '566.0000.004';
```

### 2. Поиск по любому альтернативному артикулу

```sql
-- Найти запись, где в JSON-массиве есть нужный артикул
SELECT * FROM spare_parts 
WHERE barcodes LIKE '%566.0000.004%';
```

### 3. Поиск по наименованию (частичное совпадение)

```sql
SELECT * FROM spare_parts 
WHERE name LIKE '%головная часть%';
```

### 4. Получить все альтернативные артикулы для позиции

```sql
SELECT 
    article,
    name,
    json_each.value as alias_article
FROM spare_parts, json_each(spare_parts.barcodes)
WHERE article = '566.0000.004';
```

### 5. Поиск с нормализацией (один запрос по любому артикулу)

```sql
-- Ищет и в article, и в barcodes
SELECT DISTINCT n.* 
FROM spare_parts n
LEFT JOIN json_each(n.barcodes) as aliases
WHERE 
    n.article = '566.0000.004'
    OR aliases.value = '566.0000.004';
```

## 🔗 Связь с CSS Export DB

Две базы данных работают вместе:

| База | Роль | Особенность |
|------|------|-------------|
| `nomenclature.db` | **Основная** | Ваша внутренняя номенклатура, русские названия |
| `css_export.db` | **Вспомогательная** | Оригинальная номенклатура производителя |

### Пример объединённого поиска

```python
import sqlite3

def search_article(article):
    """Поиск по всем базам"""
    results = {'internal': None, 'manufacturer': []}
    
    # Поиск в nomenclature.db
    conn = sqlite3.connect('data/databases/nomenclature/nomenclature.db')
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT n.* 
        FROM spare_parts n
        LEFT JOIN json_each(n.barcodes) as aliases
        WHERE n.article = ? OR aliases.value = ?
    """, (article, article))
    results['internal'] = cur.fetchone()
    conn.close()
    
    # Поиск в css_export.db
    conn = sqlite3.connect('data/databases/css_export/css_export.db')
    cur = conn.cursor()
    cur.execute("""
        SELECT product_model, art_no, name, usage_path 
        FROM spare_parts 
        WHERE art_no = ?
    """, (article,))
    results['manufacturer'] = cur.fetchall()
    conn.close()
    
    return results
```

## 🛠️ Инструменты для работы

### Просмотр БД

```bash
# Командная строка
sqlite3 data/databases/nomenclature/nomenclature.db
.tables
SELECT * FROM spare_parts LIMIT 10;
.quit
```

### Экспорт в Excel

```python
import sqlite3
import pandas as pd
import json

conn = sqlite3.connect('data/databases/nomenclature/nomenclature.db')

# Читаем все данные
df = pd.read_sql_query("SELECT * FROM spare_parts", conn)

# Раскрываем JSON с альтернативными артикулами
df['barcodes'] = df['barcodes'].apply(
    lambda x: ', '.join(json.loads(x)) if x else ''
)

df.to_excel('nomenclature.xlsx', index=False)
conn.close()
```

## 📊 Статистика

```sql
-- Общее количество позиций
SELECT COUNT(*) as total FROM spare_parts;

-- Уникальные единицы измерения
SELECT unit, COUNT(*) as count FROM spare_parts GROUP BY unit;

-- Среднее количество альтернативных артикулов на позицию
SELECT AVG(json_array_length(barcodes)) as avg_aliases 
FROM spare_parts;
```

### Обновление альтернативных артикулов

```sql
UPDATE spare_parts 
SET barcodes = '["1013637","566.0000.004","НОВЫЙ_АРТ"]'
WHERE article = '566.0000.004';
```

## 📝 Примечания

1. **Поле `barcodes`** хранится как JSON-массив для гибкости
2. **Артикул** не всегда входит в массив альтернативных
3. **Единица измерения** — преимущественно `шт`, но могут быть и другие

---

**Версия:** 1.0  
**Дата создания:** 2026-05-17  
**Количество записей:** 1693  
**Формат хранения:** SQLite v3