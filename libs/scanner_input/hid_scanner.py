"""
Реализация сканера штрих-кодов для HID-устройств.

Обрабатывает ввод от USB/Bluetooth сканеров, работающих в режиме клавиатуры.
Фильтрует артефакты ввода, определяет конец строки по символу Enter.
"""

import sys
import tty
import termios
import threading
from typing import Optional, Callable

from .interfaces import ScannerProvider
from .buffer import ScanBuffer


class HidScanner(ScannerProvider):
    """
    Сканер штрих-кодов для HID-устройств.
    
    Работает в режиме чтения сырого ввода из stdin.
    Автоматически определяет конец штрих-кода по символу перевода строки.
    """

    def __init__(self, min_length: int = 3, timeout_seconds: float = 1.0):
        """
        Инициализация HID-сканера.
        
        Args:
            min_length: Минимальная длина штрих-кода для отсечения шума.
            timeout_seconds: Таймаут между символами для определения конца ввода.
        """
        super().__init__()
        self._min_length = min_length
        self._timeout = timeout_seconds
        self._buffer = ScanBuffer(min_length=min_length, timeout_seconds=timeout_seconds)
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._old_settings: Optional[list] = None

    def start_listening(self) -> None:
        """Запуск потока прослушивания HID-устройства."""
        if self._is_active:
            return

        self._is_active = True
        self._stop_event.clear()
        
        # Сохраняем настройки терминала
        if sys.stdin.isatty():
            self._old_settings = termios.tcgetattr(sys.stdin.fileno())
            tty.setcbreak(sys.stdin.fileno())

        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop_listening(self) -> None:
        """Остановка прослушивания и восстановление настроек терминала."""
        if not self._is_active:
            return

        self._is_active = False
        self._stop_event.set()
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        # Восстанавливаем настройки терминала
        if self._old_settings and sys.stdin.isatty():
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self._old_settings)
            self._old_settings = None

    def _listen_loop(self) -> None:
        """Основной цикл чтения ввода."""
        while not self._stop_event.is_set():
            try:
                char = sys.stdin.read(1)
                if not char:
                    continue
                
                # Обработка специальных символов
                if char in ('\n', '\r'):
                    code = self._buffer.get_code()
                    if code:
                        self._notify_callback(code)
                else:
                    self._buffer.add_char(char)
                    
            except Exception as e:
                # Логирование ошибки (в реальном проекте использовать logging)
                print(f"Error reading from HID scanner: {e}")
                break

    def set_callback(self, callback: Callable[[str], None]) -> None:
        """Установка обработчика штрих-кодов."""
        super().set_callback(callback)
        # Переопределяем коллбэк буфера для автоматической передачи
        self._buffer.set_callback(lambda code: self._notify_callback(code) if self._is_active else None)
