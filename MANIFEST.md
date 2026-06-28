# ScanHead Core Architecture Manifest

## 📜 Введение
Этот документ описывает архитектурные принципы, стандарты кодирования и запреты проекта **ScanHead Core**. 
Нарушение принципов манифеста считается критической ошибкой и требует обязательного ревью кода.
---
## 1. 📐 Строгая Многослойность (Layered Architecture)
Проект делится на чёткие изолированные слои. Взаимодействие возможно **только сверху вниз**.
| Слой | Директория | Ответственность | Запреты |
|------|------------|-----------------|---------|
| **UI (Presentation)** | `gui/` | Отрисовка, ввод пользователя, привязка событий. Использует **гибридный стек ttk+tk**. | Никакой бизнес-логики, расчетов, прямых запросов к БД/файлам. |
| **Application Services** | `gui/services/` | Бизнес-правила, поиск, генерация штрихкодов, управление состоянием, агрегация данных из БД. | Не знают о конкретных виджетах Tkinter. Работают только через адаптеры. |
| **Adapters** | `gui/services/adapters/` | Обёртки над SQLite с потокобезопасным доступом, read-only соединения (`?mode=ro`). | Не содержат бизнес-логики. Только CRUD и поиск. |
| **Domain Models** | `libs/domain_models/` | Чистые DTO: `Product`, `Address`, `InventoryItem`. Без логики, без зависимостей. | Не содержат методов бизнес-логики, только данные и простые свойства. |
| **Infrastructure** | `libs/` (utils, scanner_input, printing, etc.) | Утилиты, нормализация артикулов, генерация этикеток, обработка сканера, DI контейнер. | Не импортируются напрямую в UI. Подключаются через сервисы. |

**Правило потока данных:**
```
UI → вызывает Service → использует Adapter → читает Database → возвращает Domain Model → обновляет UI (через root.after())
```
---
## 2. 🖥️ Гибридный стек ttk+tk (КРИТИЧЕСКИ ВАЖНО)
Проект **обязан** использовать гибридный подход: оба импорта должны присутствовать в каждом GUI-файле.
```python
# Правильно — оба импорта
import tkinter as tk
from tkinter import ttk

# Неправильно — только один из них
import tkinter as tk          # ❌ нет ttk
from tkinter import ttk       # ❌ нет tk
```
**Почему это важно:**
- `ttk` предоставляет современные виджеты с темами оформления
- `tk` нужен для низкоуровневого контроля (обработка событий, координаты, фокус)
- Попытка использовать только `ttk` приводит к поломке интерфейса (проверено на практике)

**Запрещено:**
- ❌ Удалять `tk` из любого GUI-файла
- ❌ Заменять `tk.StringVar()` на `ttk.StringVar()` (последнего не существует)
---
## 3. 🤝 Закон Деметры (Law of Demeter)
> "Разговаривай только с друзьями". Модуль знает только о тех объектах, которые получает напрямую.

**✅ Разрешено:**
- Виджет вызывает метод сервиса: `self._search_service.search_async(query)`
- Сервис возвращает список моделей: `List[Product]`
- Компоненты общаются через Callbacks или DI-контейнер

**❌ Запрещено:**
- Виджет лезет внутрь другого виджета: `details_frame._entry_widget.delete(0, END)`
- Сервис манипулирует элементами GUI напрямую
---
## 4. 🔌 Инверсия Зависимостей (DIP)
Верхние слои зависят от абстракций, а не от конкретных реализаций.
**Реализация:**
- Интерфейсы объявлены в `services/interfaces/`
- Конкретные реализации находятся в `gui/services/adapters/`
- Внедрение происходит в `main.py` через `DIContainer`
```python
# Пример правильного внедрения
class SearchAddressTab:
    def __init__(self, parent, di_container: DIContainer):
        self._search_service = di_container.get(ISearchService)
        self._product_service = di_container.get(ProductDetailsService)
```
---
## 5. 🔄 Потокобезопасность (КРИТИЧЕСКИ ВАЖНО)

Tkinter не потокобезопасен.
**✅ Разрешено:**
- Обновление GUI из фонового потока строго через `root.after(0, callback)`
- Использование `threading` для тяжёлых операций (поиск по БД)

**❌ Запрещено:**
- Прямой вызов методов виджетов (`label.config()`) из `threading.Thread`

