"""
Модуль интернационализации и централизованного хранения сообщений.

Предоставляет единый интерфейс для получения текстовых сообщений
(ошибки, успех, предупреждения) с поддержкой переключения языков.
"""

from typing import Dict, Optional
from enum import Enum


class Language(Enum):
    """Поддерживаемые языки."""
    RU = "ru"
    EN = "en"


# Словарь сообщений на русском языке
RU_MESSAGES: Dict[str, str] = {
    # Общие
    "success": "Успешно",
    "error": "Ошибка",
    "warning": "Предупреждение",
    "confirm": "Подтверждение",
    "cancel": "Отмена",
    "close": "Закрыть",
    "save": "Сохранить",
    "load": "Загрузить",
    "delete": "Удалить",
    "edit": "Редактировать",
    "add": "Добавить",
    
    # Статусы операций
    "operation_completed": "Операция завершена успешно",
    "operation_failed": "Не удалось выполнить операцию",
    "data_saved": "Данные сохранены",
    "data_loaded": "Данные загружены",
    "data_deleted": "Данные удалены",
    "no_data_found": "Данные не найдены",
    "empty_list": "Список пуст",
    
    # Ошибки валидации
    "invalid_input": "Неверный ввод",
    "required_field": "Поле обязательно для заполнения",
    "invalid_format": "Неверный формат данных",
    "duplicate_entry": "Запись уже существует",
    "invalid_article": "Неверный формат артикула",
    "invalid_barcode": "Неверный формат штрих-кода",
    "invalid_quantity": "Количество должно быть положительным числом",
    
    # Ошибки базы данных
    "db_connection_error": "Ошибка подключения к базе данных",
    "db_query_error": "Ошибка выполнения запроса",
    "db_lock_error": "База данных заблокирована",
    "db_not_found": "Запись не найдена в базе данных",
    
    # Ошибки файловых операций
    "file_not_found": "Файл не найден",
    "file_access_error": "Нет доступа к файлу",
    "file_save_error": "Не удалось сохранить файл",
    "file_load_error": "Не удалось загрузить файл",
    "invalid_file_format": "Неверный формат файла",
    
    # Ошибки сканера
    "scanner_error": "Ошибка сканера штрих-кодов",
    "scanner_not_connected": "Сканер не подключен",
    "scanner_timeout": "Превышено время ожидания сканера",
    "barcode_read_error": "Не удалось прочитать штрих-код",
    
    # Ошибки печати
    "printer_error": "Ошибка принтера",
    "printer_not_found": "Принтер не найден",
    "print_failed": "Не удалось распечатать этикетку",
    
    # Сообщения инвентаризации
    "inventory_started": "Инвентаризация начата",
    "inventory_completed": "Инвентаризация завершена",
    "inventory_cancelled": "Инвентаризация отменена",
    "count_saved": "Результаты подсчета сохранены",
    "discrepancy_found": "Обнаружены расхождения",
    "no_discrepancies": "Расхождений не обнаружено",
    
    # Подтверждения
    "confirm_delete": "Вы уверены, что хотите удалить запись?",
    "confirm_cancel": "Вы уверены, что хотите отменить операцию?",
    "confirm_overwrite": "Файл уже существует. Перезаписать?",
}

