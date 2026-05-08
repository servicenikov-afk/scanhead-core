"""
Утилиты для генерации имен файлов по шаблонам.
Позволяет гибко настраивать формат именования экспортируемых файлов.
"""
import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class FileNameGenerator:
    """
    Генератор имен файлов на основе шаблонов.
    
    Поддерживаемые переменные в шаблоне:
        {date}      - Дата в формате YYYY-MM-DD
        {time}      - Время в формате HH-MM-SS
        {timestamp} - Unix timestamp
        {type}      - Тип файла (например, 'inventory', 'report')
        {counter}   - Счетчик (для избежания коллизий)
        {prefix}    - Пользовательский префикс
        {suffix}    - Пользовательский суффикс
    
    Пример использования:
        gen = FileNameGenerator()
        name = gen.generate("inventory_{date}_{type}", type="export", ext="xlsx")
        # Результат: inventory_2023-10-05_export.xlsx
    """

    DEFAULT_TEMPLATE = "{date}_{type}_{time}"
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H-%M-%S"

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Инициализация генератора.
        
        Args:
            base_dir: Базовая директория для сохранения. Если None, используется текущая.
        """
        self.base_dir = base_dir or Path.cwd()
        self._counter = 0

    def generate(
        self, 
        template: Optional[str] = None, 
        ext: str = "txt",
        **kwargs: Any
    ) -> Path:
        """
        Сгенерировать имя файла.
        
        Args:
            template: Шаблон имени. Если None, используется шаблон по умолчанию.
            ext: Расширение файла (без точки).
            **kwargs: Переменные для подстановки в шаблон (type, prefix, suffix и т.д.).
            
        Returns:
            Полный путь к файлу (Path).
        """
        if template is None:
            template = self.DEFAULT_TEMPLATE

        now = datetime.datetime.now()
        
        # Подготовка переменных окружения
        variables: Dict[str, Any] = {
            "date": now.strftime(self.DATE_FORMAT),
            "time": now.strftime(self.TIME_FORMAT),
            "timestamp": int(now.timestamp()),
            "type": kwargs.get("type", "data"),
            "prefix": kwargs.get("prefix", ""),
            "suffix": kwargs.get("suffix", ""),
        }
        
        # Автоинкремент счетчика если нужен
        if "{counter}" in template:
            self._counter += 1
            variables["counter"] = self._counter
        else:
            # Сброс счетчика если он не используется в шаблоне
            self._counter = 0

        # Подстановка значений
        try:
            filename = template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Неизвестная переменная в шаблоне: {e}")

        # Очистка имени от лишних разделителей
        filename = self._clean_filename(filename)
        
        # Добавление расширения
        if not filename.endswith(f".{ext}"):
            filename = f"{filename}.{ext}"

        return self.base_dir / filename

    def _clean_filename(self, name: str) -> str:
        """Очистить имя файла от двойных разделителей и пробелов по краям."""
        # Замена пробелов на подчеркивания
        name = name.replace(" ", "_")
        
        # Удаление двойных подчеркиваний и дефисов
        while "__" in name:
            name = name.replace("__", "_")
        while "--" in name:
            name = name.replace("--", "-")
            
        # Удаление разделителей по краям
        name = name.strip("_-")
        
        # Удаление префиксов/суффиксов если они пустые (чтобы не было _type_)
        name = name.replace("__", "_")
        
        return name

    def reset_counter(self):
        """Сбросить внутренний счетчик."""
        self._counter = 0
