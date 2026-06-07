# Документация проекта ScanHead Combine

## 📚 Структура документации

- [Схема баз данных](database_schema.md) - подробное описание всех трёх БД
- [Несоответствия кода и БД](code_db_mismatches.md) - выявленные проблемы в адаптерах
- [API сервисов](services_api.md) - описание сервисного слоя

---

## 🏗️ Архитектура проекта

```
scanhead-core/
├── libs/
│   └── domain_models/
│       └── product.py          # Доменная модель Product
├── gui/
│   ├── services/
│   │   ├── adapters/
│   │   │   ├── nomenclature_adapter.py  # Адаптер к nomenclature.db
│   │   │   ├── store_adapter.py         # Адаптер к store.db
│   │   │   └── css_export_adapter.py    # Адаптер к css_export.db
│   │   └── product_details_service.py   # Сервис агрегации данных
│   └── dialogs/
│       └── product_info_dialog.py       # Окно детальной информации
├── data/
│   └── databases/
│       ├── nomenclature/     # Основная номенклатура (README внутри)
│       ├── store/            # Складские адреса (README внутри)
│       └── css_export/       # Запчасти Franke (README внутри)
└── docs/
    ├── database_schema.md
    ├── code_db_mismatches.md
    └── services_api.md
```

## 🔧 Версия билда

**Текущая версия:** 2.3

---

## 📝 Примечания

1. Физические файлы баз данных находятся **только на тестовой машине** в директории `\data\databases\`
2. В репозитории присутствуют только README-файлы с описанием структуры БД
3. Каждая база данных содержит собственный README.md с примерами SQL-запросов