# Словарь сообщений на английском языке
EN_MESSAGES: Dict[str, str] = {
    # General
    "success": "Success",
    "error": "Error",
    "warning": "Warning",
    "confirm": "Confirmation",
    "cancel": "Cancel",
    "close": "Close",
    "save": "Save",
    "load": "Load",
    "delete": "Delete",
    "edit": "Edit",
    "add": "Add",
    
    # Operation statuses
    "operation_completed": "Operation completed successfully",
    "operation_failed": "Failed to complete operation",
    "data_saved": "Data saved",
    "data_loaded": "Data loaded",
    "data_deleted": "Data deleted",
    "no_data_found": "No data found",
    "empty_list": "List is empty",
    
    # Validation errors
    "invalid_input": "Invalid input",
    "required_field": "Field is required",
    "invalid_format": "Invalid data format",
    "duplicate_entry": "Entry already exists",
    "invalid_article": "Invalid article format",
    "invalid_barcode": "Invalid barcode format",
    "invalid_quantity": "Quantity must be a positive number",
    
    # Database errors
    "db_connection_error": "Database connection error",
    "db_query_error": "Database query error",
    "db_lock_error": "Database is locked",
    "db_not_found": "Record not found in database",
    
    # File operation errors
    "file_not_found": "File not found",
    "file_access_error": "File access denied",
    "file_save_error": "Failed to save file",
    "file_load_error": "Failed to load file",
    "invalid_file_format": "Invalid file format",
    
    # Scanner errors
    "scanner_error": "Barcode scanner error",
    "scanner_not_connected": "Scanner not connected",
    "scanner_timeout": "Scanner timeout",
    "barcode_read_error": "Failed to read barcode",
    
    # Printer errors
    "printer_error": "Printer error",
    "printer_not_found": "Printer not found",
    "print_failed": "Failed to print label",
    
    # Inventory messages
    "inventory_started": "Inventory started",
    "inventory_completed": "Inventory completed",
    "inventory_cancelled": "Inventory cancelled",
    "count_saved": "Count results saved",
    "discrepancy_found": "Discrepancies found",
    "no_discrepancies": "No discrepancies found",
    
    # Confirmations
    "confirm_delete": "Are you sure you want to delete this record?",
    "confirm_cancel": "Are you sure you want to cancel the operation?",
    "confirm_overwrite": "File already exists. Overwrite?",
}


class MessageManager:
    """
    Менеджер сообщений с поддержкой локализации.
    
    Пример использования:
        msg = MessageManager()
        msg.set_language(Language.RU)
        print(msg.get("success"))  # "Успешно"
        
        # Или с подстановкой параметров
        print(msg.get("data_saved", table="Products"))  # "Данные сохранены в таблицу Products"
    """
    
    def __init__(self, default_language: Language = Language.RU):
        self._language = default_language
        self._messages: Dict[Language, Dict[str, str]] = {
            Language.RU: RU_MESSAGES,
            Language.EN: EN_MESSAGES,
        }
        self._custom_messages: Dict[Language, Dict[str, str]] = {
            Language.RU: {},
            Language.EN: {},
        }
    
    def set_language(self, language: Language) -> None:
        """Установить текущий язык."""
        self._language = language
    
    def get_language(self) -> Language:
        """Получить текущий язык."""
        return self._language
    
    def add_message(self, key: str, text: str, language: Optional[Language] = None) -> None:
        """
        Добавить пользовательское сообщение.
        
        Args:
            key: Уникальный ключ сообщения
            text: Текст сообщения
            language: Язык сообщения (по умолчанию текущий)
        """
        lang = language or self._language
        self._custom_messages[lang][key] = text
    
    def get(self, key: str, **kwargs) -> str:
        """
        Получить сообщение по ключу.
        
        Args:
            key: Ключ сообщения
            **kwargs: Параметры для подстановки в текст (format-строки)
            
        Returns:
            Текст сообщения на текущем языке
            
        Raises:
            KeyError: Если ключ не найден ни в стандартных, ни в пользовательских сообщениях
        """
        # Сначала ищем в пользовательских сообщениях
        if key in self._custom_messages[self._language]:
            message = self._custom_messages[self._language][key]
        # Затем в стандартных
        elif key in self._messages[self._language]:
            message = self._messages[self._language][key]
        # Если не нашли, пробуем fallback на английский
        elif key in self._messages[Language.EN]:
            message = self._messages[Language.EN][key]
        else:
            raise KeyError(f"Message key '{key}' not found for language {self._language}")
        
        # Подстановка параметров
        if kwargs:
            try:
                message = message.format(**kwargs)
            except KeyError as e:
                # Если параметр не найден, оставляем как есть
                pass
        
        return message
    
    def get_all_keys(self, language: Optional[Language] = None) -> list:
        """Получить список всех доступных ключей сообщений."""
        lang = language or self._language
        keys = set(self._messages[lang].keys())
        keys.update(self._custom_messages[lang].keys())
        return sorted(list(keys))


# Глобальный экземпляр для удобного использования
_default_manager = MessageManager()


def get_message(key: str, **kwargs) -> str:
    """Получить сообщение через глобальный менеджер."""
    return _default_manager.get(key, **kwargs)


def set_language(language: Language) -> None:
    """Установить язык для глобального менеджера."""
    _default_manager.set_language(language)


def add_message(key: str, text: str, language: Optional[Language] = None) -> None:
    """Добавить сообщение в глобальный менеджер."""
    _default_manager.add_message(key, text, language)
