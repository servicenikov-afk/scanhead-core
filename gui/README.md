# GUI Framework (gui/)

**Статус:** ✅ Базовая версия завершена  
**Ветка:** `gui-framework-dev`  
**Стек:** `customtkinter` + `ttk` + `PIL`  
**Версия:** 2.1.0

---

## 🎯 Назначение

Модульный GUI-каркас для приложения ScanHead Combine. Слой представления, отделённый от бизнес-логики через DI (Dependency Injection).

---

## 📦 Структура

```text
gui/
├── main_window.py          # Корневое окно (CTk), инициализация, DI-контейнер
├── search_bar.py           # Поиск с debounce 300мс + автодополнение
├── product_details.py      # Панель деталей товара + кнопки действий
├── print_queue.py          # Treeview очереди печати + toolbar + меню колонок
├── sticker_preview.py      # Превью стикера + кнопка редактора пресетов
├── tabs/
│   ├── search_address_tab.py  # Вкладка "Поиск | Адрес" (основная)
│   └── inventory_tab.py       # Вкладка "Инвентаризация" (заглушка)
├── dialogs/              # Toplevel-диалоги
│   ├── settings_dialog.py   # Диалог настроек приложения
│   └── sticker_editor.py    # Редактор пресетов этикеток
├── services/             # Сервисный слой для GUI
│   ├── interfaces/         # Интерфейсы (ISearchService, IProductRepository...)
│   ├── adapters/           # Адаптеры к реальным БД (NomenclatureAdapter, StoreAdapter...)
│   └── stubs/              # Заглушки сервисов для разработки
├── widgets/              # Кастомные виджеты (переиспользуемые компоненты)
└── windows/              # Дочерние окна (Toplevel)
```

---

## 🏗️ Архитектурные принципы

### 1. Dependency Injection (DI)
Все зависимости передаются явно через конструкторы:
```python
self._search_bar = SearchBar(
    master,
    search_service=self._services.get("search_service"),
    on_search_result=self._on_search_result
)
```

### 2. Слабая связность
- Интерфейсы в `services/interfaces/`
- Заглушки в `services/stubs/`
- Бизнес-логика не импортируется напрямую

### 3. Модульность
- Один класс = один файл
- Четкое разделение ответственности
- Переиспользуемые виджеты в `widgets/`

### 4. Неблокирующий GUI
- Тяжёлые операции в `threading.Thread`
- Результаты через `queue.Queue` + `after()`
- Debounce для поиска (300мс)
- **Регистронезависимый поиск** с фильтрацией на уровне Python (корректная работа с кириллицей и спецсимволами)

### 5. Чистая геометрия
- `CTkFrame` как контейнер
- `ttk`-виджеты внутри для таблиц
- Единый менеджер геометрии на контейнер (`grid()` или `pack()`)

---

## 🚀 Быстрый старт

### Требования
```bash
pip install customtkinter pillow
```

### Запуск
```bash
cd /workspace
python main.py
```

### Тестирование поиска
1. Введите `560` в поле поиска
2. Через ~300мс появятся товары из реальных баз данных
3. Лог: `[SearchBar] Поиск завершён, найдено: X товаров`
4. **Проверка регистронезависимости:** запрос `аб-001` находит товар `АБ-001`

---

## 🗄️ Базы данных

Приложение работает ТОЛЬКО с реальными базами данных SQLite.

### Расположение БД

Реальные базы данных находятся **ТОЛЬКО на тестовой машине** в директории `data/databases/`.
В репозиторий они **НЕ загружаются** ввиду конфиденциальности данных, но полностью соответствуют
описанию в соответствующих README.md файлах:

- `data/databases/nomenclature/README.md` — внутренний справочник номенклатуры (1693 записи)
- `data/databases/store/README.md` — складской учёт местоположения
- `data/databases/css_export/README.md` — база запчастей Franke (24678 записей)

### Конфигурация

Файл `config/app_config.json`:
```json
{
  "db_paths": {
    "nomenclature": "data/databases/nomenclature/nomenclature.db",
    "store": "data/databases/store/store.db",
    "css_export": "data/databases/css_export/css_export.db"
  }
}
```

### Адаптеры

| Сервис | Класс | Описание |
|--------|-------|----------|
| SearchService | `NomenclatureAdapter` | Поиск по основной БД номенклатуры |
| ProductRepository | `StoreAdapter` | Получение адресов хранения из БД склада |
| CssExportAdapter | `CssExportAdapter` | Данные о совместимости из CSS Export |

