# main.py
import sys
import os
import logging
import socket
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gui.main_window import MainWindow

def setup_logging():
    log_dir = Path.home() / "AppData" / "Local" / "InventoryApp" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "inventory_app.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(log_file, encoding='utf-8'), logging.StreamHandler()]
    )

def is_already_running():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('127.0.0.1', 51234))
        sock.close()
        return False
    except socket.error:
        return True

def main():
    if is_already_running():
        print("Приложение уже запущено.")
        return
    setup_logging()
    logger = logging.getLogger(__name__)
    try:
        logger.info("Запуск ScanHead")
        app = MainWindow()
        app.run()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    main()