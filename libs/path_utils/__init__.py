"""
Path Utilities Module

Универсальные утилиты для работы с путями в проектах.
Поддерживает работу как в режиме разработки, так и в скомпилированном EXE (PyInstaller).
"""

from .core import PathUtils, get_resource_path, ensure_dir, resolve_path

__version__ = "0.1.0"
__all__ = [
    "PathUtils",
    "get_resource_path",
    "ensure_dir",
    "resolve_path",
]
