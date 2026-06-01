# Структура проекта ScanHead Core

**Ветка:** `gui-framework-dev`  
**Архитектура:** Строгая многослойность (Layered Architecture)  
**Версия:** 2.1  
**Дата генерации:** 2026-06-01

> ⚠️ **Важно:** Реальные базы данных (`*.db`) находятся ТОЛЬКО на тестовой машине. В репозитории присутствуют только схемы (`*.sql`) и описания (`README.md`).

---

## 🗂 Корневая структура (исключая служебные)

```
├── main.py                    # Точка входа: загрузка конфига, bootstrap, DI, запуск GUI
├── README.md                  # Обзор проекта, возможности, задачи
├── MANIFEST.md                # Архитектурные принципы, запреты, стандарты
├── .gitignore                 # Исключения для git
│
├── config/
│   └── app_config.json        # Конфигурация: пути к БД, лог-уровень, имя приложения
│
├── data/
│   ├── databases/
│   │   ├── css_export/        # Franke запчасти: spare_parts.sql + README
│   │   ├── nomenclature/      # Внутренняя номенклатура: nomenclature.db.sql + README
│   │   └── store/             # Складские адреса: storage_locations.sql + README
│   └── icons/                 # 14 PNG-иконок (32/64px) для UI
│
├── gui/                       # Presentation Layer (customtkinter)
│   ├── __init__.py            # Маркер пакета
│   ├── README.md              # Описание GUI-модулей
│   ├── main_window.py         # MainWindow: корневой фрейм, табы, диалоги
│   ├── product_details.py     # ProductDetails: карточка товара, AddressFormatter
│   ├── search_bar.py          # SearchBar: debounce, автодополнение, SuggestionList
│   ├── print_queue.py         # PrintQueue: очередь печати (управление списком)
│   ├── sticker_preview.py     # StickerPreview: предпросмотр этикетки
│   │
│   ├── dialogs/
│   │   ├── __init__.py        # Маркер пакета
│   │   ├── settings_dialog.py # SettingsDialog: модальные настройки
│   │   ├── field_editor.py    # FieldEditor: универсальный редактор полей
│   │   ├── product_info_dialog.py # ProductInfoDialog: детальная информация
│   │   ├── sticker_editor.py  # StickerEditor: редактор макета этикетки
│   │   └── add_address_dialog.py # AddAddressDialog: добавление адреса
│   │
│   ├── framework/
│   │   ├── __init__.py        # Маркер пакета
│   │   ├── dialog_base.py     # DialogBase: базовый класс для диалогов
│   │   └── list_base.py       # ListBase: базовый класс для списков (реализация)
│   │
│   ├── services/
│   │   ├── __init__.py        # Маркер пакета
│   │   ├── product_details_service.py # ProductDetailsService: агрегация 3 БД
│   │   └── adapters/
│   │       ├── __init__.py    # Маркер пакета
│   │       ├── nomenclature_adapter.py # NomenclatureAdapter: поиск в nomenclature.db
│   │       ├── store_adapter.py        # StoreAdapter: адреса хранения
│   │       └── css_export_adapter.py   # CssExportAdapter: данные от производителя
│   │
│   ├── tabs/
│   │   ├── __init__.py        # Маркер пакета
│   │   ├── search_address_tab.py # SearchAddressTab: основная рабочая вкладка
│   │   └── inventory_tab.py      # InventoryTab: заглушка (в разработке)
│   │
│   ├── widgets/
│   │   ├── __init__.py        # Маркер пакета
│   │   └── suggestion_list.py    # SuggestionList: выпадающий список подсказок
│   │
│   └── windows/
│       └── __init__.py           # Маркер пакета (заглушка для будущих окон)
│
├── libs/                        # Domain + Infrastructure (независимые модули)
│   ├── article_normalizer/      # Нормализация артикулов: core.py
│   ├── barcode_checker/         # Проверка валидности штрих-кода: core.py
│   ├── barcode_generator/       # Генерация штрих-кодов (Code128/EAN13): core.py
│   ├── barcode_validator/       # Валидация формата штрих-кода: core.py
│   ├── command_handler/         # Паттерн Command: core.py + data/commands.py
│   ├── config/                  # PresetManager: загрузка/сохранение пресетов
│   ├── config_manager/          # Управление конфигурацией приложения: core.py
│   ├── core/                    # Bootstrap: инициализация логгера, исключений
│   ├── data_enricher/           # Обогащение данных из нескольких источников
│   ├── data_exporters/          # Экспорт в CSV/Excel: csv_exporter.py, excel_exporter.py
│   ├── data_validator/          # Валидация входных данных: core.py
│   ├── db_manager/              # Управление соединениями с БД: core.py, models.py
│   ├── domain/                  # Доменные сущности: discrepancy.py
│   ├── domain_models/           # Чистые DTO (без логики):
│   │   ├── product.py           # Product: article, name, barcodes, storage_locations...
│   │   ├── address.py           # Address: code, description, quantity
│   │   ├── inventory_item.py    # InventoryItem: для инвентаризации
│   │   ├── count_item.py        # CountItem: элемент подсчёта
│   │   └── __init__.py          # Маркер пакета
│   ├── i18n/                    # Интернационализация: messages.py
│   ├── inventory_parser/        # Парсинг файлов инвентаризации: core.py
│   ├── parsers/                 # Заглушка для будущих парсеров
│   ├── path_utils/              # Утилиты работы с путями: core.py
│   ├── printing/                # Генерация этикеток: sticker_generator.py
│   ├── repository/              # Абстракции доступа к данным:
│   │   ├── interfaces.py        # IRepository: абстрактные методы
│   │   └── sqlite_impl.py       # SQLite-реализация интерфейсов
│   ├── scanner_input/           # Обработка ввода сканеров:
│   │   ├── interfaces.py        # ScannerProvider: абстрактный интерфейс
│   │   ├── hid_scanner.py       # HID-режим сканера (клавиатурная эмуляция)
│   │   ├── buffer.py            # Буфер ввода для сканера
│   │   └── camera_stub.py       # Заглушка для камеры
│   ├── ui_components/           # Переиспользуемые UI-компоненты: accordion.py
│   └── utils/
│       ├── address_formatter.py # AddressFormatter: парсинг/форматирование адресов
│       ├── fuzzy_search.py      # FuzzyFilter: нечёткий поиск с эвристиками
│       ├── file_naming.py       # Утилиты генерации имён файлов
│       └── __init__.py          # Маркер пакета
│
└── services/                    # Application Layer (бизнес-логика)
    ├── __init__.py              # Маркер пакета
    ├── di_container.py          # DIContainer: регистрация/получение зависимостей
    ├── interfaces/              # Абстракции сервисов (используются в gui/):
    │   └── __init__.py          # ISearchService, IProductRepository, etc. (содержит только __init__.py)
    └── stubs/                   # Заглушки для разработки:
        └── __init__.py          # StubSearchService, etc. (содержит только __init__.py)
```

