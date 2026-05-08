"""Пакет интернационализации."""

from .messages import (
    Language,
    MessageManager,
    get_message,
    set_language,
    add_message,
    RU_MESSAGES,
    EN_MESSAGES,
)

__all__ = [
    "Language",
    "MessageManager",
    "get_message",
    "set_language",
    "add_message",
    "RU_MESSAGES",
    "EN_MESSAGES",
]
