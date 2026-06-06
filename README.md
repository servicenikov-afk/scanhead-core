# ScanHead Combine

Модульное ядро для системы инвентаризации и управления складом. Версия 2.1.

## 🎯 Цель

Разделение монолитной логики legacy-проектов на независимые модули с четкими интерфейсами. Сборка нового приложения `scanhead-combine` на основе этих модулей.

## 🖥️ GUI стек: ttk + tk (ГИБРИДНЫЙ)

Проект использует **гибридный подход**: одновременно `import tkinter as tk` и `from tkinter import ttk`.

- `ttk` — для современных виджетов с темами оформления
- `tk` — для низкоуровневого контроля (события, координаты, фокус)

**Важно:** Попытка использовать только `ttk` приводит к поломке интерфейса. Оба импорта обязательны в каждом GUI-файле.

## 📦 Структура
├── libs/ # Библиотеки (независимые модули)
│ ├── core/ # Инфраструктура: bootstrap, инициализация
│ ├── i18n/ # Интернационализация
│ ├── domain/ # Доменная логика
│ ├── repository/ # Доступ к данным
│ ├── scanner_input/ # Обработка ввода сканеров (HID)
│ ├── printing/ # Генерация этикеток (Pillow)
│ ├── config/ # PresetManager
│ ├── utils/ # address_formatter, fuzzy_search
│ └── ... # Другие модули
│
├── gui/ # GUI приложение (ttk+tk)
│ ├── main_window.py # Корневое окно
│ ├── search_bar.py # Поиск с debounce и подсказками
│ ├── product_details.py # Детали товара (readonly)
│ ├── print_queue.py # Очередь печати
│ ├── sticker_preview.py # Предпросмотр этикетки
│ ├── tabs/ # SearchAddressTab, InventoryTab (заглушка)
│ ├── dialogs/ # SettingsDialog, FieldEditor, StickerEditor
│ ├── framework/ # DialogBase, ListBase
│ └── services/ # ProductDetailsService + адаптеры БД
│
├── services/ # DI контейнер, интерфейсы, заглушки
├── config/ # app_config.json
├── data/ # Иконки, изображения, README для БД
└── main.py # Точка входа

text

## 🗄️ Базы данных (read-only)

Проект агрегирует данные из трёх SQLite-источников:

| База | Таблица | Записей | Роль |
|------|---------|---------|------|
| `nomenclature.db` | `nomenclature` | 1 693 | Основной справочник (canonical_article, name_ru) |
| `store.db` | `storage_locations` | — | Адреса хранения (JSON-поле `locations`) |
| `css_export.db` | `spare_parts` | 24 678 | Запчасти Franke (артикулы производителя) |

**Важно:** Физические файлы `.db` находятся **только на тестовой машине**. В репозитории — только схемы и README.

## 🔧 Модули

| Модуль | Версия | Статус |
|--------|--------|--------|
| `core/bootstrap` | 2.1.0 | ✅ |
| `i18n/messages` | 2.1.0 | ✅ |
| `domain/discrepancy` | 2.1.0 | ✅ |
| `repository` | 2.1.0 | ✅ |
| `scanner_input` | 2.1.0 | ✅ |
| `utils/fuzzy_search` | 2.1.0 | ✅ |
| `utils/address_formatter` | 2.1.0 | ✅ |
| `printing/sticker_generator` | 2.1.0 | ✅ |
| `config/preset_manager` | 2.1.0 | ✅ |
| `command_handler` | 2.1.0 | ✅ |
| `domain_models` | 2.1.0 | ✅ |
| `data_exporters` | 2.1.0 | ✅ |
| `ui_components` | 2.1.0 | ✅ |
| `gui/framework` | 2.1.0 | ✅ |
| `gui/tabs/search_address_tab` | 2.1.0 | ✅ |
| `gui/tabs/inventory_tab` | 2.1.0 | 🚧 |

## ✅ Возможности GUI (v2.1)

### Поиск
- Регистронезависимый поиск по артикулу, наименованию и штрих-кодам
- Корректная работа с кириллицей и спецсимволами (дефис, проценты и др.)
- Debounce 300 мс для оптимизации
- Ограничение выдачи: 50 товаров

### Отображение товаров
- Агрегация данных из трёх БД через `ProductDetailsService`
- Read-only поля карточки товара
- Динамический рендеринг адресов (компактный / с подписями)
- Корректный парсинг JSON-полей (`barcodes`, `locations`)

### Печать
- Генерация этикеток со штрих-кодами (Code128/EAN13)
- Предпросмотр перед печатью
- Очередь заданий

## 🛡️ Архитектурные правила

1. **Слои:** `gui/` → `services/` → `libs/` (строго сверху вниз)
2. **Гибридный стек:** в каждом GUI-файле оба импорта (`import tkinter as tk` И `from tkinter import ttk`)
3. **DI:** зависимости внедряются через `DIContainer`, не создаются в виджетах
4. **Потоки:** обновление GUI из фона только через `root.after(0, ...)`
5. **БД:** read-only соединения (`?mode=ro`), каждое в своём потоке
6. **Коммиты:** префиксы `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`

## 📚 Документация

- [`MANIFEST.md`](MANIFEST.md) — архитектурные принципы и запреты
- [`current_structure.MD`](current_structure.MD) — детальная структура проекта
- [`docs/database_schema.md`](docs/database_schema.md) — схемы БД и связи
- [`docs/services_api.md`](docs/services_api.md) — API сервисов

## 🔜 Планы

1. ✅ Базовое GUI (ветка `main-gui`) — стабильная версия на гибридном ttk+tk
2. 🚧 Парсеры накладных
3. 🚧 Поддержка камеры (вместо ручного ввода)
4. 🚧 Вкладка "Инвентаризация" (полноценная реализация)

---

**Версия 2.1 | Гибридный стек ttk+tk | read-only БД | DI контейнер**