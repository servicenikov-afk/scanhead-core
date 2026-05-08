"""Command Handler Module

Модуль для обработки команд сканера штрих-кодов.
Поддерживает команды на русском и английском языках.
"""

from .core import CommandHandler, COMMANDS, RUS_COMMANDS

__all__ = ['CommandHandler', 'COMMANDS', 'RUS_COMMANDS']
