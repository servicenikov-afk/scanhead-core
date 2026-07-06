# TODO.md — План рефакторинга ScanHead Core v0.3.0

**Дата:** 06.07.2026  
**Версия:** 0.3.0  
**Статус:** ⚠️ Требуется рефакторинг  
**Всего проверено файлов:** 37  
**Проблемных файлов:** 16 (6 ❌ критических + 9 ⚠️ средних + 1 🔴 потокобезопасность)

---

## 📊 Сводка по проблемным файлам

| Приоритет | Количество | Файлы |
|-----------|------------|-------|
| 🔴 Критические | 6 | product_details.py, print_queue.py, product_info_dialog.py, store_adapter.py, product_details_service.py, search_address_tab.py |
| 🟡 Средние | 9 | main.py, nomenclature_adapter.py, css_export_adapter.py, inventory_tab.py, services/stubs/__init__.py, fuzzy_search.py, sticker_generator.py, search_bar.py, pdf_renderer.py |
| 🟢 Косметические | 1 | Все файлы с DEBUG_TEMP-логами |

---

# 🔴 ФАЗА 1 — КРИТИЧЕСКИЕ НАРУШЕНИЯ (6 файлов)

---

## 1. ❌ **gui/product_details.py** — Нарушение DIP + SRP

**Путь:** `gui/product_details.py`

### Проблемы:
- [ ] ❌ Прямые импорты диалогов: `from gui.dialogs.field_editor import FieldEditor`
- [ ] ❌ Прямой импорт `ProductInfoDialog` внутри метода `_on_info_click`
- [ ] ❌ Прямая работа с репозиторием в UI: `self._product_repo.update_field()`
- [ ] ❌ Нарушение SRP: отображение + лейаут + навигация + сохранение
- [ ] ❌ Нарушение Закона Деметры: `self._address_formatter.parse(addr)`
- [ ] 🗑️ Мёртвый код: `_render_incompatible_address()` не вызывается
- [ ] 🗑️ Мёртвый параметр: `show_edit_btn` всегда `False`
- [ ] ⚠️ Непонятная зависимость: обработка `_draw_engine`

### Решения:
- [ ] Создать фабрику диалогов `DialogFactory` и внедрить её
- [ ] Создать `IProductService` для бизнес-логики обновления полей
- [ ] Вынести логику сохранения в сервис
- [ ] Удалить `_render_incompatible_address()`
- [ ] Удалить параметр `show_edit_btn`
- [ ] Убрать обработку `_draw_engine` или задокументировать

### Пример исправления:
```python
# Было (плохо):
class ProductDetails(ctk.CTkFrame):
    def __init__(self, ..., product_repo: IProductRepository):
        self._product_repo = product_repo

    def _on_field_saved(self, field_name: str, new_value: str):
        self._product_repo.update_field(...)  # ❌ UI → репозиторий

# Должно быть (хорошо):
class ProductDetails(ctk.CTkFrame):
    def __init__(self, ..., product_service: IProductService, dialog_factory: DialogFactory):
        self._product_service = product_service
        self._dialog_factory = dialog_factory

    def _on_field_saved(self, field_name: str, new_value: str):
        self._product_service.update_field(...)  # ✅ UI → сервис
```

---

## 2. ❌ **gui/print_queue.py** — Нарушение DIP + SRP + IOC

**Путь:** `gui/print_queue.py`

### Проблемы:
- [ ] ❌ Нарушение DIP/IOC: жёсткая привязка к CustomTkinter в `__init__`
- [ ] ❌ Нарушение SRP: отображение + состояние + inline-редактирование + печать
- [ ] ❌ Нарушение Закона Деметры: прямая работа с `self._tree` во всех методах
- [ ] ❌ Смешение стека: `ctk.CTkFrame` + `ttk.Treeview` без чёткого разделения
- [ ] 🗑️ Мёртвый код: `_toggle_column_menu()` — пустая заглушка
- [ ] 🗑️ Мёртвый код: `_import_from_file()` — пустая заглушка
- [ ] 🗑️ Неиспользуемый параметр: `_product_repo` передаётся, но не используется
- [ ] ⚠️ Глобальный флаг `_theme_applied` — нарушение инкапсуляции
- [ ] ⚠️ `for widget in self._tree.winfo_children(): widget.destroy()` — опасное удаление

