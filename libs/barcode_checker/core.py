"""
Barcode Checker Core
Логика проверки и валидации штрих-кодов.
"""

from typing import Optional, List


class BarcodeChecker:
    """
    Класс для проверки и валидации штрих-кодов различных форматов.
    
    Поддерживаемые форматы:
    - EAN-13 (European Article Number)
    - EAN-8
    - UPC-A (Universal Product Code)
    - Code-128 (требует реализации)
    
    Примеры использования:
        checker = BarcodeChecker()
        is_valid = checker.validate_ean13("4601234567890")
    """

    def __init__(self):
        """Инициализация проверщика штрих-кодов."""
        pass

    def validate_ean13(self, barcode: str) -> bool:
        """
        Проверить валидность EAN-13 штрих-кода по контрольной сумме.
        
        Args:
            barcode: 13-значный штрих-код
            
        Returns:
            True если штрих-код валиден
        """
        if not barcode:
            return False
        
        # Очистка от пробелов и дефисов
        barcode = barcode.replace(' ', '').replace('-', '')
        
        # Проверка длины
        if len(barcode) != 13:
            return False
        
        # Проверка что все символы цифры
        if not barcode.isdigit():
            return False
        
        # Вычисление контрольной суммы
        digits = [int(d) for d in barcode]
        checksum = sum(digits[i] for i in range(0, 12, 2))  # Нечетные позиции (0-indexed)
        checksum += sum(digits[i] * 3 for i in range(1, 12, 2))  # Четные позиции
        
        expected_check_digit = (10 - (checksum % 10)) % 10
        actual_check_digit = digits[12]
        
        return expected_check_digit == actual_check_digit

    def calculate_ean13_check_digit(self, barcode_12: str) -> Optional[int]:
        """
        Вычислить контрольную цифру для 12-значного префикса EAN-13.
        
        Args:
            barcode_12: 12-значный префикс
            
        Returns:
            Контрольная цифра или None если входные данные невалидны
        """
        if not barcode_12 or len(barcode_12) != 12 or not barcode_12.isdigit():
            return None
        
        digits = [int(d) for d in barcode_12]
        checksum = sum(digits[i] for i in range(0, 12, 2))
        checksum += sum(digits[i] * 3 for i in range(1, 12, 2))
        
        return (10 - (checksum % 10)) % 10

    def validate_ean8(self, barcode: str) -> bool:
        """
        Проверить валидность EAN-8 штрих-кода.
        TODO: Реализовать логику проверки EAN-8.
        
        Args:
            barcode: 8-значный штрих-код
            
        Returns:
            True если штрих-код валиден
        """
        raise NotImplementedError("Метод validate_ean8 требует реализации")

    def validate_upc_a(self, barcode: str) -> bool:
        """
        Проверить валидность UPC-A штрих-кода.
        TODO: Реализовать логику проверки UPC-A.
        
        Args:
            barcode: 12-значный штрих-код
            
        Returns:
            True если штрих-код валиден
        """
        raise NotImplementedError("Метод validate_upc_a требует реализации")

    def validate_code128(self, barcode: str) -> bool:
        """
        Проверить валидность Code-128 штрих-кода.
        TODO: Реализовать логику проверки Code-128.
        
        Args:
            barcode: Штрих-код формата Code-128
            
        Returns:
            True если штрих-код валиден
        """
        raise NotImplementedError("Метод validate_code128 требует реализации")

    def normalize(self, barcode: str) -> str:
        """
        Нормализовать штрих-код (удалить пробелы, дефисы).
        
        Args:
            barcode: Исходный штрих-код
            
        Returns:
            Нормализованный штрих-код
        """
        if not barcode:
            return ""
        
        return barcode.replace(' ', '').replace('-', '').strip()

    def detect_format(self, barcode: str) -> Optional[str]:
        """
        Определить формат штрих-кода по длине и структуре.
        
        Args:
            barcode: Штрих-код для определения формата
            
        Returns:
            Название формата ('EAN-13', 'EAN-8', 'UPC-A') или None
        """
        normalized = self.normalize(barcode)
        
        if not normalized.isdigit():
            return None
        
        length = len(normalized)
        
        if length == 13:
            return 'EAN-13'
        elif length == 8:
            return 'EAN-8'
        elif length == 12:
            return 'UPC-A'
        
        return None

    def get_supported_formats(self) -> List[str]:
        """
        Получить список поддерживаемых форматов.
        
        Returns:
            Список названий форматов
        """
        return ['EAN-13', 'EAN-8', 'UPC-A', 'Code-128']
