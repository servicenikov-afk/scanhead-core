"""
DB Manager Module
Универсальный менеджер работы с базами данных и источниками данных.
"""

from .core import DBManager, DataSourceType
from .models import DataRecord

__version__ = "0.1.0"
__all__ = ["DBManager", "DataSourceType", "DataRecord"]