---

## 🧱 Детальное описание модулей

### 🔹 `main.py` — Точка входа
**Ответственность:** Инициализация приложения, загрузка конфига, настройка DI, запуск GUI.
**Ключевые шаги:**
1. `load_config()` → загрузка `config/app_config.json`
2. `quick_bootstrap()` → настройка логгера, обработчика исключений
3. Создание адаптеров БД: `NomenclatureAdapter`, `StoreAdapter`, `CssExportAdapter`
4. Инициализация `ProductDetailsService` (агрегация 3 источников)
5. Регистрация сервисов в `DIContainer`
6. Создание `ctk.CTk()` → `MainWindow` → `mainloop()`
**Особенности:**
- Использует ТОЛЬКО реальные БД (моки удалены)
- Все соединения с БД — read-only (`?mode=ro`)
- Потокобезопасность: каждое соединение создаётся в своём потоке

---

### 🔹 `gui/main_window.py` — `class MainWindow(ctk.CTkFrame)`
**Ответственность:** Корневое окно, управление вкладками, диалогами, глобальными действиями.
**Атрибуты:**
- `_container: DIContainer` — доступ к сервисам
- `_search_service: ISearchService`, `_settings_service: ISettingsService`
- `_notebook: CTkTabview` — контейнер вкладок
- `_search_tab: SearchAddressTab`, `_inventory_tab: InventoryTab`
**Методы:**
- `__init__(master, di_container)` — инициализация, загрузка иконок
- `_load_icon(filename, size)` — загрузка CTkImage с обработкой ошибок
- `_create_ui()` — сборка: top-bar, кнопки, табы, контент-фрейм
- `_on_tab_change()` — переключение видимости вкладок
- `_on_search_result(products)` — передача результатов в вкладку
- `_open_settings()`, `_on_setting_changed(key, value)` — работа с настройками
- `_open_help()` — заглушка справки
**Зависимости:** `customtkinter`, `PIL`, `gui.tabs.*`, `gui.dialogs.*`, `services.interfaces`

