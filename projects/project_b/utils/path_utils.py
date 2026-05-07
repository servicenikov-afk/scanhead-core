# utils/path_utils.py
import sys
import os

def resource_path(relative_path):
    """Получить путь к файлу, работает и в разработке и в EXE"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)