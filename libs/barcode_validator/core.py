import re
from typing import Optional, Tuple

class BarcodeValidator:
    """Валидация штрих-кодов (EAN-13, Code-128, QR)."""

    @staticmethod
    def validate_ean13(code: str) -> Tuple[bool, Optional[str]]:
        """Проверка EAN-13: длина 12 или 13 цифр, контрольная сумма."""
        if not code:
            return False, "Пустой код"
        
        clean_code = re.sub(r'\D', '', code)
        
        if len(clean_code) == 12:
            # Если передано 12 цифр, просто проверяем формат (контрольную сумму посчитаем при генерации)
            return True, None
        
        if len(clean_code) != 13:
            return False, f"Неверная длина EAN-13: {len(clean_code)} (ожидалось 12 или 13)"
        
        if not clean_code.isdigit():
            return False, "EAN-13 должен содержать только цифры"

        # Проверка контрольной суммы
        total = 0
        for i, digit in enumerate(clean_code[:-1]):
            d = int(digit)
            total += d * 3 if i % 2 == 1 else d
        
        check_digit = (10 - (total % 10)) % 10
        if check_digit != int(clean_code[-1]):
            return False, f"Неверная контрольная сумма EAN-13. Ожидалась {check_digit}, получена {clean_code[-1]}"
        
        return True, None

    @staticmethod
    def validate_code128(code: str) -> Tuple[bool, Optional[str]]:
        """Базовая проверка Code-128 (непустая строка)."""
        if not code:
            return False, "Пустой код Code-128"
        # Полная валидация контрольной суммы требует сложных таблиц символов
        return True, None

    @staticmethod
    def sanitize_for_qr(data: str) -> str:
        """Очистка данных для QR-кода (убирает опасные символы, если нужно)."""
        # Пока возвращаем как есть, но здесь можно добавить логику экранирования
        return data.strip()