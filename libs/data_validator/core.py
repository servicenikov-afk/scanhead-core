"""
Data Validator Core
Централизованная валидация данных с поддержкой кастомных правил.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Any
from enum import Enum


class ValidationSeverity(Enum):
    """Уровень серьезности ошибки валидации."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Результат проверки одного правила."""
    
    field: str
    is_valid: bool
    message: str = ""
    severity: ValidationSeverity = ValidationSeverity.ERROR
    value: Any = None

    @classmethod
    def ok(cls, field: str, value: Any = None, message: str = "OK") -> 'ValidationResult':
        """Создать успешный результат."""
        return cls(field=field, is_valid=True, message=message, value=value)

    @classmethod
    def fail(cls, field: str, message: str, value: Any = None, 
             severity: ValidationSeverity = ValidationSeverity.ERROR) -> 'ValidationResult':
        """Создать результат с ошибкой."""
        return cls(field=field, is_valid=False, message=message, value=value, severity=severity)


@dataclass
class ValidationRule:
    """Правило валидации."""
    
    name: str
    field: str
    validator: Callable[[Any], bool]
    error_message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    skip_if_empty: bool = True


class DataValidator:
    """
    Централизованный валидатор данных.
    
    Пример использования:
        validator = DataValidator()
        
        # Добавление правил
        validator.add_rule(ValidationRule(
            name="article_not_empty",
            field="article",
            validator=lambda x: bool(x and x.strip()),
            error_message="Артикул не может быть пустым"
        ))
        
        # Проверка данных
        data = {"article": "  ", "barcode": "123"}
        results = validator.validate(data)
        
        if not results.is_valid:
            print(results.errors)
    """

    def __init__(self):
        self.rules: Dict[str, ValidationRule] = {}
        self.custom_validators: Dict[str, Callable[[Dict[str, Any]], List[ValidationResult]]] = {}

    def add_rule(self, rule: ValidationRule):
        """Добавить правило валидации."""
        self.rules[rule.name] = rule

    def remove_rule(self, rule_name: str):
        """Удалить правило по имени."""
        if rule_name in self.rules:
            del self.rules[rule_name]

    def add_custom_validator(self, name: str, validator: Callable[[Dict[str, Any]], List[ValidationResult]]):
        """
        Добавить кастомный валидатор для сложных проверок.
        
        Args:
            name: Имя валидатора
            validator: Функция, принимающая dict с данными и возвращающая список ValidationResult
        """
        self.custom_validators[name] = validator

    def validate(self, data: Dict[str, Any]) -> 'ValidationReport':
        """
        Проверить данные по всем правилам.
        
        Args:
            data: Словарь с данными для проверки
            
        Returns:
            ValidationReport с результатами всех проверок
        """
        results: List[ValidationResult] = []

        # Применение правил
        for rule in self.rules.values():
            value = data.get(rule.field)
            
            # Пропуск пустых значений если указано
            if rule.skip_if_empty and (value is None or value == ""):
                results.append(ValidationResult.ok(rule.field, value, "Пропущено (пустое значение)"))
                continue
            
            # Проверка
            try:
                is_valid = rule.validator(value)
                if is_valid:
                    results.append(ValidationResult.ok(rule.field, value))
                else:
                    results.append(ValidationResult.fail(
                        field=rule.field,
                        message=rule.error_message,
                        value=value,
                        severity=rule.severity
                    ))
            except Exception as e:
                results.append(ValidationResult.fail(
                    field=rule.field,
                    message=f"Ошибка валидации: {str(e)}",
                    value=value,
                    severity=ValidationSeverity.CRITICAL
                ))

        # Применение кастомных валидаторов
        for validator_func in self.custom_validators.values():
            try:
                custom_results = validator_func(data)
                results.extend(custom_results)
            except Exception as e:
                results.append(ValidationResult.fail(
                    field="_custom",
                    message=f"Ошибка кастомного валидатора: {str(e)}",
                    severity=ValidationSeverity.CRITICAL
                ))

        return ValidationReport(results)

    def validate_or_raise(self, data: Dict[str, Any], exception_class: type = ValueError):
        """
        Проверить данные и выбросить исключение при ошибках.
        
        Args:
            data: Данные для проверки
            exception_class: Класс исключения для выброса
            
        Raises:
            exception_class: Если валидация не пройдена
        """
        report = self.validate(data)
        if not report.is_valid:
            errors = "; ".join([e.message for e in report.errors])
            raise exception_class(f"Валидация не пройдена: {errors}")


@dataclass
class ValidationReport:
    """Отчет о валидации."""
    
    results: List[ValidationResult]
    
    @property
    def is_valid(self) -> bool:
        """Проверить есть ли ошибки уровня ERROR или CRITICAL."""
        return not any(r.is_valid is False and r.severity in 
                      (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL) 
                      for r in self.results)
    
    @property
    def errors(self) -> List[ValidationResult]:
        """Получить все ошибки."""
        return [r for r in self.results if not r.is_valid]
    
    @property
    def warnings(self) -> List[ValidationResult]:
        """Получить все предупреждения."""
        return [r for r in self.results if not r.is_valid and r.severity == ValidationSeverity.WARNING]
    
    @property
    def critical_errors(self) -> List[ValidationResult]:
        """Получить критические ошибки."""
        return [r for r in self.results if not r.is_valid and r.severity == ValidationSeverity.CRITICAL]
    
    def get_errors_by_field(self, field: str) -> List[ValidationResult]:
        """Получить ошибки для конкретного поля."""
        return [r for r in self.errors if r.field == field]
    
    def summary(self) -> str:
        """Получить краткую сводку."""
        total = len(self.results)
        errors = len(self.errors)
        warnings = len(self.warnings)
        
        if errors == 0:
            return f"Валидация пройдена ({total} проверок)"
        else:
            return f"Найдено ошибок: {errors}, предупреждений: {warnings} (всего {total} проверок)"
