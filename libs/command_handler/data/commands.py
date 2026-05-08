"""
Словарь команд сканера штрих-кода.

Этот файл содержит маппинг коротких кодов команд на их полные названия.
Используется модулем command_handler для распознавания команд, вводимых через сканер.

Формат: "код_команды": "полное_название_команды"
"""

# Стандартные команды управления процессом инвентаризации
COMMANDS = {
    # === Управление процессом ===
    "start": "start_inventory",      # Начать новую инвентаризацию
    "stop": "stop_inventory",        # Остановить текущую инвентаризацию
    "pause": "pause_inventory",      # Поставить на паузу
    "resume": "resume_inventory",    # Возобновить после паузы
    "cancel": "cancel_inventory",    # Отменить текущую операцию
    
    # === Работа с данными ===
    "add": "add_item",               # Добавить товар
    "remove": "remove_item",         # Удалить товар
    "edit": "edit_item",             # Редактировать позицию
    "find": "find_item",             # Поиск товара
    "list": "list_items",            # Показать список товаров
    "count": "count_items",          # Подсчитать количество позиций
    "total": "show_total",           # Показать итоговые суммы
    "clear": "clear_list",           # Очистить список
    
    # === Экспорт и импорт ===
    "export": "export_data",         # Экспортировать данные
    "import": "import_data",         # Импортировать данные
    "save": "save_to_file",          # Сохранить в файл
    "load": "load_from_file",        # Загрузить из файла
    "print": "print_labels",         # Печать этикеток
    
    # === Навигация ===
    "up": "navigate_up",             # Вверх по списку
    "down": "navigate_down",         # Вниз по списку
    "next": "navigate_next",         # Следующий элемент
    "prev": "navigate_prev",         # Предыдущий элемент
    "first": "navigate_first",       # Первый элемент
    "last": "navigate_last",         # Последний элемент
    
    # === Системные ===
    "help": "show_help",             # Показать справку
    "info": "show_info",             # Показать информацию
    "settings": "open_settings",     # Открыть настройки
    "exit": "exit_app",              # Выход из приложения
    "quit": "quit_app",              # Завершить работу
    "refresh": "refresh_data",       # Обновить данные
    "sync": "sync_data",             # Синхронизировать данные
    
    # === Специфичные для инвентаризации ===
    "scan": "scan_barcode",          # Сканировать штрих-код
    "manual": "manual_entry",        # Ручной ввод
    "verify": "verify_item",         # Проверить позицию
    "diff": "show_differences",      # Показать расхождения
    "report": "generate_report",     # Сгенерировать отчёт
}
