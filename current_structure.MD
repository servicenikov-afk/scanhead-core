# Структура проекта ScanHead Core

Ветка: gui-framework-dev | Версия: 2.2 | Дата: 2026-07-03

⚠️ Реальные БД (.db) — только на тестовой машине. В репозитории — схемы (.sql) и README.

📜 Архитектурные правила — см. MANIFEST.md
📖 Обзор проекта — см. README.md

---

## 🔹 main.py — Точка входа

**Слой:** Application Bootstrap / Composition Root
**Назначение:** Инициализация логирования, загрузка конфига, настройка DI-контейнера, создание MainWindow, запуск mainloop.

**Ключевые зависимости:** customtkinter, libs.core.quick_bootstrap, gui.main_window.MainWindow, services.di_container.DIContainer, services.config_manager_adapter.ConfigManagerSettingsAdapter

**Особенности:**
- Использует ТОЛЬКО реальные БД (моки удалены)
- Соединения — read-only (?mode=ro), потокобезопасные
- В finally вызывает settings_service.save() для сохранения настроек
- ISettingsService зарегистрирован как ConfigManagerSettingsAdapter (реальный сервис, не заглушка)

⚠️ **Соответствие манифесту:**
- Импорты внутри main() затрудняют статический анализ
- Жёсткие пути к БД по умолчанию в коде
- Смешивание ответственностей: логирование + DI + GUI-тема

---

## 🔹 gui/main_window.py — MainWindow

**Слой:** UI (Presentation)
**Назначение:** Главный контейнер UI, навигация по вкладкам, маршрутизация событий.

**Ключевые зависимости:** customtkinter, PIL.Image, gui.tabs.*, gui.dialogs.settings_dialog, services.di_container, services.interfaces

**Методы:** _create_ui(), _on_tab_change(), _open_settings(), _on_setting_changed()

✅ Соответствует манифесту (DIP, SRP, разделение слоёв)

---

## 🔹 gui/product_details.py — ProductDetails

**Слой:** UI (Presentation)
**Назначение:** Readonly-панель деталей товара с редактированием через модалки.

**Ключевые зависимости:** customtkinter, services.interfaces.IProductRepository, libs.domain_models, gui.dialogs.*, libs.utils.AddressFormatter

**Методы:** set_product(), _render_addresses_*(), _open_editor(), _on_field_saved()

⚠️ **Соответствие манифесту:**
- ❌ Нарушение DIP: прямые импорты диалогов вместо фабрик
- ❌ Нарушение SRP: отображение + лейаут + навигация + сохранение
- ❌ Прямая работа с репозиторием в UI (_on_field_saved → update_field)

---

## 🔹 gui/search_bar.py — SearchBar

**Слой:** UI (Presentation)
**Назначение:** Поиск с debounce 300 мс, автодополнение, асинхронный поиск.

**Ключевые зависимости:** customtkinter, services.interfaces.ISearchService, libs.domain_models.Product, gui.widgets.suggestion_list, threading.Timer

**Методы:** _on_key_release, _do_search, _on_search_complete, _show_suggestions, _hide_suggestions

⚠️ **Соответствие манифесту:**
- ❌ threading.Timer для debounce — идиоматичнее widget.after()

---

## 🔹 gui/print_queue.py — PrintQueue

**Слой:** UI (Presentation)
**Назначение:** Очередь печати на базе ttk.Treeview с inline-редактированием.

**Ключевые зависимости:** customtkinter, tkinter.ttk, services.interfaces.*, libs.domain_models.Product

**Методы:** add_item(), set_products(), clear(), _print_all(), _print_one_by_one(), _start_inline_edit()

⚠️ **Соответствие манифесту:**
- ❌ Нарушение DIP/IOC: жёсткая привязка к CustomTkinter в __init__
- ❌ Нарушение SRP: отображение + состояние + inline-редактирование + печать
- ❌ Незавершённый функционал: _toggle_column_menu, _import_from_file — заглушки

---

## 🔹 gui/sticker_preview.py — StickerPreview

**Слой:** UI (Presentation)
**Назначение:** Превью макета этикетки, точка входа в редактор пресетов.

**Ключевые зависимости:** customtkinter, PIL, services.interfaces.*, libs.domain_models.Product, gui.dialogs.sticker_editor

