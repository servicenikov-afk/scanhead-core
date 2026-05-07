# main.py - точка входа с использованием NomenclatureCSV

import tkinter as tk
import sys
from pathlib import Path
import requests

# Добавляем пути к модулям
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "modules"))
sys.path.insert(0, str(current_dir / "gui"))

try:
    from config_manager import ConfigManager
    from nomenclature import NomenclatureCSV
    from invoice_parser import InvoiceParser
    from sticker_generator import StickerGenerator
    from main_window import MainWindow
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    input("Нажмите Enter для выхода...")
    sys.exit(1)

def main():
    """Точка входа приложения"""
    print("Sticker Maker v3.3")
    
    # Инициализация компонентов
    config = ConfigManager()
    
    # Создаем объект для работы с номенклатурой (только CSV, без SQLite)
    csv_path = config.get('paths.csv_path')
    nomenclature = NomenclatureCSV(csv_path)
    
    # Создаем парсер накладных
    invoice_parser = InvoiceParser()
    
    # Создаем генератор стикеров
    generator = StickerGenerator(config)
    
    # Автозагрузка базы номенклатуры
    if config.get('paths.auto_load_database', True):
        print("Загрузка базы номенклатуры из CSV...")
        csv_url = config.get('paths.database_url')
        if csv_url:
            success = nomenclature.download_and_load(csv_url, local_path=csv_path)
            if success:
                print(f"✓ База загружена. Записей: {len(nomenclature.data)}")
            else:
                print("✗ Не удалось загрузить базу")
        else:
            print("✗ URL базы данных не указан в конфигурации")
    
    # Запуск GUI
    root = tk.Tk()
    app = MainWindow(root, config, nomenclature, generator, invoice_parser)
    root.mainloop()

def run_application():
    """Запускает приложение"""
    print("=" * 50)
    print("Sticker Maker v3.3")
    print("=" * 50)
    
    # Инициализация компонентов
    config = ConfigManager()
    
    # Создаем объекты
    nomenclature = NomenclatureCSV(config.get('paths.csv_path'))
    invoice_parser = InvoiceParser(config=config.config)
    generator = StickerGenerator(config)
    
    # Автозагрузка базы номенклатуры
    if config.get('paths.auto_load_database', True):
        print("Загрузка базы номенклатуры из CSV...")
        csv_url = config.get('paths.database_url')
        if csv_url:
            success = nomenclature.download_and_load(csv_url, config.get('paths.csv_path'))
            if success:
                print(f"✓ База загружена. Записей: {len(nomenclature.data)}")
            else:
                print("✗ Не удалось загрузить базу")
        else:
            print("⚠ URL базы данных не указан")
    
    # Запуск GUI
    try:
        from gui.main_window import run_gui
        run_gui(config, nomenclature, generator, invoice_parser)
    except ImportError as e:
        print(f"Ошибка запуска GUI: {e}")
        input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    run_application()