# modules/barcode_checker.py

import re
import logging
from typing import Tuple, List, Dict, Any

logger = logging.getLogger(__name__)


class BarcodeChecker:
    """Проверяет совместимость артикулов с типами кодов"""
    
    def __init__(self):
        """Инициализация проверщика"""
        # Code128 поддерживает все печатные ASCII символы (32-126)
        self.code128_valid_chars = set(chr(i) for i in range(32, 127))
    
    @staticmethod
    def normalize_for_barcode(article: str) -> str:
        """Нормализация артикула для штрих-кода (берет первую часть до слэша)"""
        if not article:
            return ""
        
        result = str(article).strip()
        
        # Берем часть до слэша (как в основной логике)
        if '/' in result:
            parts = [part.strip() for part in result.split('/') if part.strip()]
            if parts:
                result = parts[0]
        
        return result
    
    def check_code128_compatibility(self, text: str) -> Tuple[bool, List[str]]:
        """Проверяет совместимость текста с Code128"""
        if not text:
            return True, []
        
        # Нормализуем текст для проверки
        normalized_text = self.normalize_for_barcode(text)
        
        invalid_chars = []
        
        for char in normalized_text:
            code = ord(char)
            if code < 32 or code > 126:  # Только печатные ASCII символы
                invalid_chars.append(char)
        
        invalid_chars = list(set(invalid_chars))
        is_valid = len(invalid_chars) == 0
        
        logger.debug(f"Проверка Code128: '{text}' -> '{normalized_text}' - валидность: {is_valid}")
        return is_valid, invalid_chars
    
    def get_recommended_barcode_type(self, article: str, config: Dict[str, Any]) -> str:
        """Рекомендует тип штрих-кода для артикула"""
        if not article:
            return 'none'
        
        # Нормализуем артикул для проверки
        normalized_article = self.normalize_for_barcode(article)
        
        barcode_type = config.get('barcode.type', 'auto')
        fallback_to_qr = config.get('barcode.auto_rules.fallback_to_qr', True)
        skip_invalid = config.get('barcode.auto_rules.skip_if_invalid', False)
        
        logger.debug(f"Определение типа кода для '{normalized_article}'")
        
        # Если тип указан явно
        if barcode_type != 'auto':
            if barcode_type == 'code128':
                is_valid, _ = self.check_code128_compatibility(normalized_article)
                if not is_valid:
                    if skip_invalid:
                        logger.warning(f"Артикул '{normalized_article}' не совместим с Code128, код пропускается")
                        return 'none'
                    elif fallback_to_qr:
                        logger.warning(f"Артикул '{normalized_article}' не совместим с Code128, используется QR-код")
                        return 'qr'
                    else:
                        logger.warning(f"Артикул '{normalized_article}' не совместим с Code128, используется Code128 (возможны ошибки)")
                        return 'code128'
                else:
                    logger.debug(f"Артикул '{normalized_article}' совместим с Code128")
                    return 'code128'
            elif barcode_type == 'qr':
                logger.debug(f"Используется QR-код для '{normalized_article}' (явно задано)")
                return 'qr'
            elif barcode_type == 'none':
                logger.debug(f"Код не создается для '{normalized_article}' (явно задано)")
                return 'none'
            else:
                logger.warning(f"Неизвестный тип кода: {barcode_type}, используется автоопределение")
        
        # Автоматический выбор
        is_valid, _ = self.check_code128_compatibility(normalized_article)
        
        if is_valid:
            logger.debug(f"Автовыбор: Code128 для '{normalized_article}'")
            return 'code128'
        elif fallback_to_qr:
            logger.debug(f"Автовыбор: QR для '{normalized_article}' (несовместим с Code128)")
            return 'qr'
        elif skip_invalid:
            logger.debug(f"Автовыбор: пропуск кода для '{normalized_article}' (несовместим с Code128)")
            return 'none'
        else:
            logger.warning(f"Автовыбор: Code128 для '{normalized_article}' (несовместим, возможны ошибки)")
            return 'code128'
    
    def validate_article_for_barcode(self, article: str) -> Tuple[bool, str, List[str]]:
        """Расширенная проверка артикула для создания кода"""
        if not article:
            return False, "Пустой артикул", []
        
        # Нормализуем артикул
        normalized_article = self.normalize_for_barcode(article)
        
        is_valid, invalid_chars = self.check_code128_compatibility(normalized_article)
        
        if is_valid:
            return True, "Совместим с Code128", []
        else:
            invalid_str = ', '.join([f"'{c}' (U+{ord(c):04X})" for c in invalid_chars[:5]])
            if len(invalid_chars) > 5:
                invalid_str += f" и еще {len(invalid_chars) - 5} символов"
            
            message = f"Содержит недопустимые для Code128 символы: {invalid_str}"
            return False, message, invalid_chars