**Методы:** set_product(), clear(), _generate_preview(), _open_editor()

✅ Соответствует манифесту

---

## 🔹 gui/dialogs/settings_dialog.py — SettingsDialog

**Слой:** UI (Presentation)
**Назначение:** Модалка настроек (тема, язык, поиск, формат адреса).

**Ключевые зависимости:** customtkinter, services.interfaces.ISettingsService

**Методы:** _create_view_tab(), _create_address_tab(), _create_data_tab(), _on_click_save(), _get_address_config_from_ui(), _load_address_settings()

**Особенности:** В _on_click_save вызывает self._settings_service.save() для немедленного сохранения.

✅ Соответствует манифесту (DIP, UI без бизнес-логики)

---

## 🔹 gui/dialogs/sticker_editor.py — StickerEditor

**Слой:** UI (Presentation)
**Назначение:** Редактор пресетов стикеров (размеры, шрифты, штрих-коды).

**Ключевые зависимости:** customtkinter, tkinter, services.interfaces.ISettingsService, libs.domain_models.Product, libs.printing.sticker_generator

**Методы:** _create_ui(), _show_group(), _update_preview(), _collect_current_preset(), _save(), _reset()

✅ Соответствует манифесту (DIP, SRP)

---

## 🔹 gui/dialogs/product_info_dialog.py — ProductInfoDialog

**Слой:** UI (Presentation)
**Назначение:** Модалка деталей товара с 3 вкладками (номенклатура, адреса, производитель).

**Ключевые зависимости:** customtkinter, gui.services.product_details_service, libs.domain_models.Product, libs.utils.AddressFormatter, адаптеры БД

**Методы:** _create_ui(), _load_details(), _add_address_row(), _save_all_locations(), _delete_address_row()

⚠️ **Соответствие манифесту:**
- ❌ Нарушение SRP: UI + парсинг адресов + работа с БД + async
- ❌ Прямая зависимость от адаптеров в UI

---

## 🔹 gui/dialogs/field_editor.py — FieldEditor

**Слой:** UI (Presentation)
**Назначение:** Модалка редактирования одного поля товара.

**Ключевые зависимости:** customtkinter, services.interfaces.IProductRepository

**Методы:** _create_content(), _on_click_save(), _get_field_label()

✅ Соответствует манифесту (DIP, инкапсуляция)

---

## 🔹 gui/dialogs/add_address_dialog.py — AddAddressDialog

**Слой:** UI (Presentation)
**Назначение:** Модалка добавления адреса (структурированный/свободный ввод).

**Ключевые зависимости:** customtkinter, libs.utils.AddressFormatter, AddressFormatConfig

**Методы:** _render_formatted_fields(), _toggle_free_entry_mode(), _get_address_value(), _show_validation_warning()

✅ Соответствует манифесту (DIP, UI отделён от доменной логики)

---

🔹 gui/dialogs/print_confirm_dialog.py — PrintConfirmDialog 🆕
Слой: UI (Presentation / Dialogs)
Назначение: Диалог подтверждения печати с прогресс-баром и статусом.
Ключевые зависимости: customtkinter, tkinter
Методы:
  - show_progress(current, total, status) — обновление прогресса
  - show_error(message) — показ ошибки
  - show_success() — показ успеха и автозакрытие
  - _safe_destroy() — безопасное закрытие
Особенности:
  - Потокобезопасный (все обновления UI через root.after())
  - Модальное окно с grab_set()
  - Кнопки "Печать" / "Отмена" с блокировкой во время работы
  - Автозакрытие через 1.2 сек после успеха
✅ Соответствует манифесту (DIP, UI без бизнес-логики)

---

## 🔹 gui/tabs/search_address_tab.py — SearchAddressTab

**Слой:** UI (Presentation)
**Назначение:** Композитная вкладка "Поиск | Адрес" (SearchBar + ProductDetails + PrintQueue + StickerPreview).

**Ключевые зависимости:** customtkinter, services.di_container.DIContainer, services.interfaces.*, gui.*, libs.utils.AddressFormatter

**Методы:** _create_search_bar(), _create_details_panel(), _create_bottom_panel(), _on_search_result(), update_products(), on_setting_changed()

