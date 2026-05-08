"""
Заглушка для сканера на основе камеры.

Предназначена для будущей реализации сканирования через камеру телефона/веб-камеру.
Сейчас имитирует задержку сканирования и возвращает тестовые данные.
"""

import threading
import time
from typing import Optional, List

from .interfaces import ScannerProvider


class CameraStub(ScannerProvider):
    """
    Заглушка сканера камеры для разработки и тестирования.
    
    Имитирует процесс сканирования с задержкой и выдает предопределенные коды.
    В будущем будет заменена на реальную реализацию с OpenCV/ZBar.
    """

    def __init__(self, test_codes: Optional[List[str]] = None, scan_interval: float = 2.0):
        """
        Инициализация заглушки камеры.
        
        Args:
            test_codes: Список тестовых штрих-кодов для эмуляции.
            scan_interval: Интервал между "сканированиями" в секундах.
        """
        super().__init__()
        self._test_codes = test_codes or [
            "2000000000000",
            "4601234567890",
            "TEST-CODE-123",
        ]
        self._scan_interval = scan_interval
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._current_index = 0

    def start_listening(self) -> None:
        """Запуск эмуляции сканирования."""
        if self._is_active:
            return

        self._is_active = True
        self._stop_event.clear()
        self._current_index = 0

        self._thread = threading.Thread(target=self._scan_loop, daemon=True)
        self._thread.start()

    def stop_listening(self) -> None:
        """Остановка эмуляции."""
        if not self._is_active:
            return

        self._is_active = False
        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def _scan_loop(self) -> None:
        """Цикл эмуляции сканирования."""
        while not self._stop_event.is_set():
            # Эмуляция задержки обработки изображения
            time.sleep(self._scan_interval)
            
            if not self._is_active:
                break

            # Получение следующего тестового кода
            code = self._get_next_code()
            if code:
                self._notify_callback(code)

    def _get_next_code(self) -> str:
        """Получение следующего тестового кода по кругу."""
        code = self._test_codes[self._current_index % len(self._test_codes)]
        self._current_index += 1
        return code

    def set_test_codes(self, codes: List[str]) -> None:
        """
        Установка нового списка тестовых кодов.
        
        Args:
            codes: Список штрих-кодов для эмуляции.
        """
        self._test_codes = codes