### Решения:
- [ ] Выделить `PrintQueueModel` для состояния и бизнес-логики
- [ ] Использовать паттерн MVC или MVP
- [ ] Создать `IPrintQueueService` для логики печати
- [ ] Удалить мёртвый код (`_toggle_column_menu`, `_import_from_file`)
- [ ] Удалить неиспользуемый `_product_repo`
- [ ] Заменить глобальный флаг на проверку существования стиля
- [ ] Использовать `tree.delete()` вместо удаления дочерних виджетов

### Пример исправления:
```python
# Было (плохо):
class PrintQueue(ctk.CTkFrame):
    def __init__(self, ..., product_repo, printer_service):
        self._products: List[Product] = []
        self._tree = ttk.Treeview(...)  # ❌ UI + состояние

    def add_item(self, product):  # ❌ бизнес-логика в UI
        self._products.append(product)
        self._tree.insert(...)

# Должно быть (хорошо):
class PrintQueueModel:
    def __init__(self):
        self._items: List[QueueItem] = []
    
    def add_item(self, product): ...  # бизнес-логика
    def get_items(self) -> List[QueueItem]: ...

class PrintQueue(ctk.CTkFrame):
    def __init__(self, model: PrintQueueModel, printer_service: IPrinterService):
        self._model = model
        self._printer_service = printer_service
        # только отображение
```

---

## 3. ❌ **gui/dialogs/product_info_dialog.py** — Нарушение SRP + DIP

**Путь:** `gui/dialogs/product_info_dialog.py`

### Проблемы:
- [ ] ❌ Нарушение SRP: UI + парсинг адресов + работа с БД + async-загрузка
- [ ] ❌ Прямая зависимость от адаптеров: `nomenclature_adapter`, `store_adapter`, `css_adapter`
- [ ] ❌ Прямые импорты из `gui.services`: `ProductDetailsService`
- [ ] ❌ Нарушение DIP: диалог знает о конкретных адаптерах, а не интерфейсах
- [ ] ❌ `_load_details_legacy()` — дублирует логику, работает напрямую с адаптерами
- [ ] 🗑️ Мёртвый код: `_load_details_legacy()` не должен существовать
- [ ] ⚠️ `_unsaved_changes` — состояние должно управляться сервисом

### Решения:
- [ ] Создать интерфейс `IProductDetailsService` (или использовать существующий)
- [ ] Внедрять готовый `Product` с уже загруженными данными
- [ ] Передавать только `product: Product` и `settings_service: ISettingsService`
- [ ] Удалить `_load_details_legacy()` и все прямые адаптеры
- [ ] Вынести логику сохранения адресов в сервис
- [ ] Использовать `AddressFormatter` через DI

### Пример исправления:
```python
# Было (плохо):
class ProductInfoDialog(ctk.CTkToplevel):
    def __init__(self, ..., nomenclature_adapter, store_adapter, css_adapter):
        self._nomenclature_adapter = nomenclature_adapter  # ❌ прямые адаптеры
        self._store_adapter = store_adapter

# Должно быть (хорошо):
class ProductInfoDialog(ctk.CTkToplevel):
    def __init__(self, master, product: Product, settings_service: ISettingsService, dialog_factory: DialogFactory):
        self._product = product  # ✅ готовые данные
        self._settings_service = settings_service
        self._dialog_factory = dialog_factory
```

---

## 4. ❌ **gui/services/adapters/store_adapter.py** — Read-only нарушение

**Путь:** `gui/services/adapters/store_adapter.py`

### Проблемы:
- [ ] ❌ **Read-only нарушение**: `sqlite3.connect(str(self.db_path))` — НЕ read-only!
- [ ] ❌ **Хрупкий путь**: `Path(__file__).parent.parent.parent.parent` (4 уровня)
- [ ] ❌ **Подавление исключений**: `return []` при ошибке (нарушает "Fail Fast")
- [ ] ❌ **INSERT OR REPLACE** удаляет старую запись (теряет `created_at`, `notes`)
- [ ] ❌ **Нет интерфейса** (Protocol/ABC) для тестируемости
- [ ] 🗑️ `_ensure_schema()` вызывается, но нигде не используется
- [ ] 🗑️ `close()` — заглушка (ничего не закрывает)