---

### 🔹 `gui/product_details.py` — `class ProductDetails(ItemsListBase)`
**Ответственность:** Отображение карточки товара (readonly-поля, динамические адреса).
**Атрибуты:**
- `_product_repo: ProductRepoService` — доступ к данным
- `_current_product: Optional[Product]` — текущий товар
- `_address_formatter: AddressFormatter` — форматирование адресов
- `_address_entries: list` — ссылки на виджеты адресов
**Методы:**
- `__init__(master, product_repo, on_add_to_queue, font_size, details_service, address_formatter)`
- `_create_field_row(parent, row, label, field_name)` — создание строки поля
- `_on_info_click()`, `_on_add_to_queue_click()` — обработчики кнопок
- `_open_editor(field_name)`, `_get_field_value(field_name)` — редактирование
- `_render_addresses()` — отрисовка адресов (режимы: compact/with_labels)
- `_render_addresses_with_labels()`, `_render_addresses_compact()` — варианты рендера
- `_render_incompatible_address(addr_str, row, col)` — fallback для неформатируемых
- `set_product(product)` — обновление UI данными товара (с `after_idle` для безопасности)
- `clear()`, `get_current_product()`
**Особенности:**
- Все поля ввода — `state="disabled"` (readonly)
- Адреса рендерятся динамически с учётом `AddressFormatConfig`
- Использует `after_idle()` для безопасной отрисовки после layout-событий
- Проверка `winfo_exists()` перед обращением к виджетам

---

### 🔹 `gui/search_bar.py` — `class SearchBar(ctk.CTkFrame)`
**Ответственность:** Поле поиска с debounce, автодополнением, обработкой ввода.
**Ключевые компоненты:**
- Дебаунс 300мс через `threading.Timer`
- Регистронезависимый поиск с поддержкой кириллицы и спецсимволов
- Ограничение выдачи: 50 товаров
- Callback `on_search(query)` для передачи запроса в сервис
- `SuggestionList` — выпадающий список подсказок с клавиатурной навигацией
**Методы:**
- `_on_key_release(event)` — запуск таймера дебаунса
- `_do_search(query)` — вызов `search_service.search_async()`
- `_on_search_complete(products)` — обработка результатов, показ подсказок
- `_show_suggestions()`, `_hide_suggestions()` — управление dropdown
- `apply_settings(config)` — применение настроек шрифта/автофокуса

---

### 🔹 `gui/services/adapters/*.py` — Адаптеры БД
**Общая ответственность:** Обёртки над SQLite с потокобезопасным доступом.
**Общие черты всех адаптеров:**
- Ленивая инициализация соединения (`_get_connection()`)
- Каждое соединение создаётся в своём потоке (потокобезопасность)
- Режим read-only: `sqlite3.connect(f"file:{path}?mode=ro", uri=True)`
- Динамическое определение имени таблицы через `sqlite_master`
- Обработка ошибок с логированием, возврат пустых списков при сбое

#### `NomenclatureAdapter`
- `search(query: str) → List[Product]` — регистронезависимый поиск по article/name/barcodes
- `get_by_article(article: str) → Optional[Product]` — точный поиск
- Парсинг JSON-поля `barcodes` из БД

#### `StoreAdapter`
- `get_all_locations(article: str) → List[str]` — получение всех адресов (из JSON-поля `locations`)
- `update_location(article: str, location: str)` — добавление адреса к списку
- `set_locations(article: str, locations: List[str], notes: str)` — полная замена списка

#### `CssExportAdapter`
- `get_by_article(article: str) → List[Dict[str, Any]]` — информация о запчастях для разных моделей
- `search_by_name(query: str) → List[Dict[str, Any]]` — поиск по названию детали

---

### 🔹 `gui/services/product_details_service.py` — `class ProductDetailsService`
**Ответственность:** Агрегация данных о товаре из трёх источников.
**Методы:**
- `get_product_details(article: str, callback: Optional[Callable] = None) → Optional[Product]` — основной метод (синхронный/асинхронный)
- `_fetch_all_data(article: str)` — сборка данных:
  1. `nomenclature.db` → базовые поля (article, name, barcodes, unit)
  2. `store.db` → `storage_locations` (список адресов)
  3. `css_export.db` → `manufacturer_info`, `models`, `category`
- `_get_nomenclature_data()`, `_get_storage_locations()`, `_get_manufacturer_info()` — приватные методы-источники
**Особенности:**
- Асинхронный режим через `threading.Thread` с callback
- Логирование отладочных данных (`[DEBUG_TEMP]`) для трассировки обогащения
- Возвращает `Product` с заполненными полями или `None` при ошибке

