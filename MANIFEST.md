# ScanHead Core — Архитектурный Манифест

**Версия:** 0.3.0 | **Дата:** 06.07.2026

Нарушение правил = обязательное ревью кода.

---

## 1. 📐 Строгая многослойность

Проект делится на изолированные слои. Взаимодействие — только сверху вниз.

| Слой | Директория | Ответственность | Запреты |
|------|------------|-----------------|---------|
| UI (Presentation) | gui/ | Отрисовка, события, гибридный ttk+tk | Бизнес-логика, SQL, прямые запросы к БД |
| Application Services | gui/services/, services/ | Бизнес-правила, агрегация, поиск, DI | Знать о конкретных виджетах Tkinter |
| Adapters | gui/services/adapters/ | SQLite (?mode=ro) | Бизнес-логика |
| Domain Models | libs/domain_models/ | Чистые DTO (Product, Address) | Методы бизнес-логики |
| Infrastructure | libs/ | Утилиты, генераторы | Прямые импорты в UI |

**Поток данных:**
UI → Service → Adapter → DB → Domain Model → UI (через root.after())

**Исключение из read-only:**
- `store_adapter.py` — единственный адаптер с записью (CRUD для адресов)
- Остальные адаптеры — строго read-only (`?mode=ro`)

---

## 2. 🖥️ Гибридный стек ttk+tk (КРИТИЧНО)

В КАЖДОМ GUI-файле ОБА импорта:
```python
import tkinter as tk
from tkinter import ttk
```

**Запрещено:**
- ❌ Удалять tk из GUI-файла
- ❌ Заменять tk.StringVar() на ttk.StringVar()

---

## 3. 🤝 Закон Деметры

Модуль знает только о тех объектах, которые получает напрямую.

✅ **Разрешено:**
- Виджет → сервис: `self._search_service.search_async(query)`
- Сервис → список моделей: `List[Product]`
- Внедрение зависимостей через конструктор

❌ **Запрещено:**
- Виджет → внутренности другого виджета
- Сервис → прямая манипуляция GUI
- Прямые импорты диалогов в UI (нужна фабрика)
- Прямая работа с репозиторием из UI

---

## 4. 🔌 Dependency Inversion (DIP)

Верхние слои зависят от абстракций, а не от конкретных реализаций.

- Интерфейсы: `services/interfaces/`
- Реализации: `gui/services/adapters/`, `services/*.py`
- Внедрение: `main.py` через `DIContainer`

**Правильно:**
```python
class SearchAddressTab:
    def __init__(self, parent, di_container: DIContainer):
        self._search_service = di_container.get(ISearchService)
```

**❌ Запрещено:** `service = SomeService()` внутри `__init__` виджета.

---

## 5. 🔄 Потокобезопасность (КРИТИЧНО)

Tkinter не потокобезопасен.

✅ **Разрешено:**
- GUI из фона: `root.after(0, callback)`
- Тяжёлые операции: `threading.Thread`

❌ **Запрещено:**
- `label.config()` из `threading.Thread`
- Прямой вызов callback из фонового потока

**Правильно:**
```python
def search_async(self, query: str, callback: Callable):
    def worker():
        result = self.search(query)
        self._root.after(0, lambda: callback(result))
    threading.Thread(target=worker, daemon=True).start()
```

---

## 6. 🚫 Архитектурные табу

| Нарушение | Где встречается |
|-----------|------------------|
| ❌ Бизнес-логика в GUI | `search_address_tab.py`, `product_info_dialog.py` |
| ❌ GUI из потока | `search_bar.py`, `nomenclature_adapter.py` |
| ❌ Хардкод путей | `store_adapter.py` |
| ❌ Прямые импорты диалогов | `product_details.py` |
| ❌ Сырой SQL в сервисах | `product_details_service.py` |
| ❌ Подавление исключений | `store_adapter.py` |
| ❌ Только ttk (без tk) | — |
| ❌ Создание зависимостей в виджетах | — |
| ❌ Глобальные переменные | — |
| ❌ Сокращение имён | — |

---

## 7. 🛠️ Процесс разработки

- Стек: только гибридный ttk+tk
- Ревью: проверка соответствия манифесту перед мержем
- Коммиты: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`
- Документация: изменения в архитектуре → обновление этого файла

---

## 8. ⚠️ Минификация кода (до беты)

**Маркер файла** (обязателен в начале):
```python
# --- filename.py ---
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
```

**УБИРАЕТСЯ:** пустые строки, комментарии, docstring, лишние переносы
**СОХРАНЯЕТСЯ:** имена переменных/методов/атрибутов, импорты, строковые литералы, логика
**ОТСТУПЫ:** только табами (не PEP 8)

**Допустимо:**
- `self._min, self._max = from_, to`
- `x = a if cond else b`
- `if cond: do_something()` в одну строку

**Запрещено:**
- ❌ Сокращать имена: `self._settings_service → self._ss`
- ❌ Переименовывать параметры функций
- ❌ Менять ключи словарей
- ❌ Удалять маркер минификации
- ❌ Деобфусцировать до беты

**Исключения (НЕ минифицируются):**
- `MANIFEST.md`, `README.md`, `current_structure.md`, `TODO.md`
- `app_config.json`

---

## 📚 Ссылки

- `README.md` — обзор проекта
- `current_structure.md` — детальная структура модулей
- `TODO.md` — план рефакторинга (06.07.2026)
- `docs/database_schema.md` — схемы БД
- `docs/services_api.md` — API сервисов