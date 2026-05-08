# I18N Module (libs/i18n)

Модуль интернационализации и централизованного управления сообщениями.

## Состав

### messages.py
Предоставляет:
- Словари сообщений на русском и английском языках
- Класс `MessageManager` для управления локализацией
- Функции быстрого доступа `get_message()`, `set_language()`

**Пример использования:**
```python
from libs.i18n import get_message, set_language, Language

# Получить сообщение на текущем языке (по умолчанию RU)
print(get_message("success"))  # "Успешно"

# Переключить язык
set_language(Language.EN)
print(get_message("success"))  # "Success"

# Сообщение с параметрами
print(get_message("data_saved", table="Products"))
```

## Поддерживаемые языки
- Русский (ru)
- Английский (en)

## Зависимости
- Стандартная библиотека Python (typing, enum)

## Расширение
Для добавления нового языка:
1. Создайте словарь `{LANG}_MESSAGES` в `messages.py`
2. Добавьте язык в enum `Language`
3. Зарегистрируйте словарь в `MessageManager`