⚠️ **Соответствие манифесту:**
- ❌ DEBUG_TEMP-логирование в _on_search_result
- ❌ Импорт AddressFormatter внутри метода (нарушение PEP 8)

---

## 🔹 gui/tabs/inventory_tab.py — InventoryTab

**Слой:** UI (Presentation)
**Назначение:** Заглушка вкладки "Инвентаризация".

**Ключевые зависимости:** customtkinter, services.di_container.DIContainer

**Методы:** _create_content(), обработчики-заглушки

⚠️ **Соответствие манифесту:**
- ❌ DI-контейнер внедряется, но не используется
- ❌ master: Any вместо ctk.CTkBaseClass

---

## 🔹 gui/widgets/suggestion_list.py — SuggestionList

**Слой:** UI (Presentation / Widgets)
**Назначение:** Всплывающий dropdown автодополнения.

**Ключевые зависимости:** customtkinter, typing, logging

**Методы:** show_suggestions(), hide(), _rebuild_buttons(), update_position(), select()

✅ Соответствует манифесту (изолирован, корректное управление ресурсами)

---

## 🔹 gui/services/adapters/nomenclature_adapter.py — NomenclatureAdapter

**Слой:** Adapters (Infrastructure)
**Назначение:** Адаптер к nomenclature.db, поиск товаров по артикулу/названию/штрихкоду.

**Ключевые зависимости:** sqlite3, threading, json, pathlib, libs.domain_models.Product

**Методы:** search(), search_async(), get_by_article()

⚠️ **Соответствие манифесту:**
- ❌ search_async вызывает callback напрямую в фоне (небезопасно для Tkinter)
- ❌ Фильтрация в Python вместо индексированного SQL
- ❌ Несогласованность: _get_connection хранит коннект, публичные методы создают новые

---

## 🔹 gui/services/adapters/store_adapter.py — StoreAdapter

**Слой:** Adapters (Infrastructure)
**Назначение:** CRUD адресов хранения в store.db (JSON-поле locations).

**Ключевые зависимости:** sqlite3, threading, pathlib, json

**Методы:** get_location(), get_all_locations(), update_location(), set_locations(), _get_connection()

⚠️ **Соответствие манифесту:**
- ❌ Хрупкий путь: parent.parent.parent.parent
- ❌ Подавление исключений (нарушает "Fail Fast")
- ❌ INSERT OR REPLACE удаляет старую запись

---

## 🔹 gui/services/adapters/css_export_adapter.py — CssExportAdapter

**Слой:** Adapters (Infrastructure / Legacy)
**Назначение:** Адаптер к css_export.db (запчасти Franke).

**Ключевые зависимости:** sqlite3, pathlib, threading

**Методы:** __init__(), _get_connection(), get_by_article(), search_by_name(), close()

⚠️ **Соответствие манифесту:**
- ❌ Жёсткий путь по умолчанию в сигнатуре __init__
- ❌ Фоллбэк на Path.cwd() опасен для PyInstaller
- ❌ Нет интерфейса (Protocol/ABC) для тестируемости

---

## 🔹 gui/services/adapters/json_mock_loader.py — JsonMockLoader

**Слой:** Adapters (Deprecated / Dead Code)
**Назначение:** Загрузка тестовых данных из JSON. НЕ используется в продакшене.

⚠️ **Соответствие манифесту:**
- ❌ Мёртвый код (YAGNI) — рекомендуется удаление

---

## 🔹 gui/services/product_details_service.py — ProductDetailsService

**Слой:** Application Services
**Назначение:** Агрегация данных из 3 БД в единую доменную модель Product.

**Ключевые зависимости:** libs.domain_models.Product, адаптеры БД, threading

**Методы:** get_product_details(), _fetch_all_data(), _get_nomenclature_data(), _get_storage_locations(), _get_manufacturer_info()

⚠️ **Соответствие манифесту:**
- ❌ Прямое обращение к _get_connection() + сырой SQL в _get_nomenclature_data

---

## 🔹 services/config_manager_adapter.py — ConfigManagerSettingsAdapter 🆕

**Слой:** Application Services (Адаптер)
**Назначение:** Адаптер между ISettingsService и легаси ConfigManager из libs/config. Обеспечивает сохранение настроек в config/app_config.json.

