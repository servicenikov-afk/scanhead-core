# Nomenclature Database - Внутренний справочник номенклатуры

## 📦 Описание

База данных внутренней номенклатуры организации, содержащая соответствие между каноническими артикулами, русскими наименованиями и альтернативными артикулами (включая штрих-коды и артикулы производителей).

**Расположение БД:** `/data/databases/nomenclature/nomenclature.db`

**Роль:** Основной справочник при поиске деталей

## 🗂️ Структура таблицы `nomenclature`

| Колонка | Тип | Описание | Пример |
|---------|-----|----------|--------|
| `id` | INTEGER | Порядковый номер записи | `1` |
| `canonical_article` | TEXT | **Канонический артикул** (внутренний) | `566.0000.004` |
| `name_ru` | TEXT | Наименование на русском языке | `Головная часть 0-70% со слайдером` |
| `alternative_articles` | TEXT | JSON-массив альтернативных артикулов | `["1013637","566.0000.004"]` |
| `unit` | TEXT | Единица измерения | `шт` |

### Пример записи

```json
{
  "id": 2,
  "canonical_article": "566.0000.004",
  "name_ru": "Головная часть 0-70% со слайдером, соединения G3/8",
  "alternative_articles": "[\"1013637\",\"566.0000.004\"]",
  "unit": "шт"
}
```

## 🔍 Примеры SQL-запросов

### 1. Поиск по каноническому артикулу

```sql
SELECT * FROM nomenclature 
WHERE canonical_article = '566.0000.004';
```

### 2. Поиск по любому альтернативному артикулу

```sql
-- Найти запись, где в JSON-массиве есть нужный артикул
SELECT * FROM nomenclature 
WHERE JSON_EXTRACT(alternative_articles, '$') LIKE '%566.0000.004%';
```

### 3. Поиск по наименованию (частичное совпадение)

```sql
SELECT * FROM nomenclature 
WHERE name_ru LIKE '%головная часть%';
```

### 4. Получить все альтернативные артикулы для позиции

```sql
SELECT 
    canonical_article,
    name_ru,
    json_each.value as alias_article
FROM nomenclature, json_each(nomenclature.alternative_articles)
WHERE canonical_article = '566.0000.004';
```

### 5. Поиск с нормализацией (один запрос по любому артикулу)

```sql
-- Ищет и в каноническом, и в альтернативных
SELECT DISTINCT n.* 
FROM nomenclature n
LEFT JOIN json_each(n.alternative_articles) as aliases
WHERE 
    n.canonical_article = '566.0000.004'
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
        FROM nomenclature n
        LEFT JOIN json_each(n.alternative_articles) as aliases
        WHERE n.canonical_article = ? OR aliases.value = ?
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
SELECT * FROM nomenclature LIMIT 10;
.quit
```

### Экспорт в Excel

```python
import sqlite3
import pandas as pd
import json

conn = sqlite3.connect('data/databases/nomenclature/nomenclature.db')

# Читаем все данные
df = pd.read_sql_query("SELECT * FROM nomenclature", conn)

# Раскрываем JSON с альтернативными артикулами
df['alternative_articles'] = df['alternative_articles'].apply(
    lambda x: ', '.join(json.loads(x)) if x else ''
)

df.to_excel('nomenclature.xlsx', index=False)
conn.close()
```

## 📊 Статистика

```sql
-- Общее количество позиций
SELECT COUNT(*) as total FROM nomenclature;

-- Уникальные единицы измерения
SELECT unit, COUNT(*) as count FROM nomenclature GROUP BY unit;

-- Среднее количество альтернативных артикулов на позицию
SELECT AVG(json_array_length(alternative_articles)) as avg_aliases 
FROM nomenclature;
```

### Обновление альтернативных артикулов

```sql
UPDATE nomenclature 
SET alternative_articles = '["1013637","566.0000.004","НОВЫЙ_АРТ"]'
WHERE canonical_article = '566.0000.004';
```

## 📝 Примечания

1. **Поле `alternative_articles`** хранится как JSON-массив для гибкости
2. **Канонический артикул** не всегда входит в массив альтернативных
3. **Единица измерения** — преимущественно `шт`, но могут быть и другие

---

**Версия:** 1.0  
**Дата создания:** 2026-05-17  
**Количество записей:** 1693  
**Формат хранения:** SQLite v3