# Структура проекта ScanHead Core

**Ветка:** gui-framework-dev | **Версия:** 0.3.0 | **Дата:** 06.07.2026

⚠️ Реальные БД (.db) — только на тестовой машине. В репозитории — схемы (.sql) и README.

📜 Архитектурные правила — см. MANIFEST.md
📖 Обзор проекта — см. README.md
📋 План рефакторинга — см. TODO.md

---

## 🔹 main.py — Точка входа

**Слой:** Application Bootstrap / Composition Root
**Назначение:** Инициализация логирования, загрузка конфига, настройка DI-контейнера, создание MainWindow, запуск mainloop.

**Ключевые зависимости:** customtkinter, libs.core.quick_bootstrap, gui.main_window.MainWindow, services.di_container.DIContainer, services.config_manager_adapter.ConfigManagerSettingsAdapter

⚠️ **Соответствие манифесту:** ⚠️ Требует доработки
- Импорты внутри main() затрудняют статический анализ
- Жёсткие пути к БД по умолчанию в коде
- Смешивание ответственностей: логирование + DI + GUI-тема
- Создание root до регистрации сервисов

---

## 🔹 gui/main_window.py — MainWindow

**Слой:** UI (Presentation)
**Назначение:** Главный контейнер UI, навигация по вкладкам, маршрутизация событий.

**Ключевые зависимости:** customtkinter, PIL.Image, gui.tabs.*, gui.dialogs.settings_dialog, services.di_container, services.interfaces

✅ **Соответствие манифесту:** ✅ Полностью соответствует
- 🗑️ Неиспользуемые: `_img_help`, `_img_settings` (загружаются, но не применяются)

---

## 🔹 gui/product_details.py — ProductDetails

**Слой:** UI (Presentation)
**Назначение:** Readonly-панель деталей товара с редактированием через модалки.

**Ключевые зависимости:** customtkinter, services.interfaces.IProductRepository, libs.domain_models, gui.dialogs.*, libs.utils.AddressFormatter

❌ **Соответствие манифесту:** ❌ Критические нарушения
- Прямые импорты диалогов вместо фабрик
- Нарушение SRP: отображение + лейаут + навигация + сохранение
- Прямая работа с репозиторием в UI
- 🗑️ Мёртвый код: `_render_incompatible_address()`, `show_edit_btn`

---

## 🔹 gui/search_bar.py — SearchBar

**Слой:** UI (Presentation)
**Назначение:** Поиск с debounce, автодополнение, асинхронный поиск.

**Ключевые зависимости:** customtkinter, services.interfaces.ISearchService, libs.domain_models.Product, gui.widgets.suggestion_list

❌ **Соответствие манифесту:** ❌ Нарушение потокобезопасности
- threading.Timer для debounce — должен быть widget.after()
- Callback из фонового потока

---

## 🔹 gui/print_queue.py — PrintQueue

**Слой:** UI (Presentation)
**Назначение:** Очередь печати на базе ttk.Treeview с inline-редактированием.

**Ключевые зависимости:** customtkinter, tkinter.ttk, services.interfaces.*, libs.domain_models.Product

❌ **Соответствие манифесту:** ❌ Критические нарушения
- Нарушение DIP/IOC: жёсткая привязка к CustomTkinter
- Нарушение SRP: отображение + состояние + редактирование + печать
- 🗑️ Мёртвый код: `_toggle_column_menu`, `_import_from_file`
- 🗑️ Неиспользуемый параметр: `_product_repo`
- Глобальный флаг `_theme_applied` — нарушение инкапсуляции

---

## 🔹 gui/sticker_preview.py — StickerPreview

**Слой:** UI (Presentation)
**Назначение:** Превью макета этикетки, точка входа в редактор пресетов.

**Ключевые зависимости:** customtkinter, PIL, services.interfaces.*, libs.domain_models.Product, gui.dialogs.sticker_editor

✅ **Соответствие манифесту:** ✅ Полностью соответствует

---

## 🔹 gui/dialogs/settings_dialog.py — SettingsDialog

**Слой:** UI (Presentation)
**Назначение:** Модалка настроек (тема, язык, поиск, формат адреса).

**Ключевые зависимости:** customtkinter, services.interfaces.ISettingsService

✅ **Соответствие манифесту:** ✅ Полностью соответствует

---

## 🔹 gui/dialogs/sticker_editor.py — StickerEditor

**Слой:** UI (Presentation)
**Назначение:** Редактор пресетов стикеров.

