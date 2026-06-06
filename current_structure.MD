Структура проекта ScanHead Core
Ветка: gui-framework-dev
Архитектура: Строгая многослойность (Layered Architecture)
Версия: 2.2
Дата обновления: 2026-06-07
⚠️ Важно: Реальные базы данных (*.db) находятся ТОЛЬКО на тестовой машине. В репозитории присутствуют только схемы (*.sql) и описания (README.md).
🗂 Корневая структура (исключая служебные)
12345678910111213141516171819202122232425262728293031323334353637383940414243444546474849505152535455565758596061
🧱 Детальное описание модулей
🔹 main.py — Точка входа
Слой архитектуры: Application Bootstrap / Composition Root
Назначение: Точка входа приложения ScanHead Combine. Отвечает за инициализацию логирования, загрузку конфигурации, настройку DI-контейнера с реальными адаптерами БД и заглушками сервисов, создание главного окна GUI и запуск главного цикла событий.
Ключевые зависимости:
customtkinter (GUI фреймворк)
libs.core.quick_bootstrap (инициализация ядра/логирования)
gui.main_window.MainWindow (корневой виджет UI)
services.di_container.DIContainer (внедрение зависимостей)
services.interfaces (контракты сервисов)
gui.services.adapters.* (адаптеры реальных БД)
gui.services.product_details_service.ProductDetailsService (агрегация данных)
services.stubs (заглушки для Image, Settings, Printer, Inventory)
Основные функции:
load_config() — загрузка JSON-конфигурации путей к БД и настроек логирования
main() — основная функция сборки графа зависимостей и запуска UI
Особенности:
Использует ТОЛЬКО реальные БД (моки удалены)
Все соединения с БД — read-only (?mode=ro)
Потокобезопасность: каждое соединение создаётся в своём потоке
⚠️ Соответствие манифесту: Есть вопросы
Импорты внутри функции main() затрудняют статический анализ
Жестко заданные пути к БД по умолчанию в коде (а не только в конфиге)
Смешивание ответственностей: настройка логирования, создание адаптеров, сборка DI-графа, конфигурирование GUI-темы
Регистрация заглушек (Stubs) в продакшн-коде указывает на недописанные реализации
🔹 gui/main_window.py — class MainWindow(ctk.CTkFrame)
Слой архитектуры: UI (Presentation Layer)
Назначение: Главный контейнер пользовательского интерфейса, объединяющий панель навигации (кнопки справки/настроек, переключатель вкладок) и область контента, где динамически отображаются вкладки «Поиск | Адрес» и «Инвентаризация». Отвечает за маршрутизацию событий между UI и сервисами через DI-контейнер.
Ключевые зависимости:
customtkinter (UI-фреймворк), PIL.Image (работа с иконками)
gui.tabs.search_address_tab, gui.tabs.inventory_tab, gui.dialogs.settings_dialog
services.di_container.DIContainer, services.interfaces.ISearchService, services.interfaces.ISettingsService
Основные методы:
_create_ui() — построение компоновки (top-bar, notebook, content area)
_on_tab_change() — управление видимостью вкладок (show/hide через pack)
_open_settings() / _on_setting_changed() — модальный диалог настроек и проброс изменений
✅ Соответствие манифесту: Да
Dependency Inversion (зависимости через интерфейсы)
Single Responsibility (окно управляет только компоновкой и маршрутизацией)
Явное разделение слоёв (UI не содержит бизнес-логики)
🔹 gui/product_details.py — class ProductDetails(ctk.CTkFrame)
Слой архитектуры: UI (Presentation Layer)
Назначение: Виджет-панель для отображения детальной информации о товаре (артикул, наименование, адреса хранения) в режиме "только чтение" с возможностью редактирования полей через модальные диалоги и добавления товара в очередь обработки.
Ключевые зависимости:
customtkinter (UI-фреймворк)
services.interfaces.IProductRepository (абстракция доступа к данным)
libs.domain_models.Product, Address (доменные модели)
gui.dialogs.field_editor.FieldEditor (диалог редактирования поля)
gui.dialogs.product_info_dialog.ProductInfoDialog (диалог подробной информации)
libs.utils.AddressFormatter, AddressFormatConfig (форматирование адресов)
Основные методы:
set_product(product) — публичный метод для привязки товара и обновления UI
_render_addresses() / _render_addresses_with_labels() / _render_addresses_compact() — логика динамической отрисовки адресов
_open_editor(), _on_field_saved() — цепочка вызова диалога редактирования и сохранения изменений
Особенности:
Все поля ввода — state="disabled" (readonly)
Адреса рендерятся динамически с учётом AddressFormatConfig
Использует after_idle() для безопасной отрисовки после layout-событий
Проверка winfo_exists() перед обращением к виджетам
⚠️ Соответствие манифесту: Есть вопросы
Нарушение DIP: Класс напрямую импортирует и инстанцирует конкретные реализации диалогов вместо получения фабрик/интерфейсов через конструктор
Нарушение SRP: Класс несет ответственность за отображение данных, управление лейаутом адресов, навигацию и координацию сохранения данных
Прямая работа с репозиторием в UI: Метод _on_field_saved вызывает self._product_repo.update_field напрямую из виджета
Использование after_idle и ручной очистки _draw_engine — признаки фрагментарной работы с жизненным циклом виджетов
🔹 gui/search_bar.py — class SearchBar(ctk.CTkFrame)
Слой архитектуры: UI (Presentation Layer)
Назначение: Виджет поисковой строки с функцией отложенного поиска (debounce 300 мс), автодополнением в выпадающем списке и асинхронным взаимодействием с сервисом поиска.
Ключевые зависимости:
customtkinter (базовый UI-фреймворк)
services.interfaces.ISearchService (абстракция сервиса поиска)
libs.domain_models.Product (доменная модель товара)
gui.widgets.suggestion_list.SuggestionList (виджет выпадающего списка подсказок)
threading.Timer (реализация debounce-таймера)
Основные методы:
_on_key_release / _do_search / _on_search_complete — цепочка обработки ввода с дебаунсом и асинхронным колбэком
_show_suggestions / _hide_suggestions — управление жизненным циклом выпадающего окна подсказок
Особенности:
Дебаунс 300мс через threading.Timer
Регистронезависимый поиск с поддержкой кириллицы и спецсимволов
Ограничение выдачи: 50 товаров
⚠️ Соответствие манифесту: Есть вопросы
Использование threading.Timer для дебаунса в GUI-приложении создает лишние потоки при каждом нажатии клавиши. В Tkinter/CustomTkinter идиоматичнее использовать widget.after() для планирования отложенных действий в главном потоке
🔹 gui/print_queue.py — class PrintQueue(ctk.CTkFrame)
Слой архитектуры: UI (Presentation Layer)
Назначение: Виджет очереди печати на базе ttk.Treeview для отображения списка товаров с поддержкой inline-редактирования ячеек, управления видимостью колонок и запуска печати (пакетной или поштучной).
Ключевые зависимости:
customtkinter, tkinter.ttk (GUI-фреймворки)
services.interfaces.IProductRepository, IPrinterService, ISettingsService (абстракции сервисов)
libs.domain_models.Product (доменная модель)
Основные методы:
add_item(product), set_products(products), clear() — управление данными очереди
_print_all(), _print_one_by_one() — триггеры печати через IPrinterService
_start_inline_edit() — реализация редактирования ячейки "на месте"
⚠️ Соответствие манифесту: Есть вопросы
Нарушение DIP/IOC: Класс самостоятельно создает и размещает дочерние виджеты в __init__, жестко привязывая логику к конкретной реализации CustomTkinter
Нарушение SRP: Класс смешивает ответственность за отображение, управление состоянием колонок/настройками, inline-редактирование и оркестрацию печати
Незавершенная функциональность: Методы _toggle_column_menu, _import_from_file и сохранение изменений при inline-редактировании являются заглушками
Смешивание виджетов: Использование нативного ttk.Entry поверх ttk.Treeview внутри customtkinter контейнеров может вызывать артефакты рендеринга
🔹 gui/sticker_preview.py — class StickerPreview(ctk.CTkFrame)
Слой архитектуры: UI (Presentation Layer)
Назначение: Визуальный компонент (виджет) для отображения превью макета этикетки товара с заглушкой при отсутствии данных и точкой входа для открытия редактора пресетов.
Ключевые зависимости:
customtkinter (UI-фреймворк), PIL (обработка изображений)
services.interfaces (абстракции сервисов печати и настроек)
libs.domain_models.Product (доменная модель)
gui.dialogs.sticker_editor (диалог редактирования)
Основные методы:
update_product(product) / clear() — обновление данных товара
_show_placeholder() — отображение плейсхолдера
✅ Соответствие манифесту: Да
Модуль соответствует правилам: находится в слое UI, зависит от абстракций и доменных моделей, не содержит бизнес-логики генерации макета
🔹 gui/dialogs/add_address_dialog.py — class AddAddressDialog(ctk.CTkToplevel)
Слой архитектуры: UI (Presentation Layer)
Назначение: Реализует модальный диалог для добавления адреса хранения с поддержкой двух режимов ввода: структурированного (по сконфигурированным уровням) и свободного (одна текстовая строка). Инкапсулирует логику валидации адреса через AddressFormatter и передает результат через callback-функцию.
Ключевые зависимости:
customtkinter (GUI-фреймворк)
libs.utils.AddressFormatter и AddressFormatConfig (доменная логика форматирования/валидации)
logging, typing (аннотации типов)
Основные методы:
_render_formatted_fields() — динамическая генерация сетки полей ввода на основе конфигурации уровней
_toggle_free_entry_mode() / _get_address_value() — управление режимами ввода и сборка итогового адреса
_show_validation_warning() / _force_save_and_close() — обработка сценариев невалидных данных
✅ Соответствие манифесту: Да
Соответствует принципам разделения ответственности (UI отделен от доменной логики через AddressFormatter)
Использует Dependency Injection (formatter, callback)
Не содержит бизнес-логики, ограничиваясь презентацией и валидацией ввода
🔹 gui/dialogs/field_editor.py — class FieldEditor(ctk.CTkToplevel)
Слой архитектуры: UI (Presentation Layer)
Назначение: Реализует модальный диалог (Toplevel) для редактирования одного конкретного поля товара (артикул, название, адрес и т.д.), предоставляя интерфейс ввода и передачу нового значения через callback.
Ключевые зависимости:
customtkinter (UI фреймворк)
services.interfaces.IProductRepository (абстракция репозитория для типизации зависимостей)
typing (аннотации типов), logging
Основные методы:
_create_content (построение UI)
_on_click_save (обработка сохранения)
_get_field_label (локализация названий полей)
✅ Соответствие манифесту: Да
Соответствует принципам Clean Architecture: зависит от абстракции (IProductRepository)
Не содержит бизнес-логики (делегирует сохранение через callback on_save)
Инкапсулирует только логику представления
🔹 gui/dialogs/product_info_dialog.py — class ProductInfoDialog(ctk.CTkToplevel)
Слой архитектуры: UI (Presentation Layer)
Назначение: Модальное диалоговое окно для просмотра и редактирования детальной информации о товаре. Агрегирует данные из трёх источников (номенклатура, адреса хранения, данные производителя/CSV) во вкладках и предоставляет интерфейс для управления адресами хранения (CRUD с форматированием).
Ключевые зависимости:
customtkinter (UI фреймворк)
gui.services.product_details_service.ProductDetailsService (асинхронная загрузка агрегированных данных)
libs.domain_models.Product (доменная модель для типизации результата)
libs.utils.AddressFormatter (опционально, для парсинга/форматирования адресов)
Адаптеры БД (nomenclature_adapter, store_adapter, css_adapter) — для legacy-режима совместимости
Основные методы:
_create_ui() / _create_nomenclature_tab() / _create_store_tab() / _create_css_tab() — построение интерфейса
_load_details() / _update_ui_with_full_data() — оркестрация загрузки данных (async callback)
_add_address_row() / _save_all_locations() / _delete_address_row() — управление динамическим списком адресов
⚠️ Соответствие манифесту: Есть вопросы
Нарушение SRP: Класс объединяет управление жизненным циклом окна, верстку 3х сложных вкладок, логику парсинга/форматирования адресов, работу с БД, асинхронную загрузку данных, состояние "грязных" полей и динамический ресайз виджетов
Прямая зависимость от адаптеров в UI: Конструктор принимает адаптеры БД, что связывает слой представления со слоем инфраструктуры
🔹 gui/dialogs/settings_dialog.py — class SettingsDialog(ctk.CTkToplevel)
Слой архитектуры: UI (Presentation Layer)
Назначение: Реализует модальный диалог настроек приложения с вкладками для управления темой, языком, параметрами поиска (шрифт, автофокус) и конфигурацией форматирования адресов. Обеспечивает загрузку текущих значений из сервиса настроек и их персистентное сохранение с уведомлением подписчиков об изменениях.
Ключевые зависимости:
customtkinter (виджеты UI)
services.interfaces.ISettingsService (абстракция хранения настроек)
logging, typing (аннотации типов)
Основные методы:
_create_view_tab, _create_address_tab, _create_data_tab — построение вкладок UI
_on_click_save — агрегация данных из UI и сохранение через сервис
_get_address_config_from_ui / _load_address_settings — сериализация/десериализация сложной конфигурации адресов
✅ Соответствие манифесту: Да
Соблюдается Dependency Inversion (зависимость от интерфейса ISettingsService)
UI-слой не содержит бизнес-логики, а только оркестрацию виджетов и DTO-подобных словарей конфигурации
🔹 gui/dialogs/sticker_editor.py — class StickerEditor(ctk.CTkToplevel)
Слой архитектуры: UI (Presentation Layer)
Назначение: Модальный диалог для визуального редактирования параметров пресета стикера (размеры, тип штрих-кода, шрифт) с последующим сохранением конфигурации в сервисе настроек.
Ключевые зависимости:
customtkinter (UI-фреймворк)
services.interfaces.ISettingsService (абстракция хранения настроек)
logging, typing
Основные методы:
_create_setting_field / _create_combo_setting (фабричные методы для построения полей ввода)
_on_click_save / _on_click_reset (хендлеры действий пользователя)
✅ Соответствие манифесту: Да
Соблюдается Dependency Inversion (зависимость от интерфейса ISettingsService)
Single Responsibility (только UI-логика редактирования пресета)
Отсутствует бизнес-логика и прямая работа с БД/файлами
🔹 gui/services/adapters/nomenclature_adapter.py — class NomenclatureAdapter
Слой архитектуры: Adapters (Инфраструктура / Адаптеры внешних источников данных)
Назначение: Адаптер для доступа к справочнику номенклатуры (SQLite БД), предоставляющий синхронные и асинхронные методы поиска товаров по артикулу, названию или штрихкоду с маппингом на доменную модель Product.
Ключевые зависимости:
sqlite3, threading, json, pathlib
libs.domain_models.Product
Основные методы:
search(query) — синхронный поиск с фильтрацией в памяти (Python)
search_async(query, callback) — обертка в threading.Thread для неблокирующего поиска
get_by_article(article) — точное получение товара по артикулу
⚠️ Соответствие манифесту: Есть вопросы
Потокобезопасность GUI: search_async вызывает callback напрямую в фоновом потоке, что небезопасно для Tkinter/CustomTkinter (требует after или queue)
Производительность поиска: Загрузка 1000 строк и фильтрация в Python (LOWER LIKE) вместо индексированного SQL-запроса с COLLATE NOCASE не масштабируется
Управление соединениями: Несогласованность: _get_connection хранит коннект в экземпляре, а публичные методы создают новые коннекты на каждый вызов
Фатальность пути: Жестко заданный путь к БД
🔹 gui/services/adapters/store_adapter.py — class StoreAdapter
Слой архитектуры: Adapters (Инфраструктура / Адаптеры БД)
Назначение: Адаптер для доступа к данным (Data Access Object) к SQLite-базе store.db, предоставляющий CRUD-интерфейс для управления адресами хранения товаров (артикулов) с хранением списка локаций в JSON-полях.
Ключевые зависимости:
sqlite3, threading, pathlib, json, logging, typing (только стандартная библиотека Python)
Основные методы:
get_location(article) / get_all_locations(article) — чтение адресов
update_location(article, location) / set_locations(article, locations, notes) — запись/обновление адресов
_get_connection() — фабрика соединений (новое на каждый вызов/поток)
⚠️ Соответствие манифесту: Есть вопросы
Жесткая привязка к структуре путей: Вычисление project_root через parent.parent.parent.parent крайне хрупко и ломается при изменении глубины вложенности файла
Подавление исключений: Методы публичного API ловят Exception, логируют и возвращают None/False/[], скрывая реальные ошибки БД от вызывающего кода (нарушает принцип "Fail Fast")
Небезопасная схема миграции: _ensure_schema закомментирован в __init__, но использует CREATE TABLE IF NOT EXISTS без версионирования миграций
Производительность/Ресурсы: Открытие/закрытие соединения при каждом вызове метода создает накладные расходы
Потеря данных при INSERT OR REPLACE: Метод update_location использует INSERT OR REPLACE, что удаляет старую запись
🔹 gui/services/adapters/css_export_adapter.py — class CssExportAdapter
Слой архитектуры: Adapters (Инфраструктурный адаптер для внешнего источника данных / Legacy DB)
Назначение: Адаптер для доступа к данным справочника запчастей (CSS Export) из локальной SQLite-базы css_export.db. Инкапсулирует логику подключения, выполнения SQL-запросов и маппинга результатов в словари Python для использования сервисами приложения.
Ключевые зависимости:
sqlite3 (Стандартная библиотека), pathlib, threading, logging, typing
Внутренних зависимостей проекта нет (чистый адаптер)
Основные методы:
__init__ — инициализация с автопоиском пути к БД относительно корня проекта или CWD
_get_connection — создание потокобезопасного read-only соединения на лету
get_by_article(article) — точный поиск деталей по артикулу (возвращает список моделей/позиций)
search_by_name(query) — нечеткий поиск по названию (LIMIT 50)
close — заглушка для совместимости интерфейса (соединения короткоживущие)
⚠️ Соответствие манифесту: Есть вопросы
Жестко заданный путь по умолчанию (data/databases/css_export/...) в сигнатуре __init__ нарушает принцип конфигурируемости через DI/Config
Фоллбэк на Path.cwd() в конструкторе создает неявное поведение, зависящее от точки входа (рабочей директории), что опасно для упаковки (PyInstaller) и тестов
Прямые SQL-запросы в коде — допустимо для адаптера, но требует интеграционных тестов на реальной схеме БД
Отсутствие интерфейса (Protocol/ABC) — сложно подменить реализацию для тестов (моки) или смены источника без изменения потребителей
🔹 gui/services/adapters/json_mock_loader.py — class JsonMockLoader
Слой архитектуры: Adapters (технически — Infrastructure/Adapters, но функционально — Dead Code / Legacy)
Назначение: Модуль-историк (deprecated), реализующий загрузку тестовых данных (товаров и адресов) из локальных JSON-файлов в доменные модели. Явно помечен как неиспользуемый в продакшене, сохранён исключительно для истории; приложение работает только с реальными базами данных.
Ключевые зависимости:
json, pathlib.Path, typing (List, Optional)
libs.domain_models (Product, Address)
Основные методы:
_parse_products / _parse_addresses — методы маппинга JSON на доменные сущности
load_products / load_addresses / get_product_by_article — публичный API для доступа к мок-данным
⚠️ Соответствие манифесту: Есть вопросы
Модуль нарушает принцип чистоты кодовой базы (YAGNI / Dead Code): мёртвый код должен удаляться, а не комментироваться как "история"
Наличие адаптера для моков в слое adapters создаёт путаницу относительно текущей стратегии работы с данными (реальные БД vs моки)
Рекомендуется полное удаление файла
🔹 gui/services/product_details_service.py — class ProductDetailsService
Слой архитектуры: Application Services (Сервис приложения / Use Case)
Назначение: Агрегация детальной информации о товаре из трёх независимых источников данных (номенклатура, адреса хранения, данные производителя) в единую доменную модель Product с поддержкой синхронного и асинхронного (callback-based) режимов работы.
Ключевые зависимости:
libs.domain_models.Product (Domain Model)
gui.services.adapters.nomenclature_adapter.NomenclatureAdapter (Adapter)
gui.services.adapters.store_adapter.StoreAdapter (Adapter)
gui.services.adapters.css_export_adapter.CssExportAdapter (Adapter)
threading, logging (Standard Library)
Основные методы:
get_product_details(article, callback) — публичный метод входа (поддерживает sync/async)
_fetch_all_data(article) — внутренний метод сборки агрегированного объекта Product
_get_nomenclature_data, _get_storage_locations, _get_manufacturer_info — методы-запросы к конкретным адаптерам/источникам
⚠️ Соответствие манифесту: Есть вопросы
Нарушение абстракции адаптера: В методе _get_nomenclature_data происходит прямое обращение к self._nomenclature._get_connection() и выполнение сырых SQL-запросов с динамическим определением имени таблицы. Логика запроса должна инкапсулироваться внутри адаптера
🔹 gui/tabs/search_address_tab.py — class SearchAddressTab(ctk.CTkFrame)
Слой архитектуры: UI (Presentation Layer)
Назначение: Композитный виджет вкладки «Поиск | Адрес», объединяющий поисковую строку, панель деталей товара, очередь печати и превью стикера в единый интерфейс пользователя.
Ключевые зависимости:
customtkinter (базовый UI-фреймворк)
services.di_container.DIContainer (внедрение зависимостей)
Интерфейсы сервисов: ISearchService, IProductRepository, IPrinterService, ISettingsService
Локальные UI-компоненты: SearchBar, ProductDetails, PrintQueue, StickerPreview
Доменная модель: libs.domain_models.Product
Утилиты форматирования: libs.utils.AddressFormatter, AddressFormatConfig
Основные методы:
_on_search_result — коллбэк-обработчик результатов поиска с асинхронным обогащением товаров адресами хранения через product_details_service
update_products — точка входа для обновления состояния всех дочерних панелей после завершения загрузки данных
⚠️ Соответствие манифесту: Есть вопросы
Нарушение чистоты слоев / Временный код: В методе _on_search_result присутствует блок логирования с префиксом DEBUG_TEMP, который должен быть удален перед релизом
Импорт внутри метода: Импорт AddressFormatter и AddressFormatConfig внутри _create_details_panel нарушает конвенцию PEP 8 (импорты вверху файла) и может скрывать циклические зависимости
Сложность коллбэков: Исп
🔹 gui/tabs/inventory_tab.py — class InventoryTab(ctk.CTkFrame)
Слой архитектуры: UI (Presentation Layer)
Назначение: Реализует вкладку "Инвентаризация" интерфейса пользователя в виде заглушки (MVP/Placeholder), отображающую информацию о планируемом функционале и эмулирующую взаимодействие через неактивные кнопки.
Ключевые зависимости:
customtkinter (UI-фреймворк)
services.di_container.DIContainer (внедрение зависимостей, пока не используется напрямую в логике)
logging (логирование событий UI)
Основные методы:
_create_content() — построение декларативного UI (заголовок, описание, панель кнопок)
Обработчики событий-заглушки: _on_import_click, _on_scanner_click, _on_export_click
⚠️ Соответствие манифесту: Есть вопросы
DI Container: Контейнер внедряется в __init__, но не используется для получения сервисов (например, IInventoryService), что нарушает принцип Dependency Inversion и делает зависимость мертвым кодом
Типизация: Аргумент master: Any должен быть типизирован как ctk.CTkBaseClass или ctk.CTk для строгой типизации
Архитектура UI: Логика создания виджетов смешана с данными (тексты планируемого функционала хардкодятся в методе _create_content)
🔹 gui/widgets/suggestion_list.py — class SuggestionList(ctk.CTkToplevel)
Слой архитектуры: UI (Presentation Layer / Widgets)
Назначение: Реализует всплывающий выпадающий виджет (dropdown) для отображения списка текстовых подсказок (автодополнение) с поддержкой навигации, выбора элемента и динамического позиционирования относительно курсора/поля ввода.
Ключевые зависимости:
customtkinter (базовый UI-фреймворк)
typing (аннотации типов)
logging (диагностика выбора)
Основные методы:
show_suggestions — отображение списка подсказок
hide — скрытие виджета
_rebuild_buttons — перестроение списка
_update_position — позиционирование
_select — обработка выбора
✅ Соответствие манифесту: Да
Виджет изолирован, не содержит бизнес-логики
Корректно управляет ресурсами (отмена after-колбэков, очистка дочерних виджетов в destroy/hide)
Использует типизацию и логирование
🔹 libs/domain_models/product.py — class Product (dataclass)
Слой архитектуры: Domain Models
Назначение: Определяет доменную сущность Product (Товар), инкапсулирующую идентифицирующие атрибуты (артикул, штрих-коды), наименование, логистические данные (адреса хранения) и справочную информацию (категория, производитель, единицы измерения). Предоставляет логику проверки принадлежности кода товару.
Ключевые зависимости: Только стандартная библиотека Python (dataclasses, typing). Внешних зависимостей нет.
Основные методы:
matches_article_or_barcode(code: str) -> bool — метод бизнес-логики для идентификации товара по входящему коду
Поля:
python
12345678910
✅ Соответствие манифесту: Да
Модуль представляет собой чистую доменную модель без зависимостей от инфраструктуры, UI или фреймворков
Соответствует правилам Clean Architecture и изоляции слоя Domain
🔹 libs/utils/address_formatter.py — class AddressFormatter
Слой архитектуры: Application Services / Domain Logic (чистый доменный сервис без зависимостей от инфраструктуры и UI)
Назначение: Модуль инкапсулирует бизнес-логику работы со складскими адресами: парсинг, форматирование, валидацию и управление конфигурацией структуры адреса (уровни, разделители, режимы отображения).
Ключевые зависимости: Только стандартная библиотека Python (json, dataclasses, typing). Внешних пакетов не использует.
Основные классы/функции:
AddressFormatConfig — датакласс конфигурации (уровни, разделители, режимы, сериализация)
AddressFormatter — основной сервис:
parse / format — парсинг и форматирование адресов
validate — валидация
is_compatible — проверка совместимости
format_with_labels — форматирование с подписями
add_level, remove_level — управление уровнями
Работа с JSON для БД
✅ Соответствие манифесту: Да
Код следует принципам Clean Architecture: изолирован, типизирован, не имеет побочных эффектов
Использует стандартные типы и датаклассы
Соответствует SRP
🔹 services/di_container.py — class DIContainer
Слой архитектуры: Application Services (Инфраструктура приложения / Composition Root)
Назначение: Реализует паттерн Dependency Injection (DI) для централизованного управления жизненным циклом и зависимостями сервисов приложения. Обеспечивает переключение между заглушками (stubs) для разработки UI и реальными реализациями бизнес-логики.
Ключевые зависимости:
services.interfaces (контракты: ISearchService, IProductRepository и др.)
services.stubs (заглушки для разработки)
logging (системное логирование)
Основные методы:
register(interface, implementation) — ручная регистрация зависимости
get(interface) — разрешение зависимости (resolve)
register_default_services() — массовая регистрация заглушек
register_real_services(config) — точка расширения для продакшн-реализаций (заглушка)
✅ Соответствие манифесту: Да
Модуль следует принципам DIP (Dependency Inversion Principle): зависит от абстракций (interfaces), а не конкретных реализаций
Изолирует детали создания объектов от бизнес-логики и UI
Поддерживает тестируемость и заменяемость компонентов
🔹 services/interfaces/__init__.py — Абстрактные интерфейсы сервисов
Слой архитектуры: Application Services (слой абстракций/порт в терминах Clean Architecture / Hexagonal Architecture)
Назначение: Модуль определяет контракты (абстрактные базовые классы) для всех бизнес-сервисов приложения, обеспечивая слабую связанность через принцип инверсии зависимостей (DIP) и позволяя подменять реализации (моки, тестовые заглушки, продакшн-бэкенды) без изменения кода потребителей.
Ключевые зависимости:
abc (стандартная библиотека)
typing (стандартная библиотека)
libs.domain_models (внутренний доменный слой: Product, Address)
Основные интерфейсы:
ISearchService (поиск и получение товаров)
IProductRepository (CRUD-операции и адресация)
IPrinterService (генерация и печать этикеток)
ISettingsService (управление конфигурацией)
IImageService / IInventoryService (заглушки для расширения)
✅ Соответствие манифесту: Да
Модуль идеально соответствует правилам: чистая абстракция без реализации
Зависит только от доменных моделей (libs.domain_models) и стандартной библиотеки
Не тянет за собой фреймворки (PySide, requests и т.д.)
Позволяет использовать его в любом слое приложения
🔹 services/stubs/__init__.py — Заглушки сервисов
Слой архитектуры: Infrastructure (Адаптеры / Заглушки)
Назначение: Модуль предоставляет заглушки (stub-реализации) для всех сервисных интерфейсов приложения, позволяя разрабатывать и тестировать GUI-слой без зависимости от реальной бизнес-логики, баз данных или оборудования.
Ключевые зависимости:
libs.domain_models (Product, Address, InventoryItem)
services.interfaces (ISearchService, IProductRepository, IImageService, IPrinterService, ISettingsService, IInventoryService)
PIL.Image, threading, logging
Основные классы:
StubSearchService (асинхронный поиск с эмуляцией задержки)
StubSettingsService (in-memory хранилище настроек UI)
StubPrinterService / StubImageService (генерация пустых изображений PIL)
StubInventoryService / StubProductRepository (логгирующие заглушки CRUD-операций)
✅ Соответствие манифесту: Да
Модуль изолирован в services/stubs
Реализует контракты из services.interfaces
Не содержит бизнес-логики
Соответствует принципам Clean Architecture и Dependency Inversion
🗄️ Базы данных: схемы и связи
nomenclature.db (внутренняя номенклатура)
Таблица
Поля
Записей
nomenclature
canonical_article, name_ru, alternative_articles (JSON), unit
~1 693
Роль: Основной справочник с русскими наименованиями и альтернативными артикулами.
store.db (складские адреса)
Таблица
Поля
Особенность
storage_locations
article, locations (JSON-массив), alternative_names (JSON)
Один артикул → несколько адресов
css_export.db (запчасти Franke)
Таблица
Поля
Записей
spare_parts
art_no, product_model, name, usage_path, category1-3, production_date_*, serial_*
~24 678 записей, 20 моделей
Схема связей
123
Поток данных при поиске:
Пользователь вводит запрос → SearchBar
SearchBar → NomenclatureAdapter.search() (через ISearchService)
NomenclatureAdapter → SQL-запрос → список Product (без адресов)
ProductDetailsService.get_product_details() → обогащение:
store_adapter.get_all_locations() → storage_locations
css_adapter.get_by_article() → manufacturer_info, models
Результат → callback в SearchAddressTab → обновление UI
Выбор товара → ProductDetails.set_product() → отрисовка полей + адресов
⚠️ Критические правила (из MANIFEST.md)
Слои: gui/ → services/ → interfaces → libs/ (строго сверху вниз)
Запрещено в gui/: бизнес-логика, прямые запросы к БД, хардкод путей
DI: все зависимости внедряются через DIContainer, не создаются в __init__ виджетов
Потоки: обновление GUI из background-threads только через root.after(0, ...)
Тестируемость: бизнес-логика должна работать без GUI (headless)
Коммиты: префиксы feat:, fix:, refactor:, docs:, chore:
Закон Деметры: виджеты не лезут во внутренности друг друга, только через интерфейсы
Fail Fast: проверки winfo_exists(), валидация входных данных, логирование ошибок
📦 Модули-заглушки (готовятся к реализации)
Модуль
Статус
Примечание
gui/tabs/inventory_tab.py
🚧 В разработке
Заглушка с кнопками-плейсхолдерами
libs/inventory_parser/
🚧 Готовится
Парсинг Excel-файлов инвентаризации
libs/scanner_input/camera_stub.py
🚧 Заглушка
Будущая поддержка камер
libs/parsers/
🚧 Пустой
Резерв для будущих парсеров накладных
gui/services/adapters/json_mock_loader.py
❌ Deprecated
Мок-данные удалены из продакшена, рекомендуется удалить файл
📊 Сводка соответствия манифесту
✅ Полностью соответствуют:
gui/main_window.py
gui/dialogs/add_address_dialog.py
gui/dialogs/field_editor.py
gui/dialogs/settings_dialog.py
gui/dialogs/sticker_editor.py
gui/sticker_preview.py
gui/widgets/suggestion_list.py
libs/domain_models/product.py
libs/utils/address_formatter.py
services/di_container.py
services/interfaces/__init__.py
services/stubs/__init__.py
⚠️ Требуют доработки:
main.py — смешивание ответственностей, жестко заданные пути
gui/product_details.py — нарушение DIP и SRP, прямая работа с репозиторием
gui/search_bar.py — использование threading.Timer вместо widget.after()
gui/print_queue.py — нарушение DIP/IOC и SRP, незавершенная функциональность
gui/dialogs/product_info_dialog.py — нарушение SRP, прямая зависимость от адаптеров
gui/services/adapters/*.py — проблемы с потокобезопасностью, производительностью, жесткой привязкой к путям
gui/services/product_details_service.py — нарушение абстракции адаптера
gui/tabs/search_address_tab.py — отладочный код, импорт внутри метода
gui/tabs/inventory_tab.py — неиспользуемый DI Container
Документ обновлен на основе AI-анализа кода. Актуальность: 2026-06-06 16:45 UTC±0