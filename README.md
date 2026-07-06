# ScanHead Combine v0.3.0

Модульное десктопное приложение для инвентаризации и управления складом.
Агрегирует данные из трёх SQLite-баз (номенклатура, адреса хранения, запчасти Franke).

---

## 📊 Прогресс разработки

Автоматически обновляемый дашборд доступен по адресу:
https://servicenikov-afk.github.io/scanhead-core/dashboard.html

---

## 🖥️ Стек

Гибридный ttk + tk — в каждом GUI-файле ОБА импорта:
```python
import tkinter as tk
from tkinter import ttk
```

---

## 📦 Структура проекта

```
scanhead-core/
├── main.py                          # Точка входа + DI-контейнер
├── config/app_config.json           # Конфигурация приложения
├── data/
│   ├── databases/                   # 3 SQLite БД (только на тестовой машине)
│   ├── icons/                       # 14 PNG-иконок
│   └── images/                      # noimage.png
├── gui/                             # Presentation Layer
│   ├── main_window.py               # Корневое окно
│   ├── product_details.py           # Карточка товара
│   ├── search_bar.py                # Поиск с debounce
│   ├── print_queue.py               # Очередь печати
│   ├── sticker_preview.py           # Превью этикетки
│   ├── tabs/                        # SearchAddressTab, InventoryTab
│   ├── dialogs/                     # SettingsDialog, StickerEditor, ProductInfoDialog и др.
│   ├── widgets/                     # SuggestionList
│   └── services/                    # ProductDetailsService + адаптеры БД
├── libs/                            # Domain + Infrastructure
│   ├── domain_models/               # Product, Address, InventoryItem
│   ├── utils/                       # address_formatter, fuzzy_search, file_naming
│   ├── printing/                    # sticker_generator, pdf_renderer
│   └── config_manager/              # ConfigManager
├── services/                        # DI + интерфейсы + сервисы
│   ├── di_container.py              # DIContainer
│   ├── interfaces/                  # Абстракции (ISearchService и др.)
│   ├── stubs/                       # Заглушки для тестов
│   ├── config_manager_adapter.py    # Адаптер ConfigManager → ISettingsService
│   ├── printer_service.py           # Реальный сервис печати
│   └── presets_config_utils.py      # Конвертация пресетов
└── docs/                            # Схемы БД, API
```

---

## 🗄️ Базы данных

| База | Таблица | Записей | Роль | Режим |
|------|---------|---------|------|-------|
| nomenclature.db | nomenclature | 1 693 | Основной справочник | read-only |
| store.db | storage_locations | — | Адреса хранения (JSON) | **запись** |
| css_export.db | spare_parts | 24 678 | Запчасти Franke | read-only |

Физические .db файлы — только на тестовой машине. В репозитории — схемы и README.

---

## ✅ Возможности GUI

- **Поиск:** регистронезависимый, debounce 300 мс, кириллица + спецсимволы, лимит 50 товаров
- **Отображение:** агрегация из 3 БД, readonly-карточка, динамический рендер адресов
- **Печать:** генерация этикеток (Code128/EAN13/QR), превью, очередь заданий, PDF
- **Настройки:** тема, язык, шрифт поиска, формат адреса, пресеты стикеров

---

## 🛡️ Архитектура

Строгая многослойность: `gui/` → `services/` → `libs/` (сверху вниз).
DI через `DIContainer`, потокобезопасность через `root.after(0, ...)`.

Правила и запреты — см. `MANIFEST.md`
Детальная карта модулей — см. `current_structure.md`
План рефакторинга — см. `TODO.md`

---

## 🔜 Планы

- ✅ Базовое GUI
- ✅ Сохранение настроек через `ConfigManagerSettingsAdapter`
- ✅ Реальный сервис печати
- 🚧 Парсеры накладных
- 🚧 Полноценная вкладка "Инвентаризация"

---

## 📚 Документация

- `MANIFEST.md` — архитектурные принципы и запреты
- `current_structure.md` — детальная структура модулей
- `TODO.md` — план рефакторинга (06.07.2026)
- `docs/database_schema.md` — схемы БД и связи
- `docs/services_api.md` — API сервисов

---

**Версия:** 0.3.0 | **Ветка:** main | **Дата:** 06.07.2026