**Ключевые зависимости:** services.interfaces.ISettingsService, libs.config.config_manager.ConfigManager

**Методы:**
- __init__(config_path) — инициализация с путём к конфигу
- get_setting(key, default) — получение настройки
- set_setting(key, value) — установка настройки
- get_column_config() — конфигурация колонок
- set_column_config(config) — установка конфигурации колонок
- save() — сохранение в файл

**Особенности:**
- Заменяет StubSettingsService в main.py
- Использует точечные пути (get('sticker.width_mm'))
- Рекурсивное слияние с дефолтами
- Автосоздание директории конфига

✅ Соответствует манифесту (DIP, адаптер к легаси-коду)

---

## 🔹 services/presets_config_utils.py — PresetsConfigUtils
**Слой:** Application Services (Утилиты)
**Назначение:** Единая точка конвертации форматов пресетов стикеров (flat ↔ nested).
**Ключевые зависимости:** Только стандартная библиотека (typing)
**Функции:**
- to_nested(flat) — конвертация плоского формата (UI) в вложенный (StickerGenerator)
- to_flat(nested) — конвертация вложенного формата в плоский
- normalize_preset(preset) — нормализация пресета из любого формата в вложенный
**Особенности:**
- Устраняет дублирование логики конвертации между UI-компонентами
- Обеспечивает обратную совместимость при чтении старых конфигов
✅ Соответствует манифесту (SRP, DRY)

---

🔹 services/printer_service.py — RealPrinterService 🆕
Слой: Application Services (Печать)
Назначение: Реальный сервис печати: рендерит PDF и отправляет на принтер.
Ключевые зависимости:
  - services.interfaces.IPrinterService, ISettingsService
  - libs.printing.pdf_renderer.PdfStickerRenderer
  - gui.dialogs.print_confirm_dialog.PrintConfirmDialog
  - tkinter, threading, os, subprocess
Методы:
  - print_queue(products, one_by_one) → bool
  - generate_sticker(product, preset) → Any (заглушка)
  - print_sticker(image, copies) → bool (заглушка)
  - _start_print_worker(products, preset) — worker-поток
  - _send_to_printer(pdf_path) — отправка на печать
  - _schedule_cleanup(pdf_path, delay_seconds) — очистка временных файлов
