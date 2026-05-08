"""
Генератор изображений этикеток (стикеров) с штрих-кодами.
Независимый модуль для создания печатных форм.
"""
from PIL import Image, ImageDraw, ImageFont
import qrcode
from barcode import Code128, EAN13
from barcode.writer import ImageWriter
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, Union, List
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


class StickerGenerator:
    """
    Генератор этикеток на основе конфигурации.
    
    Поддерживает:
        - Разные размеры (в мм)
        - Штрих-коды Code128 и EAN13
        - QR-коды
        - Произвольный текст с переносом строк
        - Пресеты оформления
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Инициализация генератора.
        
        Args:
            config: Словарь конфигурации. Если None, используются значения по умолчанию.
        """
        self.config = config or {}
        self.dpi = self._get('sticker.dpi', 300)
        self.mm_to_inch = 1 / 25.4
        self.font_cache: Dict[str, ImageFont.FreeTypeFont] = {}
        self.available_fonts = self._find_fonts()

    def _get(self, key_path: str, default: Any = None) -> Any:
        """Безопасное получение вложенного значения из конфига."""
        if isinstance(self.config, dict):
            v, keys = self.config, key_path.split('.')
            try:
                for k in keys:
                    v = v[k]
                return v
            except (KeyError, TypeError):
                return default
        return default

    def _find_fonts(self) -> Dict[str, str]:
        """Поиск доступных системных шрифтов (Windows)."""
        fonts = {}
        win_fonts = "C:\\Windows\\Fonts"
        font_map = [
            ("arial.ttf", "arial", "n"), ("arialbd.ttf", "arial", "b"),
            ("ariali.ttf", "arial", "i"), ("arialbi.ttf", "arial", "bi"),
            ("calibri.ttf", "calibri", "n"), ("calibrib.ttf", "calibri", "b"),
            ("tahoma.ttf", "tahoma", "n"), ("tahomabd.ttf", "tahoma", "b"),
            ("verdana.ttf", "verdana", "n"), ("verdanab.ttf", "verdana", "b"),
        ]
        
        for fname, family, style in font_map:
            path = f"{win_fonts}\\{fname}"
            if Path(path).exists():
                fonts[f"{family}_{style}"] = path
        
        if not fonts:
            fonts['default'] = None
        return fonts

    def _get_font(self, size_pt: int, bold: bool = False, italic: bool = False, 
                  font_family: Optional[str] = None) -> ImageFont.FreeTypeFont:
        """Получить объект шрифта с кэшированием."""
        ff = (font_family or self._get('fonts.default_font', 'Arial')).lower()
        style = ('b' if bold else '') + ('i' if italic else '') or 'n'
        size_px = int(size_pt * self.dpi / 72)
        key = f"{ff}_{style}_{size_px}"
        
        if key in self.font_cache:
            return self.font_cache[key]
        
        font_path = None
        # Поиск точного совпадения
        for k, p in self.available_fonts.items():
            if k.startswith(f"{ff}_{style}"):
                font_path = p
                break
        
        # Поиск семейства без стиля
        if not font_path:
            for k, p in self.available_fonts.items():
                if k.startswith(f"{ff}_"):
                    font_path = p
                    break
        
        # Любой доступный шрифт
        if not font_path and self.available_fonts:
            font_path = next(iter(self.available_fonts.values()))
            
        try:
            font = ImageFont.truetype(font_path, size_px) if font_path else ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()
            
        self.font_cache[key] = font
        return font

    def _mm_to_pixels(self, mm: float) -> int:
        """Конвертация миллиметров в пиксели."""
        return int(mm * self.mm_to_inch * self.dpi)

    def _get_sticker_size(self) -> Tuple[int, int]:
        """Получить размер стикера в пикселях."""
        width_mm = self._get('sticker.width_mm', 40)
        height_mm = self._get('sticker.height_mm', 20)
        
        if self._get('sticker.orientation') == 'landscape':
            width_mm, height_mm = height_mm, width_mm
            
        return self._mm_to_pixels(width_mm), self._mm_to_pixels(height_mm)

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
        """Разбить текст на строки для размещения в заданной ширине."""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            if bbox[2] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                # Если слово само по себе длиннее строки, разбиваем его (упрощенно)
                if font.getbbox(word)[2] > max_width:
                    lines.append(word)
                    current_line = []
                else:
                    current_line = [word]
                    
        if current_line:
            lines.append(' '.join(current_line))
            
        return lines

    def generate(
        self,
        article: str,
        name: str,
        address: Optional[str] = None,
        quantity: Optional[Union[int, float]] = None,
        unit: str = "шт",
        barcode_type: str = "code128",
        preset: Optional[Dict[str, Any]] = None
    ) -> Image.Image:
        """
        Сгенерировать изображение этикетки.
        
        Args:
            article: Артикул товара.
            name: Наименование товара.
            address: Адрес хранения (ячейка).
            quantity: Количество.
            unit: Единица измерения.
            barcode_type: Тип штрих-кода ('code128', 'ean13', 'qr').
            preset: Переопределение настроек пресета.
            
        Returns:
            Объект PIL.Image с готовой этикеткой.
        """
        # Применение пресета к конфигурации (временное)
        old_config = self.config.copy() if self.config else {}
        if preset:
            self.config.update(preset)
            
        try:
            img, draw = self._create_base_image()
            width, height = img.size
            
            # Нормализация артикула
            clean_article = str(article).strip()
            if '/' in clean_article:
                clean_article = clean_article.split('/')[0].strip()
            
            # Параметры макета
            show_barcode = self._get('layout.show_barcode', True)
            show_qr = self._get('layout.show_qr', False)
            font_size_title = self._get('fonts.name_size', 10)
            font_size_article = self._get('fonts.article_size', 12)
            font_size_addr = self._get('fonts.address_size', 8)
            
            y_cursor = 5
            padding = 5
            
            # 1. Артикул (крупно сверху или снизу)
            if self._get('layout.article_position') == 'top':
                f_art = self._get_font(font_size_article, bold=True)
                draw.text((padding, y_cursor), clean_article, fill='black', font=f_art)
                y_cursor += font_size_article + 2
            
            # 2. Наименование
            max_text_w = width - (2 * padding)
            f_name = self._get_font(font_size_title)
            lines = self._wrap_text(name, f_name, max_text_w)
            
            for line in lines:
                if y_cursor < height - 20: # Оставить место под штрих-код
                    draw.text((padding, y_cursor), line, fill='black', font=f_name)
                    y_cursor += font_size_title + 1
            
            # 3. Адрес
            if address and self._get('layout.show_address', True):
                f_addr = self._get_font(font_size_addr, italic=True)
                addr_y = height - 15 if self._get('layout.address_position') == 'bottom' else y_cursor
                if addr_y < height - 10:
                    draw.text((padding, addr_y), f"Яч: {address}", fill='gray', font=f_addr)
            
            # 4. Количество
            if quantity is not None:
                qty_str = f"{quantity} {unit}"
                f_qty = self._get_font(14, bold=True)
                # Справа сверху или снизу
                qx = width - padding - 50
                qy = 5 if self._get('layout.quantity_position') == 'top_right' else height - 20
                draw.text((qx, qy), qty_str, fill='blue', font=f_qty)
            
            # 5. Штрих-код
            if show_barcode and barcode_type != 'qr':
                bc_h = self._mm_to_pixels(self._get('sticker.barcode_height_mm', 10))
                bc_y = height - bc_h - 2
                
                try:
                    if barcode_type == 'ean13':
                        # EAN13 требует 12-13 цифр, иначе fallback на Code128
                        digits = ''.join(filter(str.isdigit, clean_article))
                        if len(digits) >= 12:
                            code = EAN13(digits[:13], writer=ImageWriter())
                        else:
                            code = Code128(clean_article, writer=ImageWriter())
                    else:
                        code = Code128(clean_article, writer=ImageWriter())
                    
                    # Генерация в буфер
                    buf = BytesIO()
                    code.write(buf, options={'module_width': 0.2, 'module_height': bc_h})
                    bc_img = Image.open(buf)
                    
                    # Центрирование
                    bc_x = (width - bc_img.width) // 2
                    img.paste(bc_img, (bc_x, bc_y))
                except Exception as e:
                    logger.warning(f"Ошибка генерации штрих-кода: {e}")
                    draw.text((padding, bc_y), "[Barcode Error]", fill='red', font=f_addr)
            
            # 6. QR-код (если нужен отдельно)
            if show_qr or barcode_type == 'qr':
                qr_size = self._mm_to_pixels(15)
                qr_data = clean_article
                qr = qrcode.QRCode(version=1, box_size=10, border=2)
                qr.add_data(qr_data)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white")
                qr_img = qr_img.resize((qr_size, qr_size))
                
                qr_x = width - qr_size - padding
                qr_y = height - qr_size - padding
                img.paste(qr_img, (qr_x, qr_y))
                
            return img
            
        finally:
            # Восстановление оригинальной конфигурации
            if preset:
                self.config = old_config

    def _create_base_image(self) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
        """Создать пустое изображение стикера."""
        width, height = self._get_sticker_size()
        bg_color = self._get('sticker.background_color', '#FFFFFF')
        
        img = Image.new('RGB', (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        if self._get('sticker.border', False):
            border_w = max(1, self.dpi // 300)
            draw.rectangle([(0, 0), (width - 1, height - 1)], outline='black', width=border_w)
            
        return img, draw

    def save(self, image: Image.Image, path: Union[str, Path]) -> None:
        """Сохранить изображение в файл."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        image.save(path, 'PNG')
