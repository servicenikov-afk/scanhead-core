"""
Модуль данных для обработчика команд сканера.

Содержит словари команд для распознавания ввода со сканера штрих-кода.
"""

from .commands import COMMANDS
from .rus_commands import RUS_COMMANDS

__all__ = ["COMMANDS", "RUS_COMMANDS"]
