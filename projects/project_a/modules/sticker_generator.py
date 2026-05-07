# modules/sticker_generator.py
from PIL import Image, ImageDraw, ImageFont
import qrcode, barcode, logging
from barcode.writer import ImageWriter
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, Union
from io import BytesIO

logger = logging.getLogger(__name__)

class StickerGenerator:
    def __init__(self, config: Union[Dict[str, Any], Any]):
        self.config = config
        self.dpi = self._get('sticker.dpi', 300)
        self.mm_to_inch = 1 / 25.4
        self.font_cache = {}
        self.available_fonts = self._find_fonts()
    
    def _get(self, key_path: str, default: Any = None) -> Any:
        if hasattr(self.config, 'get'): return self.config.get(key_path, default)
        if isinstance(self.config, dict):
            v, ks = self.config, key_path.split('.')
            try:
                for k in ks: v = v[k]
                return v
            except: return default
        return default
    
    def _find_fonts(self) -> Dict[str, str]:
        fonts, wf = {}, "C:\\Windows\\Fonts"
        for fn, fam, sty in [("arial.ttf","arial","n"),("arialbd.ttf","arial","b"),("ariali.ttf","arial","i"),("arialbi.ttf","arial","bi"),
                             ("calibri.ttf","calibri","n"),("calibrib.ttf","calibri","b"),("calibrii.ttf","calibri","i"),("calibriz.ttf","calibri","bi"),
                             ("tahoma.ttf","tahoma","n"),("tahomabd.ttf","tahoma","b"),("verdana.ttf","verdana","n"),
                             ("verdanab.ttf","verdana","b"),("verdanai.ttf","verdana","i"),("verdanaz.ttf","verdana","bi")]:
            p = f"{wf}\\{fn}"
            if Path(p).exists(): fonts[f"{fam}_{sty}"] = p
        if not fonts: fonts['default'] = None
        return fonts
    
    def _get_font(self, size_pt: int, bold=False, italic=False, font_family=None) -> ImageFont.FreeTypeFont:
        ff = (font_family or self._get('fonts.default_font','Arial')).lower()
        sty = ('b' if bold else '') + ('i' if italic else '') or 'n'
        sz = int(size_pt * self.dpi / 72); key = f"{ff}_{sty}_{sz}"
        if key in self.font_cache: return self.font_cache[key]
        fp = None
        for k,p in self.available_fonts.items():
            if k.startswith(f"{ff}_{sty}"): fp = p; break
        if not fp:
            for k,p in self.available_fonts.items():
                if k.startswith(f"{ff}_"): fp = p; break
        if not fp and self.available_fonts: fp = next(iter(self.available_fonts.values()))
        try: font = ImageFont.truetype(fp, sz) if fp else ImageFont.load_default()
        except: font = ImageFont.load_default()
        self.font_cache[key] = font
        return font
    
    def _normalize_article(self, a: str) -> str:
        return str(a).strip().split('/')[0].strip() if a and '/' in a else str(a).strip()
    
    def _mm_to_pixels(self, mm: float) -> int: return int(mm * self.mm_to_inch * self.dpi)
    def _get_sticker_size(self) -> Tuple[int, int]:
        w,h = self._get('sticker.width_mm',40), self._get('sticker.height_mm',20)
        if self._get('sticker.orientation')=='landscape': w,h = h,w
        return self._mm_to_pixels(w), self._mm_to_pixels(h)
    
    def _create_base_image(self) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
        w,h = self._get_sticker_size()
        img = Image.new('RGB', (w,h), color=self._get('sticker.background_color','#FFFFFF'))
        draw = ImageDraw.Draw(img)
        if self._get('sticker.border',False):
            draw.rectangle([(0,0),(w-1,h-1)], outline='black', width=max(1,self.dpi//300))
        return img, draw
    
    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list:
        words, lines, cur = text.split(), [], []
        for w in words:
            if font.getbbox(' '.join(cur+[w]))[2] <= max_w: cur.append(w)
            else:
                if cur: lines.append(' '.join(cur))
                if font.getbbox(w)[2] > max_w:
                    lines.extend(w[i:i+10] for i in range(0,len(w),10)); cur = []
                else: cur = [w]
        if cur: lines.append(' '.join(cur))
        return lines
    
    def _add_text(self, draw, text, font, color, pos, align='left', max_w=None, border=False, bg=None) -> int:
        if not text: return 0
        lines = self._wrap_text(text, font, max_w) if max_w else [text]
        lh = font.getbbox("A")[3] - font.getbbox("A")[1]
        x,y = pos
        ws = [font.getbbox(l)[2] for l in lines]
        mw = max(ws) if ws else 0
        if align=='center': rx = x - mw//2
        elif align=='right': rx = x - mw
        else: rx = x
        if bg and bg!='#FFFFFF':
            p=2; th = len(lines)*int(lh*1.2)
            draw.rectangle([(rx-p,y-p),(rx+mw+p,y+th+p)], fill=bg)
        cy = y
        for i,l in enumerate(lines):
            w = ws[i]
            tx = x - (w//2 if align=='center' else w if align=='right' else 0)
            draw.text((tx,cy), l, fill=color, font=font)
            cy += int(lh*1.2)
        if border:
            th = len(lines)*int(lh*1.2); bw = max(1,self.dpi//300)
            draw.rectangle([(rx-2,y-2),(rx+mw+2,y+th+2)], outline='black', width=bw)
        return cy - y
    
    def _add_barcode(self, img, draw, article):
        if not article or not self._get('barcode.enabled',True): return
        article = self._normalize_article(article)
        bt = self._get('barcode.type','auto')
        if bt=='auto':
            try:
                from barcode_checker import BarcodeChecker
                bt = BarcodeChecker().get_recommended_barcode_type(article, self._get('barcode',{}))
            except: bt = 'qr' if len(article)>50 else 'code128'
        if bt in ('none',None): return
        iw,ih = img.size; pad = self._mm_to_pixels(1)
        off_x, off_y = self._get('barcode.offset_x',0), self._get('barcode.offset_y',0)
        toff_x, toff_y = self._get('barcode.text_offset_x',0), self._get('barcode.text_offset_y',0)
        try:
            if bt=='code128':
                cw = self._mm_to_pixels(self._get('barcode.code128_width_mm',25))
                ch = self._mm_to_pixels(self._get('barcode.code128_height_mm',10))
                writer = ImageWriter()
                writer.set_options({'module_height':2,'module_width':0.2,'quiet_zone':0.2,'font_size':0,'write_text':False,'background':'white'})
                code = barcode.get('code128', article, writer=writer)
                buf = BytesIO()
                code.write(buf, {'module_height':5,'module_width':0.2,'quiet_zone':1,'font_size':0,'write_text':False})
                buf.seek(0)
                code_img = Image.open(buf).convert('RGB').resize((cw,ch), Image.Resampling.LANCZOS)
                nw,nh = cw,ch
                pos_map = {'top_right':(iw-nw-pad,pad), 'top_left':(pad,pad), 'bottom_right':(iw-nw-pad,ih-nh-pad), 'bottom_left':(pad,ih-nh-pad),
                          'right':(iw-nw-pad,(ih-nh)//2), 'left':(pad,(ih-nh)//2), 'top':((iw-nw)//2,pad), 'bottom':((iw-nw)//2,ih-nh-pad)}
                x,y = pos_map.get(self._get('barcode.position','top_right'), (pad,pad))
                x += off_x; y += off_y
                img.paste(code_img, (x,y))
                if self._get('barcode.border',False):
                    bw = max(1,self.dpi//300); draw.rectangle([(x-bw,y-bw),(x+nw+bw-1,y+nh+bw-1)], outline='black', width=bw)
                if self._get('barcode.show_text',False):
                    ts = self._get('barcode.text_size',4)
                    scale_x = self._get('barcode.text_scale_x', 1.0)
                    scale_y = self._get('barcode.text_scale_y', 1.0)
                    
                    font = None
                    for p in ["C:\\Windows\\Fonts\\arial.ttf","C:\\Windows\\Fonts\\tahoma.ttf"]:
                        if Path(p).exists():
                            try:
                                font = ImageFont.truetype(p, int(ts*self.dpi/72))
                                break
                            except: continue
                    if not font: font = ImageFont.load_default()
                    
                    # Получаем размеры текста
                    td = ImageDraw.Draw(Image.new('RGB',(1,1)))
                    bb = td.textbbox((0,0), article, font=font)
                    tw, th = bb[2]-bb[0], bb[3]-bb[1]
                    bo = bb[1]
                    
                    # Применяем масштабирование
                    tw_scaled = int(tw * scale_x)
                    th_scaled = int(th * scale_y)
                    
                    # Создаем изображение с текстом
                    vp = 1
                    timg = Image.new('RGB', (tw_scaled, th_scaled + 2*vp), 'white')
                    tdraw = ImageDraw.Draw(timg)
                    
                    # Масштабируем сам текст через resize (проще всего)
                    text_img = Image.new('RGB', (tw, th), 'white')
                    text_draw = ImageDraw.Draw(text_img)
                    text_draw.text((0, -bo), article, fill='black', font=font)
                    
                    if scale_x != 1.0 or scale_y != 1.0:
                        text_img = text_img.resize((tw_scaled, th_scaled), Image.Resampling.LANCZOS)
                    
                    timg.paste(text_img, (0, vp))
                    
                    tx = x + (nw - tw_scaled)//2 + toff_x
                    ty = y + nh + 2 + toff_y
                    img.paste(timg, (tx,ty))
            elif bt=='qr':
                sz = self._mm_to_pixels(self._get('barcode.size_mm',10))
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=1)
                qr.add_data(article); qr.make(fit=True)
                code_img = qr.make_image(fill_color="black", back_color="white").resize((sz,sz), Image.Resampling.LANCZOS)
                pos_map = {'top_right':(iw-sz-pad,pad), 'top_left':(pad,pad), 'bottom_right':(iw-sz-pad,ih-sz-pad), 'bottom_left':(pad,ih-sz-pad),
                          'right':(iw-sz-pad,(ih-sz)//2), 'left':(pad,(ih-sz)//2), 'top':((iw-sz)//2,pad), 'bottom':((iw-sz)//2,ih-sz-pad)}
                x,y = pos_map.get(self._get('barcode.position','top_right'), (pad,pad))
                x += off_x; y += off_y
                img.paste(code_img, (x,y))
                if self._get('barcode.border',False):
                    bw = max(1,self.dpi//300); draw.rectangle([(x-bw,y-bw),(x+sz+bw-1,y+sz+bw-1)], outline='black', width=bw)
        except Exception as e: logger.error(f"Ошибка {bt}: {e}")
    
    def generate_preview(self, article, name, quantity=None, unit=None, address=None) -> Image.Image:
        try:
            img,draw = self._create_base_image()
            w,h = img.size; pad = self._mm_to_pixels(2); cw = w-2*pad; y = pad
            if self._get('elements.article.enabled',True):
                f = self._get_font(self._get('elements.article.font_size',8), bold=self._get('elements.article.bold',True),
                                   font_family=self._get('elements.article.font_family','Arial'))
                x = {'center':w//2+self._get('elements.article.offset_x',0), 'right':w-pad+self._get('elements.article.offset_x',0),
                     'left':pad+self._get('elements.article.offset_x',0)}.get(self._get('elements.article.align','center'),pad)
                hh = self._add_text(draw, article, f, self._get('elements.article.color','#000000'),
                                    (x, y+self._get('elements.article.offset_y',0)), self._get('elements.article.align','center'), cw)
                if hh: y += hh + pad
            if self._get('elements.name.enabled',True):
                nt = name
                ml = self._get('elements.name.max_lines',3)
                if ml>0 and len(name)>ml*30: nt = name[:ml*30]+"..."
                f = self._get_font(self._get('elements.name.font_size',6), bold=self._get('elements.name.bold',False),
                                   italic=self._get('elements.name.italic',False), font_family=self._get('elements.name.font_family','Arial'))
                x = {'center':w//2+self._get('elements.name.offset_x',0), 'right':w-pad+self._get('elements.name.offset_x',0),
                     'left':pad+self._get('elements.name.offset_x',0)}.get(self._get('elements.name.align','left'),pad)
                hh = self._add_text(draw, nt, f, self._get('elements.name.color','#000000'),
                                    (x, y+self._get('elements.name.offset_y',0)), self._get('elements.name.align','left'), cw)
                if hh: y += hh + pad
            if address and self._get('elements.address.enabled',False):
                f = self._get_font(self._get('elements.address.font_size',6), bold=self._get('elements.address.bold',False),
                                   italic=self._get('elements.address.italic',False), font_family=self._get('elements.address.font_family','Arial'))
                x = {'center':w//2+self._get('elements.address.offset_x',0), 'right':w-pad+self._get('elements.address.offset_x',0),
                     'left':pad+self._get('elements.address.offset_x',0)}.get(self._get('elements.address.align','right'),w-pad)
                ay = h-pad-self._mm_to_pixels(5)+self._get('elements.address.offset_y',0)
                self._add_text(draw, address, f, self._get('elements.address.color','#606060'), (x,ay),
                               self._get('elements.address.align','right'), cw//2,
                               border=self._get('elements.address.border',False), bg=self._get('elements.address.background_color','#FFFFFF'))
            if quantity and self._get('elements.quantity.enabled',False):
                qt = f"{quantity} {unit}" if unit else str(quantity)
                f = self._get_font(self._get('elements.quantity.font_size',6), bold=self._get('elements.quantity.bold',False),
                                   italic=self._get('elements.quantity.italic',True), font_family=self._get('elements.quantity.font_family','Arial'))
                x = {'center':w//2+self._get('elements.quantity.offset_x',0), 'right':w-pad+self._get('elements.quantity.offset_x',0),
                     'left':pad+self._get('elements.quantity.offset_x',0)}.get(self._get('elements.quantity.align','center'),w//2)
                qy = h-pad-self._mm_to_pixels(5)+self._get('elements.quantity.offset_y',0)
                self._add_text(draw, qt, f, self._get('elements.quantity.color','#666666'), (x,qy), self._get('elements.quantity.align','center'), cw)
            self._add_barcode(img, draw, article)
            return img
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            w,h = self._get_sticker_size()
            return Image.new('RGB', (w,h), color='white')
    
    def save_image(self, img: Image.Image, fp: Path) -> bool:
        try: fp.parent.mkdir(parents=True, exist_ok=True); img.save(fp, 'PNG', dpi=(self.dpi,self.dpi), quality=100); return True
        except: return False