Особенности:
  - Потокобезопасный рендер (threading.Thread)
  - Обновление UI через root.after(0, callback)
  - Поддержка SumatraPDF и Adobe Reader с флагом печати
  - Фоллбэк на os.startfile() для открытия PDF
  - Автоматическая очистка temp/print/*.pdf через 30 сек
  - Обработка ошибок с messagebox и логированием
✅ Соответствует манифесту (DIP, потокобезопасность, SRP)

---

## 🔹 libs/domain_models/product.py — Product

**Слой:** Domain Models
**Назначение:** Доменная сущность Product (артикул, штрих-коды, наименование, адреса).

**Ключевые зависимости:** Только стандартная библиотека (dataclasses, typing)

**Методы:** matches_article_or_barcode(code)

✅ Соответствует манифесту (чистая доменная модель)

---

🔹 libs/printing/pdf_renderer.py — PdfStickerRenderer 🆕
Слой: Application Services (Рендеринг)
Назначение: Рендерит многостраничный PDF из списка товаров для печати.
Ключевые зависимости: PIL.Image, libs.printing.sticker_generator.StickerGenerator, libs.domain_models.Product
Методы:
  - render(products, preset, output_path) → Path
Особенности:
  - Использует StickerGenerator для рендера каждого стикера
  - Сохраняет в PDF через PIL (один стикер = одна страница)
  - Создаёт директорию temp/print/ автоматически
  - Логгирует прогресс рендеринга
✅ Соответствует манифесту (SRP, чистые зависимости)

---

## 🔹 libs/utils/address_formatter.py — AddressFormatter

**Слой:** Application Services / Domain Logic
**Назначение:** Парсинг, форматирование, валидация складских адресов.

**Ключевые зависимости:** Только стандартная библиотека (json, dataclasses, typing)

**Классы/функции:** AddressFormatConfig (датакласс), AddressFormatter (parse, format, validate, is_compatible, format_with_labels, add_level, remove_level)

✅ Соответствует манифесту (изолирован, типизирован, SRP)

---

## 🔹 services/di_container.py — DIContainer

**Слой:** Application Services (Composition Root)
**Назначение:** Управление зависимостями, переключение между заглушками и реальными реализациями.

**Ключевые зависимости:** services.interfaces, services.stubs

**Методы:** register(interface, implementation), get(interface), register_default_services(), register_real_services(config)

✅ Соответствует манифесту (DIP, изоляция создания объектов)

---

## 🔹 services/interfaces/__init__.py — Абстрактные интерфейсы

**Слой:** Application Services (Порты)
**Назначение:** Контракты для всех бизнес-сервисов (DIP).

**Ключевые зависимости:** abc, typing, libs.domain_models

**Интерфейсы:** ISearchService, IProductRepository, IPrinterService, ISettingsService, IImageService, IInventoryService

✅ Соответствует манифесту (чистая абстракция, зависит только от доменных моделей)

---

## 🔹 services/stubs/__init__.py — Заглушки сервисов

**Слой:** Infrastructure (Заглушки для тестов)
**Назначение:** Stub-реализации для разработки GUI без реальной бизнес-логики.

**Ключевые зависимости:** libs.domain_models, services.interfaces, PIL.Image, threading

**Классы:** StubSearchService, StubSettingsService, StubPrinterService, StubImageService, StubInventoryService, StubProductRepository

✅ Соответствует манифесту (изолирован, реализует контракты)

---

## 🗄️ Базы данных (кратко, детали в README)

**Поток данных при поиске:**
1. Пользователь → SearchBar
2. SearchBar → NomenclatureAdapter.search() → список Product (без адресов)
3. ProductDetailsService.get_product_details() → обогащение:
   - store_adapter.get_all_locations() → storage_locations
   - css_adapter.get_by_article() → manufacturer_info
4. Результат → callback → обновление UI

---

# 📊 Сводка соответствия манифесту

### ✅ Полностью соответствуют
  - gui/main_window.py
  - gui/dialogs/add_address_dialog.py
  - gui/dialogs/field_editor.py
  - gui/dialogs/settings_dialog.py
  - gui/dialogs/sticker_editor.py
  - gui/dialogs/print_confirm_dialog.py 🆕
  - gui/sticker_preview.py
  - gui/widgets/suggestion_list.py
  - libs/domain_models/product.py
  - libs/utils/address_formatter.py
  - libs/printing/pdf_renderer.py 🆕
  - services/di_container.py
  - services/interfaces/__init__.py
  - services/stubs/__init__.py
  - services/config_manager_adapter.py
  - services/printer_service.py 🆕
  - services/presets_config_utils.py

### ⚠️ Требуют доработки
- main.py — смешивание ответственностей, жёсткие пути
- gui/product_details.py — нарушение DIP/SRP, прямая работа с репозиторием
- gui/search_bar.py — threading.Timer вместо widget.after()
- gui/print_queue.py — нарушение DIP/IOC/SRP, незавершённый функционал
- gui/dialogs/product_info_dialog.py — нарушение SRP, прямая зависимость от адаптеров
- gui/services/adapters/*.py — потокобезопасность, производительность, жёсткие пути
- gui/services/product_details_service.py — нарушение абстракции адаптера
- gui/tabs/search_address_tab.py — DEBUG-код, импорт внутри метода
- gui/tabs/inventory_tab.py — неиспользуемый DI-контейнер

---

 Модули-заглушки (готовятся к реализации)
| Модуль                           | Статус          | Примечание                          |
|----------------------------------|-----------------|-------------------------------------|
| gui/tabs/inventory_tab.py        | 🚧 В разработке | Заглушка с кнопками-плейсхолдерами  |
| libs/inventory_parser/           | 🚧 Готовится    | Парсинг Excel-файлов инвентаризации |
| libs/scanner_input/camera_stub.py| 🚧 Заглушка     | Будущая поддержка камер             |
| libs/parsers/                    | 🚧 Пустой       | Резерв для парсеров накладных       |
| gui/services/adapters/json_mock_loader.py | ❌ Deprecated | Рекомендуется удаление        |