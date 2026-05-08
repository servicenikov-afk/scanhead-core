# Printing Module (libs/printing)

Генерация печатных форм и этикеток со штрих-кодами.

## Состав

### sticker_generator.py
Генератор этикеток со штрих-кодами.

**Возможности:**
- Поддержка форматов: Code128, EAN13, QR Code
- Генерация изображений (PNG, JPEG) через Pillow
- Настройка размеров, шрифтов, отступов
- Добавление текста под штрих-кодом

**Пример использования:**
```python
from libs.printing import StickerGenerator

gen = StickerGenerator()
gen.generate_barcode_image(
    barcode="1234567890",
    barcode_type="CODE128",
    output_path="label.png",
    width=300,
    height=100
)
```

## Зависимости
- `Pillow` — для работы с изображениями
- `python-barcode` или `qrcode` — для генерации штрих-кодов (опционально, можно использовать встроенный `libs.barcode_generator`)

## Примечания
- Модуль не зависит от GUI
- Подходит для пакетной генерации этикеток в CLI-режиме
