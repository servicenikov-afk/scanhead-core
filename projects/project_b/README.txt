========================================
   Inventory App v1.0
========================================

Структура проекта:

inventory_app/
├── main.py
├── requirements.txt
├── config/
│   └── settings.py
├── core/
│   ├── nomenclature.py
│   ├── address_manager.py
│   └── inventory_parser.py
├── models/
│   ├── product.py
│   ├── count_item.py
│   └── inventory_item.py
├── gui/
│   ├── main_window.py
│   ├── tabs/
│   │   ├── count_tab.py
│   │   ├── inventory_tab.py
│   │   └── search_tab.py
│   └── widgets/
│       └── article_entry.py
├── exporters/
│   ├── excel_exporter.py
│   └── csv_exporter.py
└── utils/
    └── article_normalizer.py

========================================
Установка:
========================================
1. Установите Python 3.8+
2. Запустите: pip install -r requirements.txt
3. Поместите файлы:
   - nomenclature.csv в C:\Users\User\AppData\Local\InventoryApp\
   - addresses.csv в C:\Users\User\AppData\Local\InventoryApp\
4. Запустите: python main.py

========================================
Поддерживаемые форматы ведомости:
========================================
- Артикулы: колонки A и F
- Наименование: колонка J
- Остаток: колонка R

