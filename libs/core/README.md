# Core Module (libs/core)

Базовые компоненты инфраструктуры приложения.

## Состав

### bootstrap.py
Модуль инициализации приложения. Предоставляет единую точку входа для настройки:
- Логгера (консоль + файл)
- Обработчика глобальных исключений
- Валидации окружения

**Пример использования:**
```python
from libs.core import Bootstrap, BootstrapConfig

config = BootstrapConfig(
    app_name="MyApp",
    log_level=logging.INFO,
    log_file=Path("app.log"),
)

bootstrap = Bootstrap(config)
bootstrap.run()

logger = logging.getLogger(__name__)
logger.info("Приложение запущено")
```

### __init__.py
Экспортирует публичный API модуля.

## Зависимости
- Стандартная библиотека Python (logging, sys, traceback, pathlib)

## Примечания
- Модуль не зависит от GUI
- Подходит для CLI и GUI приложений