**Ключевые зависимости:** customtkinter, tkinter, services.interfaces.ISettingsService, libs.domain_models.Product, libs.printing.sticker_generator, services.presets_config_utils

✅ **Соответствие манифесту:** ✅ Полностью соответствует

---

## 🔹 gui/dialogs/product_info_dialog.py — ProductInfoDialog

**Слой:** UI (Presentation)
**Назначение:** Модалка деталей товара с 3 вкладками.

**Ключевые зависимости:** customtkinter, gui.services.product_details_service, libs.domain_models.Product, libs.utils.AddressFormatter

❌ **Соответствие манифесту:** ❌ Критические нарушения
- Нарушение SRP: UI + парсинг адресов + работа с БД + async
- Прямая зависимость от адаптеров в UI
- 🗑️ Мёртвый код: `_load_details_legacy()`
- `_unsaved_changes` — состояние должно управляться сервисом

---

## 🔹 gui/dialogs/field_editor.py — FieldEditor

**Слой:** UI (Presentation)
**Назначение:** Модалка редактирования одного поля товара.

**Ключевые зависимости:** customtkinter, services.interfaces.IProductRepository

✅ **Соответствие манифесту:** ✅ Полностью соответствует
- 🗑️ Неиспользуемый параметр: `product_id`

---

## 🔹 gui/dialogs/add_address_dialog.py — AddAddressDialog

**Слой:** UI (Presentation)
**Назначение:** Модалка добавления адреса (структурированный/свободный ввод).

**Ключевые зависимости:** customtkinter, libs.utils.AddressFormatter, AddressFormatConfig

✅ **Соответствие манифесту:** ✅ Полностью соответствует

---

## 🔹 gui/dialogs/print_confirm_dialog.py — PrintConfirmDialog

**Слой:** UI (Presentation / Dialogs)
**Назначение:** Диалог подтверждения печати с прогресс-баром.

**Ключевые зависимости:** customtkinter, tkinter

✅ **Соответствие манифесту:** ✅ Полностью соответствует
- Потокобезопасный (root.after)
- Автозакрытие через 1.2 сек

---

## 🔹 gui/tabs/search_address_tab.py — SearchAddressTab

**Слой:** UI (Presentation)
**Назначение:** Композитная вкладка "Поиск | Адрес".

**Ключевые зависимости:** customtkinter, services.di_container.DIContainer, services.interfaces.*, gui.*, libs.utils.AddressFormatter

❌ **Соответствие манифесту:** ❌ Критические нарушения
- Бизнес-логика обогащения в UI
- 🗑️ DEBUG_TEMP-логирование
- Импорт внутри метода (нарушение PEP 8)
- Небезопасный callback из потока

---

## 🔹 gui/tabs/inventory_tab.py — InventoryTab

**Слой:** UI (Presentation)
**Назначение:** Заглушка вкладки "Инвентаризация".

**Ключевые зависимости:** customtkinter, services.di_container.DIContainer

⚠️ **Соответствие манифесту:** ⚠️ Требует доработки
- DI-контейнер внедряется, но не используется
- master: Any вместо ctk.CTkBaseClass

---

## 🔹 gui/widgets/suggestion_list.py — SuggestionList

**Слой:** UI (Presentation / Widgets)
**Назначение:** Всплывающий dropdown автодополнения.

**Ключевые зависимости:** customtkinter, typing, logging

✅ **Соответствие манифесту:** ✅ Полностью соответствует

---

## 🔹 gui/services/adapters/nomenclature_adapter.py — NomenclatureAdapter

**Слой:** Adapters (Infrastructure)
**Назначение:** Адаптер к nomenclature.db.

**Ключевые зависимости:** sqlite3, threading, json, pathlib, libs.domain_models.Product

⚠️ **Соответствие манифесту:** ⚠️ Требует доработки
- Фильтрация в Python вместо индексированного SQL
- search_async вызывает callback напрямую в фоне
- Несогласованность соединений
- Нет интерфейса

---

## 🔹 gui/services/adapters/store_adapter.py — StoreAdapter

**Слой:** Adapters (Infrastructure)
**Назначение:** CRUD адресов хранения в store.db.

**Ключевые зависимости:** sqlite3, threading, pathlib, json

❌ **Соответствие манифесту:** ❌ Критические нарушения
- ❌ **Read-only нарушение:** соединение НЕ в режиме `?mode=ro`
- Хрупкий путь: parent.parent.parent.parent
- Подавление исключений (нарушает "Fail Fast")
- INSERT OR REPLACE удаляет старую запись
- Нет интерфейса