### Решения:
- [ ] Использовать `?mode=ro` для read-only операций
- [ ] Создать отдельный `IStoreWriter` для записи
- [ ] Использовать `libs.path_utils.get_db_path()`
- [ ] Удалить подавление исключений: `raise` с логированием
- [ ] Использовать `INSERT OR IGNORE` + `UPDATE` вместо `REPLACE`
- [ ] Создать интерфейс `IStoreAdapter`
- [ ] Удалить `_ensure_schema()` или использовать при первом запуске
- [ ] Реализовать реальный `close()` или убрать

### Пример исправления:
```python
# Было (плохо):
conn = sqlite3.connect(str(self.db_path))  # ❌ запись

# Должно быть (хорошо):
# Для чтения:
conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)

# Для записи (отдельный адаптер или метод):
conn = sqlite3.connect(str(self.db_path))
```

```python
# Было (плохо):
def get_all_locations(self, article):
    try:
        # ...
    except Exception:
        return []  # ❌ подавление

# Должно быть (хорошо):
def get_all_locations(self, article):
    try:
        # ...
    except Exception as e:
        logger.error(f"...", exc_info=True)
        raise  # ✅ Fail Fast
```

---

## 5. ❌ **gui/services/product_details_service.py** — Нарушение абстракции

**Путь:** `gui/services/product_details_service.py`

### Проблемы:
- [ ] ❌ **Нарушение абстракции**: `self._nomenclature._get_connection()` — доступ к protected
- [ ] ❌ **Сырой SQL в сервисе**: `SELECT name FROM sqlite_master...`
- [ ] ❌ **Дублирование логики**: `_get_nomenclature_data` дублирует `NomenclatureAdapter.search`
- [ ] ❌ **Прямой вызов callback из потока**: `callback(product)` без `root.after`
- [ ] ❌ **Нет интерфейса**: `IProductDetailsService` отсутствует
- [ ] 🗑️ **DEBUG_TEMP-логи**: оставлены в коде

### Решения:
- [ ] Использовать публичный метод `nomenclature_adapter.get_by_article()`
- [ ] Удалить сырой SQL, перенести логику в адаптер
- [ ] Удалить `_get_nomenclature_data()` и использовать `NomenclatureAdapter.search()`
- [ ] Добавить `root.after(0, lambda: callback(product))` для безопасности
- [ ] Создать интерфейс `IProductDetailsService`
- [ ] Удалить все DEBUG_TEMP-логи

### Пример исправления:
```python
# Было (плохо):
def _get_nomenclature_data(self, article):
    conn = self._nomenclature._get_connection()  # ❌ доступ к protected
    cursor.execute("SELECT name FROM sqlite_master...")  # ❌ сырой SQL

# Должно быть (хорошо):
def _get_nomenclature_data(self, article):
    return self._nomenclature.get_by_article(article)  # ✅ публичный метод
```

```python
# Было (плохо):
def _fetch_thread():
    product = self._fetch_all_data(article)
    if callback: callback(product)  # ❌ из потока

# Должно быть (хорошо):
def _fetch_thread():
    product = self._fetch_all_data(article)
    if callback:
        self._root.after(0, lambda: callback(product))  # ✅ через root.after
```

---

## 6. ❌ **gui/tabs/search_address_tab.py** — Бизнес-логика в UI

**Путь:** `gui/tabs/search_address_tab.py`

### Проблемы:
- [ ] ❌ **Бизнес-логика обогащения в UI**: сложная логика `on_details_loaded`
- [ ] ❌ **DEBUG_TEMP-логирование**: оставлено в коде
- [ ] ❌ **Импорт внутри метода**: `from libs.utils import AddressFormatConfig, AddressFormatter`
- [ ] ❌ **Небезопасный callback из потока**: `details_service.get_product_details` вызывает callback из фона
- [ ] ❌ **Смешение ответственностей**: UI знает о деталях обогащения