**Примечание:** Моки удалены как неактуальные. Приложение работает только с реальными БД.

---

## 📐 Геометрия основной вкладки

**Вкладка "Поиск | Адрес"** (`tabs/search_address_tab.py`):

```
┌─────────────────────────────────────────────┐
│  🔍 [Поиск: введите артикул...]             │  ← Row 0
├─────────────────────────────────────────────┤
│                                             │
│  Детали товара (артикул, название, адрес)   │  ← Row 1 (75% высоты)
│  [➕ В очередь]                             │
│                                             │
├──────────────────────────┬──────────────────┤
│                          │                  │
│  Очередь печати          │  Превью стикера  │  ← Row 2 (25% высоты)
│  (Treeview + toolbar)    │  (макет + кнопка)│
│  75% ширины              │  25% ширины      │
│                          │                  │
└──────────────────────────┴──────────────────┘
```

**Отступы:** `padx=3, pady=3` (минимальные)

---

## 🎨 Стиль и темы

### CustomTkinter
- Базовый класс: `ctk.CTkFrame`
- Кнопки: `ctk.CTkButton` с иконками `ctk.CTkImage`
- Табы: `ctk.CTkTabview` (высота 50px, скругление 10px)

### Иконки
Расположение: `data/icons/`
- `find32.png` — поиск
- `invent32.png` — инвентаризация
- `settings32.png` — настройки
- `help32.png` — справка

### Изображения
Расположение: `data/images/`
- `noimage.png` — заглушка превью стикера

---

## 🔧 Расширение функциональности

### Добавление новой вкладки
1. Создать файл в `tabs/`:
   ```python
   # gui/tabs/new_tab.py
   class NewTab(ctk.CTkFrame):
       def __init__(self, master, services):
           super().__init__(master)
           self._services = services
           self._create_ui()
       
       def _create_ui(self):
           # Создание интерфейса
           pass
   ```

2. Добавить в `main_window.py`:
   ```python
   new_frame = self._notebook.add("  🆕  Новая вкладка  ")
   self._new_tab = NewTab(new_frame, services=self._services)
   self._new_tab.pack(fill="both", expand=True)
   ```

### Добавление диалога
1. Создать файл в `dialogs/`:
   ```python
   # gui/dialogs/my_dialog.py
   class MyDialog(ctk.CTkToplevel):
       def __init__(self, master, service):
           super().__init__(master)
           self._service = service
           self._create_ui()
           self.grab_set()  # Модальность
   ```

2. Вызов из главного окна:
   ```python
   def _open_my_dialog(self):
       dialog = MyDialog(self, self._some_service)
       dialog.grab_set()
   ```

---

## 📝 Правила разработки

### ✅ Делать
- Передавать зависимости через конструктор
- Использовать интерфейсы из `services/interfaces/`
- Писать логирование через `logging.getLogger(__name__)`
- Проверять `git status` перед коммитом
- Писать подробные сообщения коммитов
- **Реализовывать регистронезависимый поиск через фильтрацию в Python** (не через SQL `LOWER()` для кириллицы)
- **Скрывать дубликаты артикулов** при отображении поля "Артикул 2"

### ❌ Не делать
- Не использовать глобальные переменные
- Не смешивать `pack()` и `grid()` в одном контейнере
- Не блокировать GUI долгими операциями
- Не пушить `.dev-tools/`, `__pycache__/`, `*.log`
- Не выдумывать выполнение команд
- Не использовать SQL `LOWER()` для регистронезависимого поиска кириллицы (некорректно работает в SQLite)

---

## 🐛 Отладка геометрии

Временные цветные рамки для визуализации:
```python
ctk.CTkFrame(self, fg_color="red").grid(...)  # Красная = видна граница
```

Логирование событий:
```python
logger.debug("[WidgetName] Событие: описание")
```

---

## 📞 Контакты

- Репозиторий: https://github.com/servicenikov-afk/scanhead-core
- Ветка: `gui-framework-dev`
- Ответственный: GUIllermo ( Ги )

---

**Последнее обновление:** 19.05.2026  
**Изменения в v2.1:**
- ✅ Регистронезависимый поиск (кириллица + спецсимволы)
- ✅ Умное отображение "Артикул 2" (без дубликатов основного артикула)
- ✅ Корректный парсинг JSON со штрихкодами
- ✅ Пустые поля вместо текстовых заглушек
