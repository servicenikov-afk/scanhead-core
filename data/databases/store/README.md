# Store Database - Локальный складской учёт

## 📦 Описание

Локальная база данных для хранения информации о местоположении запасных частей на складе.  
Один артикул может храниться в нескольких местах (массив адресов).

**Расположение:** `\data\databases\store\store.db`

## 🗂️ Структура таблицы

| Колонка | Тип | Описание | Пример |
|---------|-----|----------|--------|
| `article` | TEXT | Артикул (уникальный) | `566.0000.004` |
| `locations` | TEXT | JSON-массив адресов | `["A-12-3","B-05-2"]` |
| `alternative_names` | TEXT | JSON-массив альтернативных названий | `["Головная часть","PURITY C"]` |
| `notes` | TEXT | Примечания | `Основной склад` |
| `created_at` | DATETIME | Дата создания записи | `2026-05-17 18:30:00` |
| `updated_at` | DATETIME | Дата последнего обновления | `2026-05-17 18:30:00` |

## 📝 Пример записи

```json
{
  "article": "566.0000.004",
  "locations": "[\"A-12-3\", \"B-05-2\", \"C-01-7\"]",
  "alternative_names": "[\"Головная часть\", \"PURITY C head\"]",
  "notes": "Основной склад + два резервных места"
}
🔍 SQL-запросы
Добавление артикула
sql
INSERT INTO storage_locations (article, locations, alternative_names, notes)
VALUES ('566.0000.004', '["A-12-3", "B-05-2"]', '["Головная часть"]', NULL);
Поиск по артикулу
sql
SELECT * FROM storage_locations WHERE article = '566.0000.004';
Добавить новый адрес
sql
UPDATE storage_locations 
SET locations = json_insert(locations, '$[#]', 'C-01-7')
WHERE article = '566.0000.004';
Удалить конкретный адрес
sql
UPDATE storage_locations 
SET locations = (
    SELECT json_group_array(value) 
    FROM json_each(locations) 
    WHERE value != 'B-05-2'
)
WHERE article = '566.0000.004';
Найти артикул по адресу
sql
SELECT article, locations 
FROM storage_locations 
WHERE locations LIKE '%A-12-3%';
Получить все адреса артикула
sql
SELECT 
    article, 
    json_group_array(value) as all_addresses
FROM storage_locations, json_each(locations)
WHERE article = '566.0000.004';

🔄 Связанные базы данных
База	Роль	Ключевое поле
nomenclature.db	Основная номенклатура	canonical_article
css_export.db	Номенклатура производителя	art_no
store.db	Складские адреса	article
Версия: 1.0
Дата создания: 2026-05-17