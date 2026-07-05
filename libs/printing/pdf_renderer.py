# --- libs/printing/pdf_renderer.py ---
import logging
from pathlib import Path
from typing import List
from PIL import Image
from libs.domain_models import Product
from libs.printing.sticker_generator import StickerGenerator
logger = logging.getLogger(__name__)
class PdfStickerRenderer:
    def __init__(self):
        self._generator = None
    def render(self, products: List[Product], preset: dict, output_path: Path) -> Path:
        logger.info(f"[PdfStickerRenderer] Рендер {len(products)} стикеров в {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self._generator = StickerGenerator(preset)
        images = []
        for i, product in enumerate(products):
            try:
                article = product.article or ""
                name = product.name or ""
                address = ""
                if hasattr(product, 'storage_locations') and product.storage_locations:
                    address = product.storage_locations[0] if isinstance(product.storage_locations, list) else str(product.storage_locations)
                elif hasattr(product, 'address') and product.address:
                    address = product.address
                pil_img = self._generator.generate(article=article, name=name, address=address)
                images.append(pil_img)
                logger.debug(f"[PdfStickerRenderer] Стикер {i+1}/{len(products)} отрендерен: {article}")
            except Exception as e:
                logger.error(f"[PdfStickerRenderer] Ошибка рендера стикера {i+1}: {e}", exc_info=True)
                blank = Image.new('RGB', (400, 300), color='white')
                images.append(blank)
        if not images:
            raise ValueError("Нет стикеров для рендера")
        if len(images) == 1:
            images[0].save(output_path, 'PDF', resolution=300.0)
        else:
            images[0].save(output_path, 'PDF', save_all=True, append_images=images[1:], resolution=300.0)
        logger.info(f"[PdfStickerRenderer] PDF создан: {output_path} ({len(images)} страниц)")
        return output_path