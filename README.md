# ScanHead Combine v2.2

Модульное ядро системы инвентаризации и управления складом.
Агрегирует данные из трёх SQLite-баз (номенклатура, адреса хранения, запчасти Franke).

## 🎯 Цель
Разделение монолитного legacy-проекта на независимые модули с чёткими интерфейсами.

## 🖥️ Стек
Гибридный ttk + tk — в каждом GUI-файле ОБА импорта:
- import tkinter as tk
- from tkinter import ttk

Попытка использовать только ttk ломает интерфейс (проверено).

## 📦 Структура проекта

scanhead-core/
├── main.py                    # Точка входа + DI-контейнер
├── config/app_config.json     # Конфигурация приложения
├── data/
│   ├── databases/             # 3 SQLite БД (read-only, только на тестовой машине)
│   ├── icons/                 # 14 PNG-иконок
│   └── images/                # noimage.png
├── gui/                       # Presentation Layer
│   ├── main_window.py         # Корневое окно
│   ├── search_bar.py          # Поиск с debounce
│   ├── product_details.py     # Карточка товара
│   ├── print_queue.py         # Очередь печати
│   ├── sticker_preview.py     # Превью этикетки
│   ├── tabs/                  # SearchAddressTab, InventoryTab
│   ├── dialogs/               # SettingsDialog, FieldEditor, StickerEditor, ProductInfoDialog
│   ├── widgets/               # SuggestionList
│   ├── framework/             # DialogBase, ListBase
│   └── services/              # ProductDetailsService + адаптеры БД
├── libs/                      # Domain + Infrastructure
│   ├── domain_models/         # Product, Address, InventoryItem
│   ├── utils/                 # address_formatter, fuzzy_search
│   ├── printing/              # sticker_generator
│   ├── config/                # ConfigManager, PresetManager
│   ├── repository/            # SQLite-реализации репозиториев
│   └── core/                  # Bootstrap, логгер
├── services/                  # DI + интерфейсы
│   ├── di_container.py        # DIContainer
│   ├── interfaces/            # Абстракции (ISearchService и др.)
│   ├── stubs/                 # Заглушки для тестов
│   └── config_manager_adapter.py  # Адаптер ConfigManager → ISettingsService
└── docs/                      # Схемы БД, API

## 🗄️ Базы данных (read-only)

| База           | Таблица             | Записей | Роль                                    |
|----------------|---------------------|---------|-----------------------------------------|
| nomenclature.db| nomenclature        | 1 693   | Основной справочник (article, name_ru)  |
| store.db       | storage_locations   | —       | Адреса хранения (JSON-поле locations)   |
| css_export.db  | spare_parts         | 24 678  | Запчасти Franke                         |

Физические .db файлы — только на тестовой машине. В репозитории — схемы и README.

## ✅ Возможности GUI
- Поиск: регистронезависимый, debounce 300 мс, кириллица + спецсимволы, лимит 50 товаров
- Отображение: агрегация из 3 БД, readonly-карточка, динамический рендер адресов
- Печать: генерация этикеток (Code128/EAN13/QR), превью, очередь заданий
- Настройки: тема, язык, шрифт поиска, формат адреса, пресеты стикеров (сохраняются в config/app_config.json)

## 🛡️ Архитектура
Строгая многослойность: gui/ → services/ → libs/ (сверху вниз).
DI через DIContainer, потокобезопасность через root.after(0, ...).

Правила и запреты — см. MANIFEST.md
Детальная карта модулей — см. current_structure.MD

## 🔜 Планы
- ✅ Базовое GUI (ветка main-gui)
- ✅ Сохранение настроек через ConfigManagerSettingsAdapter
- 🚧 Парсеры накладных
- 🚧 Поддержка камеры
- 🚧 Полноценная вкладка "Инвентаризация"

## 📚 Документация
- MANIFEST.md — архитектурные принципы и запреты
- current_structure.MD — детальная структура проекта
- docs/database_schema.md — схемы БД и связи
- docs/services_api.md — API сервисов

Версия 2.2 | Гибридный стек ttk+tk | read-only БД | DI контейнер