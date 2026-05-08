"""
Модуль для расчета и классификации расхождений при инвентаризации.
Изолирует бизнес-логику сравнения плановых и фактических остатков.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union


class DiscrepancyType(Enum):
    """Тип расхождения."""
    OK = "ok"              # Совпадение
    SURPLUS = "surplus"    # Излишек (факт > план)
    SHORTAGE = "shortage"  # Недостача (факт < план)
    ZERO_PLAN = "zero_plan" # Факт при нулевом плане
    UNPLANNED = "unplanned" # Позиция не была в плане


@dataclass
class DiscrepancyResult:
    """Результат расчета расхождения."""
    discrepancy_type: DiscrepancyType
    difference: float           # Разница (Fact - Plan)
    percent_deviation: float    # Процент отклонения от плана
    status_message: str         # Человекочитаемый статус

    @property
    def is_critical(self) -> bool:
        """Является ли расхождение критическим."""
        return self.discrepancy_type in (DiscrepancyType.SHORTAGE, DiscrepancyType.SURPLUS)


class DiscrepancyCalculator:
    """
    Калькулятор расхождений.
    
    Пример использования:
        calc = DiscrepancyCalculator()
        result = calc.calculate(plan=100, fact=95)
        print(result.status_message)
    """

    def __init__(self, zero_tolerance: float = 0.0):
        """
        Инициализация калькулятора.
        
        Args:
            zero_tolerance: Допустимая погрешность для считать нулем (например, 0.01).
        """
        self.zero_tolerance = zero_tolerance

    def calculate(
        self, 
        plan: Optional[Union[int, float]], 
        fact: Union[int, float]
    ) -> DiscrepancyResult:
        """
        Рассчитать расхождение между планом и фактом.
        
        Args:
            plan: Плановое количество (может быть None, если позиция не запланирована).
            fact: Фактическое количество.
            
        Returns:
            Объект DiscrepancyResult с деталями расчета.
        """
        # Нормализация входных данных
        if plan is None:
            return self._handle_unplanned(fact)
        
        plan = float(plan)
        fact = float(fact)
        diff = fact - plan

        # Обработка случая, когда план был 0
        if abs(plan) < self.zero_tolerance:
            return self._handle_zero_plan(fact, diff)

        # Стандартное сравнение
        if abs(diff) < self.zero_tolerance:
            return DiscrepancyResult(
                discrepancy_type=DiscrepancyType.OK,
                difference=0.0,
                percent_deviation=0.0,
                status_message="Совпадение"
            )
        
        percent = (diff / plan) * 100.0
        
        if diff > 0:
            dtype = DiscrepancyType.SURPLUS
            msg = f"Излишек: +{diff:.2f} ({percent:.1f}%)"
        else:
            dtype = DiscrepancyType.SHORTAGE
            msg = f"Недостача: {diff:.2f} ({percent:.1f}%)"

        return DiscrepancyResult(
            discrepancy_type=dtype,
            difference=diff,
            percent_deviation=percent,
            status_message=msg
        )

    def _handle_unplanned(self, fact: float) -> DiscrepancyResult:
        """Обработка позиции, которой не было в плане."""
        if abs(fact) < self.zero_tolerance:
            # Нашли 0 там, где не планировали - это нормально, просто игнорируем
            return DiscrepancyResult(
                discrepancy_type=DiscrepancyType.OK,
                difference=0.0,
                percent_deviation=0.0,
                status_message="Не запланировано (пусто)"
            )
        
        return DiscrepancyResult(
            discrepancy_type=DiscrepancyType.UNPLANNED,
            difference=fact,
            percent_deviation=0.0, # Нельзя рассчитать процент от 0 или None
            status_message=f"Не запланировано: найдено {fact}"
        )

    def _handle_zero_plan(self, fact: float, diff: float) -> DiscrepancyResult:
        """Обработка случая, когда план был 0, а факт есть."""
        return DiscrepancyResult(
            discrepancy_type=DiscrepancyType.ZERO_PLAN,
            difference=diff,
            percent_deviation=0.0,
            status_message=f"Найдено при нулевом плане: {fact}"
        )