```python
# Правильный паттерн
def _do_search(self, query):
    def worker():
        result = self._search_service.search(query)  # тяжелая операция
        self.after(0, lambda: self._update_ui(result))  # безопасное обновление
    
    threading.Thread(target=worker, daemon=True).start()
```

### Особое внимание: Адаптеры БД
- Каждое соединение создаётся в своём потоке (потокобезопасность)
---
## 6. 🗂 Актуальная структура проекта

```text
scanhead-core/
├── main.py                     # Точка входа: Bootstrap + DIContainer + MainWindow
├── config/
│   └── app_config.json         # Конфигурация приложения
├── data/
│   ├── databases/              # ТРИ SQLite БД (read-only)
│   │   ├── nomenclature/       # Внутренняя номенклатура (1,693 записи)
│   │   ├── store/              # Складские адреса (JSON-массивы)
│   │   └── css_export/         # Запчасти Franke (24,678 записей)
│   ├── icons/                  # 14 PNG-иконок для UI
│   └── images/                 # noimage.png (заглушка)
├── gui/                        # Presentation Layer (ttk+tk)
│   ├── main_window.py          # Корневое окно, управление вкладками
│   ├── search_bar.py           # Поиск с debounce + автодополнение
│   ├── product_details.py      # Карточка товара (readonly)
│   ├── print_queue.py          # Очередь печати
│   ├── sticker_preview.py      # Предпросмотр этикетки
│   ├── dialogs/                # SettingsDialog, FieldEditor, StickerEditor
│   ├── tabs/                   # SearchAddressTab, InventoryTab (заглушка)
│   ├── widgets/                # SuggestionList
│   ├── framework/              # DialogBase, ListBase
│   └── services/               # Application Layer
│       ├── product_details_service.py   # Агрегация из 3 БД
│       └── adapters/                    # NomenclatureAdapter, StoreAdapter, CssExportAdapter
├── libs/                       # Domain + Infrastructure
│   ├── domain_models/          # Product, Address, InventoryItem (чистые DTO)
│   ├── utils/                  # address_formatter.py, fuzzy_search.py
│   ├── printing/               # sticker_generator.py (этикетки с штрих-кодами)
│   ├── scanner_input/          # HID-сканер, буфер ввода
│   ├── core/                   # Bootstrap (логгер, исключения)
│   └── ... (другие утилиты)
└── services/                   # DI + интерфейсы
    ├── di_container.py         # DIContainer: регистрация зависимостей
    ├── interfaces/             # Абстракции (ISearchService, IProductRepository)
    └── stubs/                  # Заглушки для разработки
```
---
## 7. 🚫 Архитектурные Табу (Нарушение = Ревью)

| Нарушение | Описание |
|-----------|----------|
| ❌ Только `ttk` (без `tk`) | В любом GUI-файле должны быть ОБА импорта (`import tkinter as tk` И `from tkinter import ttk`) |
| ❌ Бизнес-логика в GUI | Парсинг строк, SQL-запросы, агрегация данных внутри `gui/*.py` |
| ❌ Прямые связи виджетов | Обращение к внутренностям соседнего виджета (`other_widget._private_var`) |
| ❌ Обновление GUI из потока | Прямой вызов `label.config()` из `threading.Thread` |
| ❌ Создание зависимостей в виджетах | `service = SomeService()` внутри `__init__` виджета. Только через `DIContainer` |
| ❌ Хардкод путей | `C:/...`, токены, строки подключения прямо в коде |
| ❌ Глобальные переменные | Использование `global app_state`. Состояние в сервисах или контейнере |
| ❌ Сокращение имён переменных | `self._current_preset` → `self._cp` ломает связи между модулями |
---
## 8. 🤝 Процесс Разработки
- **Стек:** Только гибридный `ttk+tk`. Любое упрощение до чистого `ttk` запрещено.
- **Ревью:** Перед мержем проверяется соответствие Манифесту.
- **Документация:** Изменения в архитектуре отражаются в этом файле.
> 💡 Помни: Хороший код — предсказуемый, читаемый и следующий правилам. Гибридный стек `ttk+tk` — это не баг, а фича.
---
## 9. ⚠️ Минификация кода (до беты)

