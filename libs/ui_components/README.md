# UI Components Module

Переиспользуемые UI компоненты для tkinter приложений.

## Установка

```python
from libs.ui_components import AccordionFrame
```

## Использование

### AccordionFrame - Раскладной фрейм

```python
import tkinter as tk
from tkinter import ttk
from libs.ui_components import AccordionFrame

root = tk.Tk()
accordion = AccordionFrame(root)
accordion.pack(fill=tk.X, padx=10, pady=10)

# Добавление секций
section1 = ttk.Frame(accordion)
ttk.Label(section1, text="Содержимое секции 1").pack(padx=10, pady=10)
accordion.add_section("Секция 1", section1, initially_expanded=True)

section2 = ttk.Frame(accordion)
ttk.Label(section2, text="Содержимое секции 2").pack(padx=10, pady=10)
accordion.add_section("Секция 2", section2, initially_expanded=False)

root.mainloop()
```

## Особенности

- Легковесный компонент без внешних зависимостей
- Поддержка произвольного количества секций
- Настраиваемое начальное состояние (развернуто/свернуто)
- Автоматическое обновление индикатора (стрелки)

## Зависимости

- tkinter (стандартная библиотека Python)