---

## 🔹 gui/services/adapters/css_export_adapter.py — CssExportAdapter

**Слой:** Adapters (Infrastructure / Legacy)
**Назначение:** Адаптер к css_export.db.

**Ключевые зависимости:** sqlite3, pathlib, threading

⚠️ **Соответствие манифесту:** ⚠️ Требует доработки
- Жёсткий путь по умолчанию в сигнатуре
- Фоллбэк на Path.cwd() опасен для PyInstaller
- Нет интерфейса

---

## 🔹 gui/services/adapters/json_mock_loader.py — JsonMockLoader 🗑️

**Слой:** Adapters (Deprecated)
**Назначение:** Загрузка тестовых данных из JSON.

❌ **Соответствие манифесту:** 🗑️ **УДАЛЁН** (06.07.2026)
- Мёртвый код (YAGNI)

---

## 🔹 gui/services/product_details_service.py — ProductDetailsService

**Слой:** Application Services
**Назначение:** Агрегация данных из 3 БД в доменную модель Product.

**Ключевые зависимости:** libs.domain_models.Product, адаптеры БД, threading

❌ **Соответствие манифесту:** ❌ Критические нарушения
- Прямое обращение к `_get_connection()` + сырой SQL
- Дублирование логики адаптера
- Прямой callback из потока (без root.after)
- 🗑️ DEBUG_TEMP-логи
- Нет интерфейса

---

## 🔹 services/config_manager_adapter.py — ConfigManagerSettingsAdapter

**Слой:** Application Services (Адаптер)
**Назначение:** Адаптер между ISettingsService и легаси ConfigManager.

**Ключевые зависимости:** services.interfaces.ISettingsService, libs.config_manager.ConfigManager

✅ **Соответствие манифесту:** ✅ Полностью соответствует
- ⚠️ Огромный default_config в коде (рекомендуется вынести)

---

## 🔹 services/presets_config_utils.py — PresetsConfigUtils

**Слой:** Application Services (Утилиты)
**Назначение:** Конвертация форматов пресетов стикеров (flat ↔ nested).

**Ключевые зависимости:** Только стандартная библиотека

✅ **Соответствие манифесту:** ✅ Полностью соответствует

---

## 🔹 services/printer_service.py — RealPrinterService

**Слой:** Application Services (Печать)
**Назначение:** Рендерит PDF и отправляет на принтер.

**Ключевые зависимости:** services.interfaces.IPrinterService, ISettingsService, libs.printing.pdf_renderer, gui.dialogs.print_confirm_dialog, tkinter, threading

