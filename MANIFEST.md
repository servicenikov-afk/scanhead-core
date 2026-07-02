# ScanHead Core — Архитектурный Манифест

Нарушение правил = обязательное ревью кода.
📜 Архитектурные принципы, стандарты и запреты проекта.
📖 Обзор проекта — см. README.md
🗺️ Карта модулей — см. current_structure.MD

---

## 1. 📐 Строгая многослойность

Проект делится на изолированные слои. Взаимодействие — только сверху вниз.

| Слой | Директория | Ответственность | Запреты |
|------|------------|-----------------|---------|
| UI (Presentation) | gui/ | Отрисовка, события, гибридный ttk+tk | Бизнес-логика, SQL, прямые запросы к БД |
| Application Services | gui/services/ | Бизнес-правила, агрегация, поиск | Знать о конкретных виджетах Tkinter |
| Adapters | gui/services/adapters/ | Read-only SQLite (?mode=ro) | Бизнес-логика |
| Domain Models | libs/domain_models/ | Чистые DTO (Product, Address) | Методы бизнес-логики |
| Infrastructure | libs/ | Утилиты, генераторы, DI | Прямые импорты в UI |

**Поток данных:**
UI → Service → Adapter → DB → Domain Model → UI (через root.after())

---

## 2. 🖥️ Гибридный стек ttk+tk (КРИТИЧНО)

В КАЖДОМ GUI-файле ОБА импорта:
- import tkinter as tk
- from tkinter import ttk

Почему:
- ttk — современные виджеты с темами
- tk — низкоуровневый контроль (события, координаты, фокус)
- Попытка использовать только ttk ломает интерфейс (проверено)

Запрещено:
- ❌ Удалять tk из GUI-файла
- ❌ Заменять tk.StringVar() на ttk.StringVar() (не существует)

---

## 3. 🤝 Закон Деметры

"Разговаривай только с друзьями". Модуль знает только о тех объектах, которые получает напрямую.

✅ Разрешено:
- Виджет → сервис: self._search_service.search_async(query)
- Сервис → список моделей: List[Product]
- Общение через callbacks или DI-контейнер

❌ Запрещено:
- Виджет → внутренности другого виджета: details_frame._entry_widget.delete(0, END)
- Сервис → прямая манипуляция GUI

---

## 4. 🔌 Dependency Inversion (DIP)

Верхние слои зависят от абстракций, а не от конкретных реализаций.

- Интерфейсы: services/interfaces/
- Реализации: gui/services/adapters/
- Внедрение: main.py через DIContainer

Пример правильного внедрения:

class SearchAddressTab:
    def __init__(self, parent, di_container: DIContainer):
        self._search_service = di_container.get(ISearchService)

❌ Запрещено: service = SomeService() внутри __init__ виджета.

---

## 5. 🔄 Потокобезопасность (КРИТИЧНО)

Tkinter не потокобезопасен.

✅ Разрешено:
- GUI из фона: root.after(0, callback)
- Тяжёлые операции: threading.Thread

❌ Запрещено:
- label.config() из threading.Thread

Правильный паттерн:

def _do_search(self, query):
    def worker():
        result = self._search_service.search(query)
        self.after(0, lambda: self._update_ui(result))
    threading.Thread(target=worker, daemon=True).start()

Особое внимание: адаптеры БД — каждое соединение в своём потоке.

---

## 6. 🚫 Архитектурные табу

| Нарушение | Описание |
|-----------|----------|
| ❌ Только ttk (без tk) | В GUI-файле ОБА импорта |
| ❌ Бизнес-логика в GUI | Парсинг, SQL, агрегация внутри gui/*.py |
| ❌ Прямые связи виджетов | other_widget._private_var |
| ❌ GUI из потока | label.config() из threading.Thread |
| ❌ Создание зависимостей в виджетах | service = SomeService() в __init__ |
| ❌ Хардкод путей | C:/..., токены, строки подключения |
| ❌ Глобальные переменные | global app_state |
| ❌ Сокращение имён | self._current_preset → self._cp |

---

## 7. 🤝 Процесс разработки

- Стек: только гибридный ttk+tk
- Ревью: проверка соответствия манифесту перед мержем
- Коммиты: feat:, fix:, refactor:, docs:, chore:
- Документация: изменения в архитектуре → обновление этого файла

💡 Хороший код — предсказуемый, читаемый, следующий правилам.

---

## 8. ⚠️ Минификация кода (до беты)

До релиза беты код минифицирован для экономии токенов.

**Маркер файла** (обязателен в начале):
# --- filename.py ---
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.

**УБИРАЕТСЯ:** пустые строки, комментарии, docstring, лишние переносы
**СОХРАНЯЕТСЯ:** имена переменных/методов/атрибутов, импорты, строковые литералы, логика
**ОТСТУПЫ:** только табами (не PEP 8)

**Допустимо:**
- self._min, self._max = from_, to
- x = a if cond else b
- if cond: do_something() в одну строку
- import logging, customtkinter as ctk, tkinter as tk

**Запрещено:**
- ❌ self._settings_service → self._ss
- ❌ Переименовывать параметры функций
- ❌ Менять ключи словарей ("article_enabled")
- ❌ Удалять маркер минификации
- ❌ Деобфусцировать до беты

**Исключения (НЕ минифицируются):**
- MANIFEST.md, README.md, current_structure.md — документация
- app_config.json — конфигурация
- Файлы с архитектурными решениями

**После беты:** деминификация + PEP 8 (имена не меняются).

---

## 📚 Ссылки

- README.md — обзор проекта
- current_structure.MD — детальная структура модулей
- docs/database_schema.md — схемы БД
- docs/services_api.md — API сервисов