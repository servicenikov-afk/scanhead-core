"""
Data Validator Module
Централизованная валидация данных.
"""

from .core import DataValidator, ValidationRule, ValidationResult

__version__ = "0.1.0"
__all__ = ["DataValidator", "ValidationRule", "ValidationResult"]
