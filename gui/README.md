# GUI Framework (gui/)

**Статус:** 🚧 В активной разработке  
**Ветка:** `gui-framework-dev`  
**Стек:** `customtkinter` + `ttk` + `PIL`

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
│   ├── adapters/           # Адаптеры (JsonMockLoader для тестовых данных)
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
2. Через ~300мс появятся 4 товара из моков
3. Лог: `[SearchBar] Поиск завершён, найдено: 4 товаров`

---

## 🧪 Моки и тестовые данные

### Включение моков
Файл `config/app_config.json`:
```json
{
  "use_mock_data": true,
  "mock_data_path": "data/mocks"
}
```

### Моки товаров
Файл `data/mocks/products.json`:
- 4 тестовых товара с артикулами `560xxx`
- Поля: `article`, `name`, `address`, `quantity`

### Заглушки сервисов
| Сервис | Класс | Описание |
|--------|-------|----------|
| SearchService | `StubSearchService` | Возвращает моки по артикулу |
| SettingsService | `StubSettingsService` | Хранит настройки в памяти |
| PrinterService | `StubPrinterService` | Логирование вместо печати |
| ProductRepository | `JsonMockLoader` | Загрузка из JSON-файла |

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

### ❌ Не делать
- Не использовать глобальные переменные
- Не смешивать `pack()` и `grid()` в одном контейнере
- Не блокировать GUI долгими операциями
- Не пушить `.dev-tools/`, `__pycache__/`, `*.log`
- Не выдумывать выполнение команд

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

**Последнее обновление:** 17.05.2026
