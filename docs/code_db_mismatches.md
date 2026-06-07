# Несоответствия кода и структуры баз данных

## ⚠️ Критические проблемы

Данный документ описывает выявленные несоответствия между ожидаемой структурой баз данных (согласно README в `/data/databases/`) и реальными SQL-запросами в коде адаптеров.

---

## 1. NomenclatureAdapter

**Файл:** `gui/services/adapters/nomenclature_adapter.py`

### Проблема 1: Неверные имена полей в запросах

**Ожидаемая схема БД** (из `data/databases/nomenclature/README.md`):
```sql
CREATE TABLE nomenclature (
    id INTEGER,
    canonical_article TEXT,      -- ← КАНОНИЧЕСКИЙ артикул
    name_ru TEXT,                -- ← Наименование на русском
    alternative_articles TEXT,   -- ← JSON-массив
    unit TEXT                    -- ← Единица измерения
);
```

**Реальный код в методе `search()`:**
```python
sql = """
    SELECT DISTINCT article, name, barcodes  -- ← НЕВЕРНЫЕ ИМЕНА ПОЛЕЙ!
    FROM {table_name}
    LIMIT 1000
"""
```

**Реальный код в методе `get_by_article()`:**
```python
sql = """
    SELECT article, name, barcodes  -- ← НЕВЕРНЫЕ ИМЕНА ПОЛЕЙ!
    FROM nomenclature
    WHERE article = ?               -- ← Поле называется canonical_article!
"""
```

### Проблема 2: Отсутствует чтение поля `unit`

Метод `get_by_article()` не запрашивает поле `unit`, хотя оно необходимо для отображения в окне детальной информации.

### Проблема 3: Неправильная обработка альтернативных артикулов

Код ожидает поле `barcodes`, но в БД поле называется `alternative_articles` и содержит JSON-массив всех альтернативных артикулов (не только штрих-кодов).

---

## 2. ProductDetailsService

**Файл:** `gui/services/product_details_service.py`

### Проблема 1: Метод `_get_nomenclature_data()` использует неверный адаптер

Метод пытается получить данные через `self._nomenclature.search(article)`, который возвращает объект `Product` с неверными полями (см. проблему выше).

### Проблема 2: Прямой SQL-запрос с правильными именами полей игнорируется

В коде есть резервный запрос с правильными именами полей:
```python
cursor.execute(f"""
    SELECT canonical_article, name_ru, alternative_articles, unit
    FROM {table_name}
    WHERE canonical_article = ?
    OR JSON_EXTRACT(alternative_articles, '$') LIKE ?
""", (article, f'%{article}%'))
```

Но он используется только если `search()` не нашёл результатов, что маловероятно из-за неверных имён полей в основном запросе.

---

## 3. ProductInfoDialog

**Файл:** `gui/dialogs/product_info_dialog.py`

### Проблема: Поля не обновляются корректно

Метод `_update_ui_with_full_data()` ожидает, что объект `Product` будет содержать поля `unit`, `description`, `category`, но они не заполняются из-за проблем в адаптере.

В методе `_load_details()`:
```python
self._lbl_description.configure(text=self._product.get('description', 'Нет описания'))
self._lbl_category.configure(text=self._product.get('category', 'Нет категории'))
```

Эти поля никогда не будут иметь значения, так как:
1. В `nomenclature.db` нет поля `description` (это нормально)
2. Поле `category` должно приходить из `css_export.db`, но не передаётся корректно

---

## 📋 Сводная таблица несоответствий

| Компонент | Ожидаемое поле | Реальное поле в коде | Статус |
|-----------|----------------|----------------------|--------|
| nomenclature.table | `canonical_article` | `article` | ❌ Неверно |
| nomenclature.table | `name_ru` | `name` | ❌ Неверно |
| nomenclature.table | `alternative_articles` | `barcodes` | ❌ Неверно |
| nomenclature.table | `unit` | (отсутствует) | ❌ Не читается |
| store.table | `locations` (JSON) | `locations` | ✅ Верно |
| css_export.table | `art_no` | `art_no` | ✅ Верно |

---

## 🔧 Требуемые изменения

### В `nomenclature_adapter.py`:

1. Заменить все упоминания `article` на `canonical_article`
2. Заменить `name` на `name_ru`
3. Заменить `barcodes` на `alternative_articles`
4. Добавить поле `unit` в SELECT-запросы
5. Обновить логику парсинга JSON для `alternative_articles`

### В `product_details_service.py`:

1. Использовать прямой SQL-запрос с правильными именами полей вместо reliance на `search()`
2. Убедиться, что поле `unit` передаётся в модель `Product`

### В `product_info_dialog.py`:

1. Убедиться, что поле `category` заполняется из данных производителя (`manufacturer_info[0]['category1']`)
2. Проверить обновление всех полей после загрузки данных

---

## 📝 Примечание

Данный документ создан исключительно для документации выявленных проблем. **Никакие изменения в код не вносились** согласно требованию заказчика.