### Решения:
- [ ] Создать `IProductEnrichmentService` для логики обогащения
- [ ] Удалить все DEBUG_TEMP-логи
- [ ] Перенести импорты в начало файла
- [ ] Передать в `SearchAddressTab` уже обогащённые продукты
- [ ] Или внедрить `enrichment_service` и вызвать его

### Пример исправления:
```python
# Было (плохо):
def _on_search_result(self, products: List[Product]):
    # ❌ бизнес-логика в UI
    pending_count = len(products)
    def on_details_loaded(product, index):
        # ... сложная логика
    for i, product in enumerate(products):
        details_service.get_product_details(product.article, callback=...)

# Должно быть (хорошо):
def _on_search_result(self, products: List[Product]):
    # ✅ UI только получает результат
    self._enrichment_service.enrich_products(
        products,
        callback=lambda enriched: self.update_products(enriched)
    )
```

---

# 🟡 ФАЗА 2 — СРЕДНИЕ НАРУШЕНИЯ (9 файлов)

---

## 7. 🔴 **gui/search_bar.py** — Нарушение потокобезопасности

**Путь:** `gui/search_bar.py`

### Проблемы:
- [ ] ❌ **`threading.Timer` для debounce** — должен быть `widget.after()`
- [ ] ⚠️ Callback из фонового потока: `self._on_search_complete` вызывается из потока

### Решения:
- [ ] Заменить `threading.Timer` на `self.after(self._debounce_ms, self._do_search)`
- [ ] Сохранять `_after_id` для отмены предыдущего вызова

### Пример исправления:
```python
# Было (плохо):
self._timer = threading.Timer(self._debounce_ms / 1000.0, self._do_search, args=[query])
self._timer.start()

# Должно быть (хорошо):
if self._after_id:
    self.after_cancel(self._after_id)
self._after_id = self.after(self._debounce_ms, lambda: self._do_search(query))
```

---

## 8. ⚠️ **gui/services/adapters/nomenclature_adapter.py** — Фильтрация в Python

**Путь:** `gui/services/adapters/nomenclature_adapter.py`

### Проблемы:
- [ ] ❌ **Фильтрация в Python** вместо индексированного SQL
- [ ] ❌ **Небезопасный callback из потока** в `search_async`
- [ ] ❌ **Несогласованность соединений**: `_get_connection` хранит коннект, методы создают новые
- [ ] ❌ **Нет интерфейса** для тестируемости
- [ ] ⚠️ **Жёсткий путь** в сигнатуре `__init__`

### Решения:
- [ ] Использовать `WHERE article LIKE ? OR name LIKE ? OR barcodes LIKE ?`
- [ ] Добавить `root.after(0, callback(results))` в `search_async`
- [ ] Удалить `_get_connection()` и использовать локальные соединения
- [ ] Создать интерфейс `INomenclatureAdapter`
- [ ] Использовать `libs.path_utils.get_db_path()`

### Пример исправления:
```python
# Было (плохо):
cursor.execute("SELECT ... FROM table LIMIT 1000")
for row in rows:
    if query_lower in article.lower():  # ❌ фильтрация в Python

# Должно быть (хорошо):
cursor.execute("""
    SELECT ... FROM table 
    WHERE LOWER(article) LIKE ? OR LOWER(name) LIKE ? OR LOWER(barcodes) LIKE ?
    LIMIT 50
""", (f"%{query}%", f"%{query}%", f"%{query}%"))
```

---

## 9. ⚠️ **gui/services/adapters/css_export_adapter.py** — Пути и интерфейс

**Путь:** `gui/services/adapters/css_export_adapter.py`

### Проблемы:
- [ ] ❌ **Жёсткий путь** в сигнатуре `__init__`
- [ ] ❌ **Нет интерфейса** для тестируемости
- [ ] ⚠️ **`close()` — заглушка**
- [ ] ⚠️ **Фильтрация только по названию**

