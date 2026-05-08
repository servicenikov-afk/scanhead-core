# Domain Module (libs/domain)

Доменные модели и бизнес-логика предметной области.

## Состав

### discrepancy.py
Модуль расчета и классификации расхождений при инвентаризации.

**Классы:**
- `DiscrepancyType` — Enum типов расхождений (OK, SURPLUS, SHORTAGE, ZERO_PLAN, UNPLANNED)
- `DiscrepancyResult` — Dataclass с результатами расчета
- `DiscrepancyCalculator` — Калькулятор для сравнения план/факт

**Пример использования:**
```python
from libs.domain import DiscrepancyCalculator

calc = DiscrepancyCalculator(zero_tolerance=0.01)
result = calc.calculate(plan=100, fact=95)

print(result.discrepancy_type)  # DiscrepancyType.SHORTAGE
print(result.percent_deviation) # -5.0
print(result.is_critical)       # True
```

## Зависимости
- Стандартная библиотека Python (dataclasses, enum, typing)

## Примечания
- Модуль не зависит от GUI и БД
- Подходит для использования в CLI, GUI и серверных приложениях
