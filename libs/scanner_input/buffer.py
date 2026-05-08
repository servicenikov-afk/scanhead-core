"""
Буфер для накопления и обработки символов штрих-кода.

Решает проблемы:
- Дребезг клавиш при быстром вводе
- Частичное чтение данных
- Определение конца ввода по таймауту
"""

import time
import threading
from typing import Optional, Callable, List


class ScanBuffer:
    """
    Буфер для накопления символов штрих-кода.
    
    Автоматически сбрасывается при превышении таймаута между символами.
    Фильтрует невалидные символы и слишком короткие последовательности.
    """

    def __init__(self, min_length: int = 3, timeout_seconds: float = 1.0):
        """
        Инициализация буфера.
        
        Args:
            min_length: Минимальная длина кода для считания валидным.
            timeout_seconds: Таймаут бездействия для сброса буфера.
        """
        self._min_length = min_length
        self._timeout = timeout_seconds
        self._buffer: List[str] = []
        self._last_char_time: float = 0.0
        self._lock = threading.Lock()
        self._callback: Optional[Callable[[str], None]] = None
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def add_char(self, char: str) -> None:
        """
        Добавление символа в буфер.
        
        Если прошло больше времени чем таймаут с последнего символа,
        буфер сбрасывается перед добавлением нового символа.
        
        Args:
            char: Символ для добавления.
        """
        current_time = time.time()
        
        with self._lock:
            # Проверка таймаута
            if self._buffer and (current_time - self._last_char_time) > self._timeout:
                self._buffer.clear()
            
            # Добавление символа
            if char.isprintable():
                self._buffer.append(char)
                self._last_char_time = current_time

    def get_code(self) -> Optional[str]:
        """
        Получение накопленного кода и сброс буфера.
        
        Returns:
            Строка со штрих-кодом или None, если код слишком короткий.
        """
        with self._lock:
            if len(self._buffer) < self._min_length:
                self._buffer.clear()
                return None
            
            code = "".join(self._buffer)
            self._buffer.clear()
            
            # Запуск коллбэка если установлен
            if self._callback:
                self._callback(code)
                
            return code

    def set_callback(self, callback: Callable[[str], None]) -> None:
        """
        Установка функции обратного вызова при получении полного кода.
        
        Args:
            callback: Функция, принимающая строку со штрих-кодом.
        """
        self._callback = callback

    def clear(self) -> None:
        """Принудительная очистка буфера."""
        with self._lock:
            self._buffer.clear()
            self._last_char_time = 0.0

    def start_auto_cleanup(self) -> None:
        """
        Запуск фонового потока для автоматической очистки по таймауту.
        
        Полезно для случаев, когда сканирование было прервано.
        """
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return
            
        self._stop_event.clear()
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def stop_auto_cleanup(self) -> None:
        """Остановка фонового потока очистки."""
        self._stop_event.set()
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=1.0)

    def _cleanup_loop(self) -> None:
        """Фоновый цикл проверки таймаута."""
        while not self._stop_event.is_set():
            time.sleep(0.1)  # Проверка каждые 100мс
            
            with self._lock:
                if self._buffer:
                    elapsed = time.time() - self._last_char_time
                    if elapsed > self._timeout:
                        self._buffer.clear()