---

### 🔹 `services/di_container.py` — `class DIContainer`
**Ответственность:** Централизованная регистрация и получение зависимостей.
**Методы:**
- `register(interface: Type, implementation: Any)` — регистрация сервиса
- `get(interface: Type) → Any` — получение сервиса (KeyError если не найден)
- `has(interface: Type) → bool` — проверка наличия
- `register_default_services()` — регистрация заглушек (для разработки без БД)
- `register_real_services(config: Dict[str, Any])` — TODO: регистрация реальных сервисов
**Интерфейсы (из `services/interfaces/`):**
- `ISearchService`, `IProductRepository`, `IImageService`, `IPrinterService`, `ISettingsService`, `IInventoryService`
**Заглушки (из `services/stubs/`):**
- `StubSearchService`, `StubProductRepository`, `StubImageService`, `StubPrinterService`, `StubSettingsService`, `StubInventoryService`

---

### 🔹 `libs/domain_models/` — Чистые DTO
**Принцип:** Только данные, без логики, без зависимостей от фреймворков.

#### `Product` (dataclass)
```python
article: str
name: str
barcodes: List[str] = field(default_factory=list)
address: Optional[str] = None
unit: Optional[str] = None
description: Optional[str] = None
category: Optional[str] = None
manufacturer_info: List[Dict[str, Any]] = field(default_factory=list)
storage_locations: List[str] = field(default_factory=list)
models: List[str] = field(default_factory=list)

def matches_article_or_barcode(self, code: str) -> bool: ...
```

#### `Address` (dataclass)
```python
code: str
description: Optional[str] = None
quantity: int = 0

def __str__(self) -> str: ...
def __eq__(self, other: object) -> bool: ...
def __hash__(self) -> int: ...
```

---

### 🔹 `libs/utils/address_formatter.py` — `class AddressFormatter`
**Ответственность:** Парсинг, форматирование, валидация строк адресов.
**Конфигурация (`AddressFormatConfig`):**
- `enabled: bool` — включено ли форматирование
- `display_mode: str` — `"compact"` или `"with_labels"`
**Методы:**
- `parse(address_str: str) → Dict[str, Any]` — разбор строки в словарь уровней (склад, секция, полка, ячейка)
- `format_with_labels(values: Dict[str, Any]) → List[Tuple[str, str]]` — форматирование с подписями
- `is_compatible(address_str: str) → Tuple[bool, str]` — проверка соответствия формату
- `get_level_names() → List[str]` — список уровней адресации

---

### 🔹 `libs/utils/fuzzy_search.py` — `class FuzzyFilter`
**Ответственность:** Нечёткий поиск с эвристиками.
**Режимы поиска:**
- `exact` — точное совпадение
- `startswith` — начало строки
- `contains` — подстрока
- `fuzzy` — эвристика: символы запроса в правильном порядке (≥80% совпадения)
- `regex` — регулярное выражение
**Методы:**
- `filter(items: List[Any], query: str, mode: str, key_extractor: Optional[Callable] = None) → List[Any]` — фильтрация списка
- `highlight(text: str, query: str, open_tag: str, close_tag: str) → str` — подсветка совпадений

---

### 🔹 `libs/core/bootstrap.py` — `class Bootstrap`
**Ответственность:** Инициализация приложения: логгер, исключения, валидация окружения.
**Компоненты:**
- `BootstrapConfig` — конфигурация инициализации
- `Bootstrap.run(config: BootstrapConfig)` — последовательность: `_setup_logging()` → `_setup_exception_handler()` → `_validate_environment()`
- `quick_bootstrap(app_name: str, log_level: int, log_file: Optional[str] = None, force_log_file: bool = False)` — утилита для быстрой настройки
**Особенности:**
- Глобальный обработчик исключений с логированием и callback
- Валидация: версия Python ≥3.8, права на запись, переменные окружения
- Логирование: консоль + опционально файл, с ротацией через `force=True`

---

