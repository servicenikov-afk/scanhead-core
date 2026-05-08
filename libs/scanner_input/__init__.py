"""
Модуль для работы со сканерами штрих-кодов.

Поддерживает различные источники ввода:
- HID-сканеры (USB, Bluetooth)
- Камеры (через заглушку или будущую реализацию)
- Файлы (для тестирования)

Пример использования:
    from libs.scanner_input import HidScanner, CameraStub
    
    # Инициализация сканера
    scanner = HidScanner()
    
    # Обработка события сканирования
    def on_scan(code: str):
        print(f"Отсканировано: {code}")
    
    scanner.set_callback(on_scan)
    scanner.start_listening()
"""

from .interfaces import ScannerProvider
from .hid_scanner import HidScanner
from .camera_stub import CameraStub
from .buffer import ScanBuffer

__all__ = [
    "ScannerProvider",
    "HidScanner",
    "CameraStub",
    "ScanBuffer",
]
