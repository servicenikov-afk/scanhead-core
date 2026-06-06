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

- Каждое соединение с SQLite создаётся read-only: `sqlite3.connect(f"file:{path}?mode=ro", uri=True)`
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

---

## 8. 🤝 Процесс Разработки

- **Ветка:** Разработка в `main-gui`. Цель — влить в `main`.
- **Стек:** Только гибридный `ttk+tk`. Любое упрощение до чистого `ttk` запрещено.
- **Ревью:** Перед мержем проверяется соответствие Манифесту.
- **Базы данных:** read-only соединения (`?mode=ro`), каждое соединение в своём потоке.
- **Документация:** Изменения в архитектуре отражаются в этом файле.

> 💡 Помни: Хороший код — предсказуемый, читаемый и следующий правилам. Гибридный стек `ttk+tk` — это не баг, а фича.

---

## 9. 📚 Ссылки на документацию

- `current_structure.md` — полная детализация всех модулей
- `README.md` — обзор проекта
- `data/databases/*/README.md` — схемы и связи трёх БД