### 🔹 `libs/printing/sticker_generator.py` — `class StickerGenerator`
**Ответственность:** Генерация изображений этикеток с штрих-кодами.
**Возможности:**
- Размеры в мм → пиксели (DPI-конвертация)
- Штрих-коды: Code128, EAN13 (с fallback), QR-коды
- Текст с переносом строк (`_wrap_text`)
- Кэширование шрифтов, поиск системных шрифтов Windows
- Пресеты оформления через конфиг
**Методы:**
- `generate(article: str, name: str, address: str, quantity: int, unit: str, barcode_type: str, preset: Dict[str, Any]) → Image.Image`
- `_create_base_image()` — создание холста с фоном/границей
- `_get_font(size_pt: int, bold: bool, italic: bool, font_family: Optional[str]) → CTFont` — кэшированный доступ к шрифтам
- `save(image: Image.Image, path: str)` — сохранение в PNG

---

### 🔹 `libs/scanner_input/interfaces.py` — `class ScannerProvider(ABC)`
**Ответственность:** Абстрактный интерфейс для всех источников штрих-кодов.
**Контракт:**
- `start_listening()` / `stop_listening()` — управление прослушиванием
- `set_callback(callback: Callable[[str], None])` — установка обработчика кодов
- `_notify_callback(code: str)` — уведомление подписчика
- `is_active: bool` — свойство-флаг активности
**Реализации (в других файлах):**
- `hid_scanner.py` — HID-режим (клавиатурная эмуляция)
- `buffer.py` — буферизация ввода
- `camera_stub.py` — заглушка для камеры

---

## 🗄️ Базы данных: схемы и связи

### `nomenclature.db` (внутренняя номенклатура)
| Таблица | Поля | Записей |
|---------|------|---------|
| `nomenclature` | `canonical_article`, `name_ru`, `alternative_articles` (JSON), `unit` | ~1 693 |
**Роль:** Основной справочник с русскими наименованиями и альтернативными артикулами.

### `store.db` (складские адреса)
| Таблица | Поля | Особенность |
|---------|------|-------------|
| `storage_locations` | `article`, `locations` (JSON-массив), `alternative_names` (JSON) | Один артикул → несколько адресов |

### `css_export.db` (запчасти Franke)
| Таблица | Поля | Записей |
|---------|------|---------|
| `spare_parts` | `art_no`, `product_model`, `name`, `usage_path`, `category1-3`, `production_date_*`, `serial_*` | ~24 678 записей, 20 моделей |

### Схема связей
```
nomenclature.canonical_article ←→ store.article
                     ↓
nomenclature.alternative_articles (JSON) ←→ css_export.art_no
```
**Поток данных при поиске:**
1. Пользователь вводит запрос → `SearchBar`
2. `SearchBar` → `NomenclatureAdapter.search()` (через `ISearchService`)
3. `NomenclatureAdapter` → SQL-запрос → список `Product` (без адресов)
4. `ProductDetailsService.get_product_details()` → обогащение:
   - `store_adapter.get_all_locations()` → `storage_locations`
   - `css_adapter.get_by_article()` → `manufacturer_info`, `models`
5. Результат → callback в `SearchAddressTab` → обновление UI
6. Выбор товара → `ProductDetails.set_product()` → отрисовка полей + адресов

---

## ⚠️ Критические правила (из MANIFEST.md)

1. **Слои:** `gui/` → `services/` → `interfaces` → `libs/` (строго сверху вниз)
2. **Запрещено в `gui/`:** бизнес-логика, прямые запросы к БД, хардкод путей
3. **DI:** все зависимости внедряются через `DIContainer`, не создаются в `__init__` виджетов
4. **Потоки:** обновление GUI из background-threads только через `root.after(0, ...)`
5. **Тестируемость:** бизнес-логика должна работать без GUI (headless)
6. **Коммиты:** префиксы `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`
7. **Закон Деметры:** виджеты не лезут во внутренности друг друга, только через интерфейсы
8. **Fail Fast:** проверки `winfo_exists()`, валидация входных данных, логирование ошибок

---

## 📦 Модули-заглушки (готовятся к реализации)

| Модуль | Статус | Примечание |
|--------|--------|------------|
| `gui/tabs/inventory_tab.py` | 🚧 В разработке | Заглушка с кнопками-плейсхолдерами |
| `libs/inventory_parser/` | 🚧 Готовится | Парсинг Excel-файлов инвентаризации |
| `libs/scanner_input/camera_stub.py` | 🚧 Заглушка | Будущая поддержка камер |
| `libs/parsers/` | 🚧 Пустой | Резерв для будущих парсеров накладных |
| `services/interfaces/*.py` | ✅ Только `__init__.py` | Интерфейсы объявляются по мере необходимости |
| `services/stubs/*.py` | ✅ Только `__init__.py` | Заглушки сервисов для разработки |

---

*Документ сгенерирован автоматически. Актуальность: 2026-06-01*
