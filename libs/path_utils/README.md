# Path Utils Module

Универсальный модуль для работы с путями в Python-проектах.

## Версия
0.1.0

## Назначение
Модуль предоставляет утилиты для:
- Работы с путями как в режиме разработки, так и в скомпилированном EXE (PyInstaller)
- Создания директорий с автоматическим созданием родителей
- Разрешения относительных путей в абсолютные
- Проверки режима выполнения (скрипт vs EXE)

## Установка
Скопируйте папку `path_utils` в директорию `libs/` вашего проекта.

## Использование

### Через класс PathUtils

```python
from libs.path_utils import PathUtils

# Инициализация с базовым путём (опционально)
utils = PathUtils()  # по умолчанию cwd
# или
utils = PathUtils(base_path=Path("/my/project"))

# Создание директории
data_dir = utils.ensure_dir("./data")

# Разрешение пути
config_path = utils.resolve_path("config", "settings.json")

# Создание директории для файла
utils.ensure_file_dir("./output/report.csv")

# Проверка режима выполнения
if utils.is_running_as_exe():
    print("Запущено как EXE")
```

### Через standalone-функции

```python
from libs.path_utils import get_resource_path, ensure_dir, resolve_path

# Получить путь к ресурсу (работает в EXE и dev)
icon_path = get_resource_path("icons/app.ico")

# Создать директорию
logs_dir = ensure_dir("./logs")

# Разрешить путь
db_path = resolve_path("data", "database.db")
```

## API

### Класс PathUtils

#### `__init__(base_path: Optional[Path] = None)`
Инициализирует утилиту с опциональным базовым путём.

#### `base_path: Path`
Свойство, возвращающее базовый путь.

#### `get_bundle_path() -> Path`
Статический метод. Возвращает путь к бандлу PyInstaller или cwd.

#### `resolve_path(*parts, relative_to_base=True) -> Path`
Разрешает путь из компонентов относительно base_path.

#### `ensure_dir(path, parents=True, exist_ok=True) -> Path`
Статический метод. Создаёт директорию и родителей при необходимости.

#### `ensure_file_dir(file_path) -> Path`
Создаёт родительскую директорию для файла.

#### `is_running_as_exe() -> bool`
Статический метод. Проверяет, запущено ли приложение как EXE.

### Функции модуля

#### `get_resource_path(relative_path) -> Path`
Получить абсолютный путь к ресурсу с учётом PyInstaller.

#### `ensure_dir(path, parents=True, exist_ok=True) -> Path`
Создать директорию (обёртка над PathUtils.ensure_dir).

#### `resolve_path(*parts, base=None) -> Path`
Разрешить путь относительно base (или cwd).

## Трафик данных

```
[Вызов функции] 
    ↓
[Определение режима: EXE или dev] → get_bundle_path() / _MEIPASS
    ↓
[Построение пути] → join parts / resolve
    ↓
[Опциональное создание директории] → mkdir(parents=True, exist_ok=True)
    ↓
[Возврат Path объекта]
```

## Зависимости
- Python 3.8+
- pathlib (стандартная библиотека)
- sys (стандартная библиотека)

## Примеры использования в проектах

### Замена старого resource_path
**Было:**
```python
from utils.path_utils import resource_path
icon = resource_path("icons/app.ico")
```

**Стало:**
```python
from libs.path_utils import get_resource_path
icon = get_resource_path("icons/app.ico")
```

### Замена mkdir
**Было:**
```python
Path("./data/output").mkdir(parents=True, exist_ok=True)
```

**Стало:**
```python
from libs.path_utils import ensure_dir
ensure_dir("./data/output")
```

## Тестирование

```python
from libs.path_utils import PathUtils, get_resource_path, ensure_dir

# Тест 1: Создание директории
test_dir = ensure_dir("./test_output/nested/dir")
assert test_dir.exists()

# Тест 2: Разрешение пути
utils = PathUtils(base_path=Path("/tmp"))
resolved = utils.resolve_path("data", "file.txt")
assert str(resolved) == "/tmp/data/file.txt"

# Тест 3: Проверка EXE режима
is_exe = PathUtils.is_running_as_exe()
print(f"Running as EXE: {is_exe}")

# Очистка
import shutil
shutil.rmtree("./test_output")
```

## Миграция
При миграции существующих проектов:
1. Замените импорты `utils.path_utils` на `libs.path_utils`
2. Функция `resource_path` теперь называется `get_resource_path`
3. Методы `ensure_dir` и `resolve_path` доступны и как статические, и как standalone

## Лицензия
Внутренний модуль проекта module-extractor.
