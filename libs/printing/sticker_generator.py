# --- sticker_generator.py ---
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
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
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.dpi = self._get('sticker.dpi', 300)
        self.mm_to_inch = 1 / 25.4
        self.font_cache: Dict[str, ImageFont.FreeTypeFont] = {}
        self.available_fonts = self._find_fonts()
    def _get(self, key_path: str, default: Any = None) -> Any:
        if isinstance(self.config, dict):
            value, keys = self.config, key_path.split('.')
            try:
                for key in keys: value = value[key]
                return value
            except (KeyError, TypeError): return default
        return default
    def _find_fonts(self) -> Dict[str, str]:
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
            if Path(path).exists(): fonts[f"{family}_{style}"] = path
        if not fonts: fonts['default'] = None
        return fonts
    def _get_font(self, size_pt: int, bold: bool = False, italic: bool = False, font_family: Optional[str] = None) -> ImageFont.FreeTypeFont:
        font_family = (font_family or self._get('fonts.default_font', 'Arial')).lower()
        style = ('b' if bold else '') + ('i' if italic else '') or 'n'
        size_px = int(size_pt * self.dpi / 72)
        key = f"{font_family}_{style}_{size_px}"
        if key in self.font_cache: return self.font_cache[key]
        font_path = None
        for font_key, path in self.available_fonts.items():
            if font_key.startswith(f"{font_family}_{style}"): font_path = path; break
        if not font_path:
            for font_key, path in self.available_fonts.items():
                if font_key.startswith(f"{font_family}_"): font_path = path; break
        if not font_path and self.available_fonts: font_path = next(iter(self.available_fonts.values()))
        try: font = ImageFont.truetype(font_path, size_px) if font_path else ImageFont.load_default()
        except Exception: font = ImageFont.load_default()
        self.font_cache[key] = font
        return font
    def _mm_to_pixels(self, mm: float) -> int:
        return int(mm * self.mm_to_inch * self.dpi)
    def _get_sticker_size(self) -> Tuple[int, int]:
        width_mm = self._get('sticker.width_mm', 40)
        height_mm = self._get('sticker.height_mm', 20)
        if self._get('sticker.orientation') == 'landscape': width_mm, height_mm = height_mm, width_mm
        return self._mm_to_pixels(width_mm), self._mm_to_pixels(height_mm)
    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            if bbox[2] <= max_width: current_line.append(word)
            else:
                if current_line: lines.append(' '.join(current_line))
                if font.getbbox(word)[2] > max_width: lines.append(word); current_line = []
                else: current_line = [word]
        if current_line: lines.append(' '.join(current_line))
        return lines
    def generate(self, article: str, name: str, address: Optional[str] = None, quantity: Optional[Union[int, float]] = None, unit: str = "шт", barcode_type: str = "code128", preset: Optional[Dict[str, Any]] = None) -> Image.Image:
        old_config = self.config.copy() if self.config else {}
        if preset: self.config.update(preset)
        try:
            image, draw = self._create_base_image()
            width, height = image.size
            clean_article = str(article).strip()
            if '/' in clean_article: clean_article = clean_article.split('/')[0].strip()
            article_cfg = self._get('article', {}); name_cfg = self._get('name', {}); address_cfg = self._get('address', {}); barcode_cfg = self._get('barcode', {})
            padding = 5
            y_cursor = padding
            if article_cfg.get('enabled', True):
                article_font = self._get_font(article_cfg.get('size', 8), bold=article_cfg.get('bold', True))
                article_text = clean_article
                text_width = article_font.getbbox(article_text)[2]
                align = article_cfg.get('align', 'left')
                if align == 'center': article_x = (width - text_width) // 2
                elif align == 'right': article_x = width - text_width - padding
                else: article_x = padding
                article_x += article_cfg.get('offset_x', 0); article_y = padding + article_cfg.get('offset_y', 0)
                draw.text((article_x, article_y), article_text, fill='black', font=article_font)
                y_cursor = article_y + int(article_cfg.get('size', 8) * self.dpi / 72) + 2
            if name_cfg.get('enabled', True):
                name_font = self._get_font(name_cfg.get('size', 6), bold=name_cfg.get('bold', False), italic=name_cfg.get('italic', False))
                max_text_width = width - (2 * padding)
                lines = self._wrap_text(name, name_font, max_text_width)[:name_cfg.get('max_lines', 5)]
                for line in lines:
                    if y_cursor >= height - 20: break
                    line_width = name_font.getbbox(line)[2]
                    align = name_cfg.get('align', 'left')
                    if align == 'center': line_x = (width - line_width) // 2
                    elif align == 'right': line_x = width - line_width - padding
                    else: line_x = padding
                    line_x += name_cfg.get('offset_x', 0); line_y = y_cursor + name_cfg.get('offset_y', 0)
                    draw.text((line_x, line_y), line, fill='black', font=name_font)
                    y_cursor += int(name_cfg.get('size', 6) * self.dpi / 72) + 1
            if address and address_cfg.get('enabled', False):
                address_font = self._get_font(address_cfg.get('size', 6), bold=address_cfg.get('bold', False), italic=address_cfg.get('italic', False))
                address_text = f"{address}"
                text_width = address_font.getbbox(address_text)[2]
                align = address_cfg.get('align', 'right')
                if align == 'center': address_x = (width - text_width) // 2
                elif align == 'left': address_x = padding
                else: address_x = width - text_width - padding
                address_x += address_cfg.get('offset_x', 0); address_y = height - address_cfg.get('size', 6) - padding + address_cfg.get('offset_y', 0)
                text_color = address_cfg.get('text_color', '#808080')
                bg_color = address_cfg.get('bg_color', 'transparent')
                if text_color and str(text_color).lower() in ('transparent', 'none', ''):
                    text_color = self._get('sticker.background_color', '#FFFFFF')
                    if text_color.lower() in ('#ffffff', 'white', '#fff'):
                        text_color = '#000000'
                if bg_color and str(bg_color).lower() not in ('transparent', 'none', ''):
                    text_bbox = address_font.getbbox(address_text)
                    t_width = text_bbox[2] - text_bbox[0]
                    t_height = text_bbox[3] - text_bbox[1]
                    pad_x, pad_y = 2, 1
                    pad_y_bottom = max(2, int(t_height * 0.4))
                    draw.rectangle(
                        [address_x - pad_x, address_y - pad_y, address_x + t_width + pad_x, address_y + t_height + pad_y_bottom],
                        fill=bg_color
                    )
                draw.text((address_x, address_y), address_text, fill=text_color, font=address_font)
            show_barcode = barcode_cfg.get('enabled', True) and self._get('layout.show_barcode', True)
            show_qr = barcode_cfg.get('type') == 'qr' or self._get('layout.show_qr', False)
            barcode_position = barcode_cfg.get('position', 'top_right')
            barcode_offset_x = barcode_cfg.get('offset_x', 0)
            barcode_offset_y = barcode_cfg.get('offset_y', 0)
            if show_barcode and not show_qr:
                code128_width_mm = barcode_cfg.get('code128_width_mm', 36)
                code128_height_mm = barcode_cfg.get('code128_height_mm', 6)
                barcode_height = self._mm_to_pixels(code128_height_mm)
                try:
                    digits = ''.join(filter(str.isdigit, clean_article))
                    if barcode_type == 'ean13' and len(digits) >= 12: code = EAN13(digits[:13], writer=ImageWriter())
                    else: code = Code128(clean_article, writer=ImageWriter())
                    buffer = BytesIO()
                    code.write(buffer, options={'module_width': 0.2, 'module_height': code128_height_mm, 'write_text': False})
                    barcode_image = Image.open(buffer)
                    target_width = self._mm_to_pixels(code128_width_mm)
                    if barcode_image.width != target_width:
                        ratio = target_width / barcode_image.width
                        barcode_image = barcode_image.resize((target_width, int(barcode_image.height * ratio)), Image.Resampling.LANCZOS)
                    if 'right' in barcode_position: barcode_x = width - barcode_image.width - padding
                    elif 'left' in barcode_position: barcode_x = padding
                    else: barcode_x = (width - barcode_image.width) // 2
                    if 'top' in barcode_position: barcode_y = padding
                    elif 'bottom' in barcode_position: barcode_y = height - barcode_image.height - padding
                    else: barcode_y = height - barcode_image.height - padding
                    barcode_x += barcode_offset_x; barcode_y += barcode_offset_y
                    image.paste(barcode_image, (barcode_x, barcode_y))
                    if barcode_cfg.get('show_text', False):
                        text_size = barcode_cfg.get('text_size', 4)
                        text_font = self._get_font(text_size)
                        text_scale_x = barcode_cfg.get('text_scale_x', 1.0)
                        text_scale_y = barcode_cfg.get('text_scale_y', 1.0)
                        text_offset_x = barcode_cfg.get('text_offset_x', 0)
                        text_offset_y = barcode_cfg.get('text_offset_y', 0)
                        text_bbox = text_font.getbbox(clean_article)
                        text_width = int((text_bbox[2] - text_bbox[0]) * text_scale_x)
                        text_height = int((text_bbox[3] - text_bbox[1]) * text_scale_y)
                        text_x = barcode_x + (barcode_image.width - text_width) // 2 + text_offset_x
                        text_y = barcode_y + barcode_image.height + 2 + text_offset_y
                        if text_scale_x != 1.0 or text_scale_y != 1.0:
                            text_image = Image.new('RGBA', (text_width, text_height), (255, 255, 255, 0))
                            text_draw = ImageDraw.Draw(text_image)
                            text_draw.text((0, 0), clean_article, fill='black', font=text_font)
                            text_image = text_image.resize((text_width, text_height), Image.Resampling.LANCZOS)
                            image.paste(text_image, (text_x, text_y), text_image)
                        else:
                            draw.text((text_x, text_y), clean_article, fill='black', font=text_font)
                except Exception as barcode_error:
                    logger.error(f"Barcode generation failed: {barcode_error}", exc_info=True)
                    draw.text((padding, height - 15), "[Barcode Error]", fill='red', font=self._get_font(6))
            if show_qr:
                qr_size_mm = barcode_cfg.get('qr_size_mm', 16)
                qr_size = self._mm_to_pixels(qr_size_mm)
                qr_code = qrcode.QRCode(version=1, box_size=10, border=2)
                qr_code.add_data(clean_article)
                qr_code.make(fit=True)
                qr_image = qr_code.make_image(fill_color="black", back_color="white").resize((qr_size, qr_size))
                if 'right' in barcode_position: qr_x = width - qr_size - padding
                elif 'left' in barcode_position: qr_x = padding
                else: qr_x = (width - qr_size) // 2
                if 'top' in barcode_position: qr_y = padding
                elif 'bottom' in barcode_position: qr_y = height - qr_size - padding
                else: qr_y = height - qr_size - padding
                qr_x += barcode_offset_x; qr_y += barcode_offset_y
                image.paste(qr_image, (qr_x, qr_y))
            return image
        finally:
            if preset: self.config = old_config
    def _create_base_image(self) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
        width, height = self._get_sticker_size()
        bg_color = self._get('sticker.background_color', '#FFFFFF')
        img = Image.new('RGB', (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)
        if self._get('sticker.border', False):
            border_w = max(1, self.dpi // 300)
            draw.rectangle([(0, 0), (width - 1, height - 1)], outline='black', width=border_w)
        return img, draw
    def save(self, image: Image.Image, path: Union[str, Path]) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        image.save(path, 'PNG')