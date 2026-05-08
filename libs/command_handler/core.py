"""Command Handler - Обработка команд сканера штрих-кодов

Модуль предоставляет функциональность для:
- Распознавания команд в строках (is_command)
- Парсинга команд в стандартный формат (parse)
- Поддержки команд на русском и английском языках
"""

from typing import Optional
from .data import COMMANDS as CMD_DATA, RUS_COMMANDS as RUS_CMD_DATA


# Маппинг коротких кодов на полные имена команд
COMMANDS = {
    'CMD_START_INV': {'code': '[CMD]START_INV', 'name': 'Начать инвентаризацию'},
    'CMD_FINISH_INV': {'code': '[CMD]FINISH_INV', 'name': 'Завершить инвентаризацию'},
    'CMD_RESET_ACTUAL': {'code': '[CMD]RESET_ACTUAL', 'name': 'Сбросить фактические остатки'},
    'CMD_ADD1': {'code': '[CMD]ADD1', 'name': '+1'},
    'CMD_ADD10': {'code': '[CMD]ADD10', 'name': '+10'},
    'CMD_ADD100': {'code': '[CMD]ADD100', 'name': '+100'},
    'CMD_SUB1': {'code': '[CMD]SUB1', 'name': '-1'},
    'CMD_SUB10': {'code': '[CMD]SUB10', 'name': '-10'},
    'CMD_SUB100': {'code': '[CMD]SUB100', 'name': '-100'},
    'CMD_MANUAL_NEXT': {'code': '[CMD]MANUAL_NEXT', 'name': 'Ручной ввод (следующая)'},
    'CMD_MANUAL_LAST': {'code': '[CMD]MANUAL_LAST', 'name': 'Ручной ввод (последняя)'},
    'CMD_ZERO_LAST': {'code': '[CMD]ZERO_LAST', 'name': 'Обнулить последнюю'},
    'CMD_SHOW_LAST': {'code': '[CMD]SHOW_LAST', 'name': 'Показать последнюю'},
    'CMD_SHOW_EXPECTED': {'code': '[CMD]SHOW_EXPECTED', 'name': 'Показать ожидаемое'},
    'CMD_SHOW_STATS': {'code': '[CMD]SHOW_STATS', 'name': 'Показать статистику'},
}

# Маппинг русской раскладки на идентификаторы команд
RUS_COMMANDS = {
    'хСЬВъЯУКЩ_ДФЫЕ': 'CMD_RESET_ACTUAL',
    'хСЬВъФВВ1': 'CMD_ADD1',
    'хСЬВъФВВ10': 'CMD_ADD10',
    'хСЬВъФВВ100': 'CMD_ADD100',
    'хСЬВъАШТШЫР_ШТМ': 'CMD_START_INV',
    'хСЬВъЬФТГФД_ДФЫЕ': 'CMD_FINISH_INV',
    'хСЬВъЬФТГФД_ТУЧЕ': 'CMD_MANUAL_NEXT',
    'хСЬВъКУЫУЕ_ФСЕГФД': 'CMD_MANUAL_LAST',
    'хСЬВъЫРЩЦ_УЧЗУСЕУВ': 'CMD_SHOW_STATS',
    'хСЬВъЫРЩЦ_ДФЫЕ': 'CMD_SHOW_LAST',
    'хСЬВъЫРЩЦ_ЫЕФЕЫ': 'CMD_SHOW_EXPECTED',
    'хСЬВъЫЕФКЕ_ШТМ': 'CMD_ZERO_LAST',
    'хСЬВъЫГИ1': 'CMD_SUB1',
    'хСЬВъЫГИ10': 'CMD_SUB10',
    'хСЬВъЫГИ100': 'CMD_SUB100',
}

# Объединяем с данными из внешних файлов для расширения
COMMANDS.update(CMD_DATA)
RUS_COMMANDS.update(RUS_CMD_DATA)


class CommandHandler:
    """Обработчик команд сканера штрих-кодов
    
    Предоставляет методы для распознавания и парсинга команд,
    включая поддержку русской раскладки клавиатуры.
    """
    
    @staticmethod
    def is_command(code: str) -> bool:
        """Проверяет, является ли строка командой
        
        Args:
            code: Строка для проверки
            
        Returns:
            True если строка является командой, False иначе
        """
        if not code:
            return False
        
        code_lower = code.lower()
        
        # Проверка на явную команду
        if code in COMMANDS or code.startswith('[CMD]') or 'cmd' in code_lower:
            return True
        
        # Проверка на русскую раскладку
        for rus in RUS_COMMANDS:
            if rus.lower() in code_lower:
                return True
        
        return False
    
    @staticmethod
    def parse(code: str) -> Optional[str]:
        """Парсит строку в идентификатор команды
        
        Args:
            code: Строка для парсинга
            
        Returns:
            Идентификатор команды (например, 'CMD_ADD1') или None
        """
        clean = code
        
        # Удаляем префикс [CMD]
        if clean.startswith('[CMD]'):
            clean = clean[5:]
        
        # Проверяем русскую раскладку
        for rus, cmd in RUS_COMMANDS.items():
            if rus.lower() in code.lower():
                return cmd
        
        # Проверяем стандартные команды
        for cmd_id, cmd_data in COMMANDS.items():
            if cmd_data['code'] == f'[CMD]{clean}' or cmd_id == clean:
                return cmd_id
        
        return None
