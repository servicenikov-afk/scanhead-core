import os
from typing import Optional
from barcode import EAN13, Code128
from barcode.writer import ImageWriter
import qrcode

class BarcodeGenerator:
    """Генерация изображений штрих-кодов и QR-кодов."""

    def __init__(self, output_dir: str = "./barcodes"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_ean13(self, code: str, filename: Optional[str] = None) -> str:
        """Генерация EAN-13. Код должен быть 12 или 13 цифр."""
        # Если 13 цифр, отрезаем последнюю для библиотеки (она сама посчитает)
        clean_code = code[:12] if len(code) >= 12 else code.zfill(12)
        
        ean = EAN13(clean_code, writer=ImageWriter())
        name = filename or f"ean_{clean_code}"
        path = os.path.join(self.output_dir, name)
        return ean.save(path)

    def generate_code128(self, code: str, filename: Optional[str] = None) -> str:
        """Генерация Code-128."""
        code128 = Code128(code, writer=ImageWriter())
        name = filename or f"code128_{code}"
        path = os.path.join(self.output_dir, name)
        return code128.save(path)

    def generate_qr(self, data: str, filename: Optional[str] = None) -> str:
        """
        Генерация QR-кода.
        FIX: Обработка слэшей и спецсимволов теперь корректна, 
        так как данные передаются в библиотеку как есть, без обрезки.
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        name = filename or f"qr_{hash(data)}"
        # Убеждаемся, что расширение .png
        if not name.endswith(".png"):
            name += ".png"
            
        path = os.path.join(self.output_dir, name)
        img.save(path)
        return path