# Command Handler Module

Модуль для обработки команд сканера штрих-кодов. Поддерживает команды на русском и английском языках, включая автоматическое распознавание команд в неправильной раскладке клавиатуры.

## Установка

```python
from libs.command_handler import CommandHandler
```

## Использование

### Проверка является ли строка командой

```python
if CommandHandler.is_command("[CMD]ADD1"):
    print("Это команда")

# Распознавание русской раскладки
if CommandHandler.is_command("хСЬВъФВВ1"):  # ADD1 в русской раскладке
    print("Это команда в русской раскладке")
```

### Парсинг команды

```python
cmd = CommandHandler.parse("[CMD]ADD1")
# Возвращает: 'CMD_ADD1'

cmd = CommandHandler.parse("хСЬВъФВВ1")
# Возвращает: 'CMD_ADD1'
```

## Доступные команды

- `CMD_START_INV` - Начать инвентаризацию
- `CMD_FINISH_INV` - Завершить инвентаризацию
- `CMD_RESET_ACTUAL` - Сбросить фактические остатки
- `CMD_ADD1`, `CMD_ADD10`, `CMD_ADD100` - Добавить 1/10/100
- `CMD_SUB1`, `CMD_SUB10`, `CMD_SUB100` - Вычесть 1/10/100
- `CMD_MANUAL_NEXT` - Ручной ввод (следующая)
- `CMD_MANUAL_LAST` - Ручной ввод (последняя)
- `CMD_ZERO_LAST` - Обнулить последнюю
- `CMD_SHOW_LAST` - Показать последнюю
- `CMD_SHOW_EXPECTED` - Показать ожидаемое
- `CMD_SHOW_STATS` - Показать статистику

## Зависимости

Нет внешних зависимостей. Только стандартная библиотека Python.