### Решения:
- [ ] Использовать `libs.path_utils.get_db_path()`
- [ ] Создать интерфейс `ICssExportAdapter`
- [ ] Удалить `close()` или реализовать
- [ ] Добавить поиск по артикулу и модели

---

## 10. ⚠️ **main.py** — Смешивание ответственностей

**Путь:** `main.py`

### Проблемы:
- [ ] ❌ **Смешивание ответственностей**: логирование + DI + GUI-тема
- [ ] ❌ **Жёсткие пути к БД** в коде
- [ ] ❌ **Импорты внутри `main()`** — затрудняют анализ
- [ ] ⚠️ **Создание root до регистрации сервисов** — нарушение порядка
- [ ] ⚠️ **Обработка TclError** — `tk.TclError` используется до импорта `tk`

### Решения:
- [ ] Вынести логирование в отдельный модуль
- [ ] Использовать конфиг для путей к БД
- [ ] Перенести импорты в начало файла
- [ ] Создавать root ПОСЛЕ регистрации сервисов
- [ ] Импортировать `tk` в начале файла

---

## 11. ⚠️ **gui/tabs/inventory_tab.py** — Неиспользуемый DI

**Путь:** `gui/tabs/inventory_tab.py`

### Проблемы:
- [ ] ⚠️ **DI-контейнер внедряется, но не используется**
- [ ] ⚠️ **master: Any** вместо `ctk.CTkBaseClass`

### Решения:
- [ ] Использовать `self._container.get(IInventoryService)` для кнопок
- [ ] Исправить аннотацию типа: `master: ctk.CTkBaseClass`

---

## 12. ⚠️ **services/stubs/__init__.py** — Небезопасный callback

**Путь:** `services/stubs/__init__.py`

### Проблемы:
- [ ] ⚠️ **`StubSearchService.search_async`** вызывает callback напрямую из потока

### Решения:
- [ ] Добавить `root.after(0, callback(results))` (если используется в тестах)
- [ ] Или оставить как заглушку (допустимо для разработки)

---

## 13. ⚠️ **libs/utils/fuzzy_search.py** — Жёсткий порог

**Путь:** `libs/utils/fuzzy_search.py`

### Проблемы:
- [ ] ⚠️ **Жёсткий порог 0.8** в `_fuzzy_match`
- [ ] ⚠️ **Нет типа для `mode`** (можно `Literal`)

### Решения:
- [ ] Добавить параметр `threshold: float = 0.8`
- [ ] Использовать `Literal` для `mode`

### Пример исправления:
```python
# Было:
def _fuzzy_match(self, text: str, query: str) -> bool:
    threshold = max(1, int(len(query) * 0.8))  # ❌ жёсткий порог

# Должно быть:
def _fuzzy_match(self, text: str, query: str, threshold: float = 0.8) -> bool:
    threshold = max(1, int(len(query) * threshold))  # ✅ параметризован
```

---

## 14. ⚠️ **libs/printing/sticker_generator.py** — Иммутабельность

**Путь:** `libs/printing/sticker_generator.py`

### Проблемы:
- [ ] ⚠️ **`self.config.update(preset)`** изменяет состояние объекта
- [ ] ⚠️ **`finally: self.config = old_config`** — восстановление конфига

### Решения:
- [ ] Сделать `generate()` иммутабельным: использовать копию конфига

### Пример исправления:
```python
# Было:
def generate(self, ..., preset=None):
    if preset: self.config.update(preset)  # ❌ мутация
    try: ...
    finally: self.config = old_config

# Должно быть:
def generate(self, ..., preset=None):
    config = self.config.copy()  # ✅ копия
    if preset: config.update(preset)
    # использовать config
```

---

## 15. ⚠️ **libs/printing/pdf_renderer.py** — Лишнее поле

**Путь:** `libs/printing/pdf_renderer.py`

### Проблемы:
- [ ] ⚠️ **`self._generator`** хранится как поле, хотя используется только в `render`

### Решения:
- [ ] Использовать локальную переменную вместо поля

### Пример исправления:
```python
# Было:
self._generator = StickerGenerator(preset)

# Должно быть:
generator = StickerGenerator(preset)  # локальная переменная
```