**До релиза беты** весь код в рабочих файлах должен находиться в **минифицированном** состоянии для экономии токенов и ускорения работы LLM-ассистента.

### 9.1. Маркер файла
Каждый минифицированный файл **обязан** начинаться с заголовка-предупреждения:
```python
# --- filename.py ---
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
```
Этот маркер запрещает автоматическое форматирование, деобфускацию и "улучшение читаемости" до выхода беты.
### 9.2. Что УБИРАЕТСЯ при минификации
| Элемент | Действие | Пример |
|---------|----------|--------|
| Пустые строки между блоками | ❌ Убираются | `def foo():\n\n    x = 1` → `def foo():\n    x = 1` |
| Комментарии (`# ...`) | ❌ Убираются | `# это комментарий` → (удалено) |
| Docstring (`"""..."""`) | ❌ Убираются | `"""Описание функции"""` → (удалено) |
| Лишние переносы в выражениях | ❌ Убираются | многострочные `if/for` → в одну строку через `;` |
| Отступы внутри блоков | ⚠️ Сохраняются | Python требует отступы — их трогать нельзя |
### 9.3. Что СОХРАНЯЕТСЯ (КРИТИЧЕСКИ ВАЖНО)
| Элемент | Действие | Причина |
|---------|----------|---------|
| **Имена переменных** | ✅ **НЕ СОКРАЩАТЬ** | `self._current_preset` → нельзя в `self._cp` |
| **Имена методов** | ✅ **НЕ СОКРАЩАТЬ** | `_update_preset_value` → нельзя в `_upv` |
| **Имена атрибутов** | ✅ **НЕ СОКРАЩАТЬ** | Ломает связи между модулями |
| **Импорты** | ✅ **НЕ СОКРАЩАТЬ** | `from services.interfaces import ISettingsService` |
| **Строковые литералы** | ✅ **НЕ СОКРАЩАТЬ** | Ключи конфигов, тексты UI |
| **Логика и алгоритмы** | ✅ **НЕ МЕНЯТЬ** | Только синтаксическое уплотнение |
⚠️Отступы от левого края только tab'ами! (не по стандарту PEP 8)
### 9.4. Пример: до и после минификации
**До (читаемый, но не минифицированный):**

```python
def _load_preset(self, name: str):
    """Загрузка пресета по имени."""
    self._current_name = name
    saved = self._presets.get(name, {})
    
    # Инициализация дефолтных значений
    self._current_preset = {}
    for group in FIELDS.values():
        for item in group:
            self._current_preset[item["key"]] = item["default"]
    
    self._current_preset.update(saved)
    self._update_preview()
```

**После (минифицированный):**

```python
def _load_preset(self,name:str):
	self._current_name=name
	saved=self._presets.get(name,{})
	self._current_preset={}
	for group in FIELDS.values():
		for item in group:self._current_preset[item["key"]]=item["default"]
	self._current_preset.update(saved)
	self._update_preview()
```
### 9.5. Допустимые приёмы уплотнения
- Объединение простых присваиваний через `;`: `self._min, self._max = from_, to`
- Тернарные операторы: `x = a if cond else b`
- `if cond: do_something()` в одну строку (без `else`)
- Цепочки `elif` без лишних переносов
- Объединение импортов: `import logging, customtkinter as ctk, tkinter as tk`
### 9.6. Запрещено при минификации
- ❌ Сокращать `self._settings_service` → `self._ss`
- ❌ Сокращать `self._current_preset` → `self._cp`
- ❌ Переименовывать параметры функций
- ❌ Менять имена ключей в словарях (`"article_enabled"` и т.п.)
- ❌ Удалять маркер `# ⚠️ Minified code`
- ❌ Деобфусцировать/переформатировать код до беты
### 9.7. Исключения (НЕ минифицируются)
- `MANIFEST.md`, `README.md`, `current_structure.md` — документация
- `app_config.json` — конфигурация
- Файлы с архитектурными решениями
### 9.8. После беты
После выхода беты все файлы проходят **деминификацию**: возвращаются комментарии, docstring, нормальные отступы и форматирование по PEP 8. Имена переменных при этом **не меняются** — они уже стабильны.
---
## 10. 📚 Ссылки на документацию
- `current_structure.md` — полная детализация всех модулей
- `README.md` — обзор проекта
- `data/databases/*/README.md` — схемы и связи трёх БД