✅ **Соответствие манифесту:** ✅ Полностью соответствует
- Потокобезопасный (root.after)
- Очистка temp/print/*.pdf через 30 сек
- 🗑️ generate_sticker, print_sticker — заглушки (TODO)

---

## 🔹 services/di_container.py — DIContainer

**Слой:** Application Services (Composition Root)
**Назначение:** Управление зависимостями.

**Ключевые зависимости:** services.interfaces, services.stubs

✅ **Соответствие манифесту:** ✅ Полностью соответствует

---

## 🔹 services/interfaces/__init__.py — Абстрактные интерфейсы

**Слой:** Application Services (Порты)
**Назначение:** Контракты для всех бизнес-сервисов.

**Ключевые зависимости:** abc, typing, libs.domain_models

✅ **Соответствие манифесту:** ✅ Полностью соответствует

---

## 🔹 services/stubs/__init__.py — Заглушки сервисов

**Слой:** Infrastructure (Заглушки для тестов)
**Назначение:** Stub-реализации для разработки GUI.

**Ключевые зависимости:** libs.domain_models, services.interfaces, PIL.Image, threading

✅ **Соответствие манифесту:** ✅ Полностью соответствует (для заглушек)
- ⚠️ StubSearchService вызывает callback из потока (допустимо для заглушек)

---

## 🔹 libs/domain_models/ — Доменные модели

**Слой:** Domain Models
**Назначение:** Чистые DTO (Product, Address, CountItem, InventoryItem).

**Ключевые зависимости:** Только стандартная библиотека (dataclasses, typing)

✅ **Соответствие манифесту:** ✅ Полностью соответствует

---

## 🔹 libs/printing/pdf_renderer.py — PdfStickerRenderer

**Слой:** Application Services (Рендеринг)
**Назначение:** Рендерит многостраничный PDF.

**Ключевые зависимости:** PIL.Image, libs.printing.sticker_generator, libs.domain_models.Product

✅ **Соответствие манифесту:** ✅ Полностью соответствует
- ⚠️ `self._generator` — лучше локальная переменная

---

## 🔹 libs/printing/sticker_generator.py — StickerGenerator

**Слой:** Application Services (Генерация)
**Назначение:** Генерация изображения стикера.

**Ключевые зависимости:** PIL, qrcode, barcode

⚠️ **Соответствие манифесту:** ⚠️ Требует доработки
- `self.config.update(preset)` — мутация состояния (нарушение иммутабельности)
- `finally: self.config = old_config` — восстановление конфига

---

## 🔹 libs/utils/address_formatter.py — AddressFormatter

**Слой:** Application Services / Domain Logic
**Назначение:** Парсинг, форматирование, валидация адресов.

**Ключевые зависимости:** Только стандартная библиотека

✅ **Соответствие манифесту:** ✅ Полностью соответствует

---

## 🔹 libs/utils/file_naming.py — FileNameGenerator

**Слой:** Application Services / Utils
**Назначение:** Генерация имён файлов по шаблону.

**Ключевые зависимости:** datetime, pathlib

✅ **Соответствие манифесту:** ✅ Полностью соответствует

---

## 🔹 libs/utils/fuzzy_search.py — FuzzyFilter

**Слой:** Application Services / Utils
**Назначение:** Нечёткий поиск с подсветкой.

**Ключевые зависимости:** re

✅ **Соответствие манифесту:** ✅ Полностью соответствует
- ⚠️ Жёсткий порог 0.8 в `_fuzzy_match` (рекомендуется параметризовать)

---

# 📊 Сводка соответствия манифесту

### ✅ Полностью соответствуют (20 файлов)
- gui/main_window.py
- gui/sticker_preview.py
- gui/dialogs/add_address_dialog.py
- gui/dialogs/field_editor.py
- gui/dialogs/settings_dialog.py
- gui/dialogs/sticker_editor.py
- gui/dialogs/print_confirm_dialog.py
- gui/widgets/suggestion_list.py
- services/di_container.py
- services/interfaces/__init__.py
- services/config_manager_adapter.py
- services/printer_service.py
- services/presets_config_utils.py
- libs/domain_models/**/*.py
- libs/printing/pdf_renderer.py
- libs/utils/address_formatter.py
- libs/utils/file_naming.py
- libs/utils/fuzzy_search.py

### ⚠️ Требуют доработки (9 файлов)
- main.py — импорты, пути, порядок инициализации
- gui/search_bar.py — threading.Timer → after
- gui/tabs/inventory_tab.py — неиспользуемый DI
- gui/services/adapters/nomenclature_adapter.py — SQL, callback, интерфейс
- gui/services/adapters/css_export_adapter.py — пути, интерфейс
- services/stubs/__init__.py — callback из потока
- libs/printing/sticker_generator.py — иммутабельность

### ❌ Критические нарушения (6 файлов)
- gui/product_details.py — DIP/SRP
- gui/print_queue.py — DIP/SRP/IOC
- gui/dialogs/product_info_dialog.py — SRP/DIP
- gui/services/adapters/store_adapter.py — read-only, пути, Fail Fast
- gui/services/product_details_service.py — абстракция, сырой SQL
- gui/tabs/search_address_tab.py — бизнес-логика в UI

### 🗑️ Удалён (1 файл)
- gui/services/adapters/json_mock_loader.py (06.07.2026)

---

## 🗄️ Базы данных

**Поток данных при поиске:**
1. Пользователь → SearchBar
2. SearchBar → NomenclatureAdapter.search() → список Product (без адресов)
3. ProductDetailsService.get_product_details() → обогащение:
   - store_adapter.get_all_locations() → storage_locations
   - css_adapter.get_by_article() → manufacturer_info
4. Результат → callback → обновление UI

---

## 📋 Модули-заглушки

| Модуль | Статус | Примечание |
|--------|--------|------------|
| gui/tabs/inventory_tab.py | 🚧 В разработке | Заглушка |
| libs/inventory_parser/ | 🚧 Готовится | Парсинг Excel |
| libs/scanner_input/camera_stub.py | 🚧 Заглушка | Поддержка камер |
| libs/parsers/ | 🚧 Пустой | Резерв |

---

**Следующие шаги:** см. TODO.md (план рефакторинга на 06.07.2026)