---

# 🟢 ФАЗА 3 — КОСМЕТИЧЕСКИЕ ИСПРАВЛЕНИЯ

---

## 16. 🟢 **DEBUG_TEMP-логи** (все файлы)

### Файлы:
- `gui/tabs/search_address_tab.py`
- `gui/services/product_details_service.py`

### Проблемы:
- [ ] 🗑️ **DEBUG_TEMP-логи** оставлены в коде

### Решения:
- [ ] Удалить все логи с `[DEBUG_TEMP]`

---

## 17. 🟢 **Неиспользуемые переменные и мёртвый код**

### Файлы:
- `gui/product_details.py` — `_render_incompatible_address()`, `show_edit_btn`
- `gui/print_queue.py` — `_toggle_column_menu()`, `_import_from_file()`, `_product_repo`
- `gui/main_window.py` — `self._img_help`, `self._img_settings`
- `gui/dialogs/field_editor.py` — `product_id`

### Решения:
- [ ] Удалить мёртвый код
- [ ] Удалить неиспользуемые параметры

---

## 18. 🟢 **Вынос default_config в отдельный файл**

### Файл:
- `services/config_manager_adapter.py`

### Проблемы:
- [ ] ⚠️ **Огромный словарь `default_config`** в коде

### Решения:
- [ ] Вынести в `config/default_config.py`
- [ ] Или загружать из `config/app_config.json` при отсутствии

---

# 📋 ЧЕК-ЛИСТ РЕФАКТОРИНГА

## 🔴 Критические (6 файлов)

| # | Файл | Статус | Ответственный | Дата |
|---|------|--------|---------------|------|
| 1 | `gui/product_details.py` | ⬜ | | |
| 2 | `gui/print_queue.py` | ⬜ | | |
| 3 | `gui/dialogs/product_info_dialog.py` | ⬜ | | |
| 4 | `gui/services/adapters/store_adapter.py` | ⬜ | | |
| 5 | `gui/services/product_details_service.py` | ⬜ | | |
| 6 | `gui/tabs/search_address_tab.py` | ⬜ | | |

## 🟡 Средние (9 файлов)

| # | Файл | Статус | Ответственный | Дата |
|---|------|--------|---------------|------|
| 7 | `gui/search_bar.py` | ⬜ | | |
| 8 | `gui/services/adapters/nomenclature_adapter.py` | ⬜ | | |
| 9 | `gui/services/adapters/css_export_adapter.py` | ⬜ | | |
| 10 | `main.py` | ⬜ | | |
| 11 | `gui/tabs/inventory_tab.py` | ⬜ | | |
| 12 | `services/stubs/__init__.py` | ⬜ | | |
| 13 | `libs/utils/fuzzy_search.py` | ⬜ | | |
| 14 | `libs/printing/sticker_generator.py` | ⬜ | | |
| 15 | `libs/printing/pdf_renderer.py` | ⬜ | | |

## 🟢 Косметические (3 задачи)

| # | Задача | Статус | Ответственный | Дата |
|---|--------|--------|---------------|------|
| 16 | Удалить DEBUG_TEMP-логи | ⬜ | | |
| 17 | Удалить мёртвый код и неиспользуемые переменные | ⬜ | | |
| 18 | Вынести default_config в отдельный файл | ⬜ | | |

---

# 📊 ИТОГОВАЯ СТАТИСТИКА

| Категория | Количество |
|-----------|------------|
| 🔴 Критические файлы | 6 |
| 🟡 Средние файлы | 9 |
| 🟢 Косметические задачи | 3 |
| **Всего задач** | **18** |
| ✅ Проверено файлов | 37 |
| ✅ Соответствуют манифесту | 20 (54%) |
| ⚠️ Требуют доработки | 16 (43%) |
| 🗑️ Удалён | 1 (3%) |

---

**Следующие шаги:**
1. Начать с 🔴 критических файлов (приоритет 1-6)
2. После завершения критических — перейти к 🟡 средним (7-15)
3. В конце — 🟢 косметические исправления (16-18)
4. После каждого файла — обновлять `current_structure.MD`