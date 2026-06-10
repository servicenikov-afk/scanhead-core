import logging, os
from typing import Any, Optional
import customtkinter as ctk
from PIL import Image
from services.interfaces import IPrinterService, ISettingsService
from libs.domain_models import Product
from gui.dialogs.sticker_editor import StickerEditor
from libs.printing.sticker_generator import StickerGenerator

logger = logging.getLogger(__name__)

class StickerPreview(ctk.CTkFrame):
    def __init__(self, master: Any, printer_service: IPrinterService, settings_service: ISettingsService):
        super().__init__(master)
        self._printer_service, self._settings_service = printer_service, settings_service
        self._current_product: Optional[Product] = None
        self._ctk_image: Optional[ctk.CTkImage] = None
        self._icon_settings = self._load_icon("settings32.png", (20, 20))
        self._init_presets()
        self._create_ui()

    def _load_icon(self, filename: str, size: tuple) -> Optional[ctk.CTkImage]:
        try:
            path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "icons", filename)
            if os.path.exists(path):
                img = Image.open(path)
                return ctk.CTkImage(light_image=img, dark_image=img, size=size)
        except Exception as e:
            logger.warning(f"Icon load failed {filename}: {e}")
        return None

    def _init_presets(self):
        if not self._settings_service.get_setting('sticker_presets'):
            default = {'name': 'Стандарт (60x40)', 'width_mm': 60, 'height_mm': 40, 'barcode_type': 'CODE128', 'font_size': 12}
            self._settings_service.set_setting('sticker_presets', {'default': default})
            self._settings_service.set_setting('current_preset_name', 'default')

    def _create_ui(self):
        self.configure(fg_color="transparent")
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        
        self._preset_combo = ctk.CTkComboBox(top, values=self._get_preset_names(), command=self._on_preset_change)
        self._preset_combo.set(self._settings_service.get_setting('current_preset_name', 'default'))
        self._preset_combo.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        btn_settings = ctk.CTkButton(top, text="", image=self._icon_settings, width=32, command=self._open_editor)
        btn_settings.pack(side="right")
        
        self._preview_frame = ctk.CTkFrame(self)
        self._preview_frame.grid(row=1, column=0, sticky="nsew", padx=3, pady=3)
        self._preview_frame.grid_rowconfigure(0, weight=1)
        self._preview_frame.grid_columnconfigure(0, weight=1)
        
        self._preview_label = ctk.CTkLabel(self._preview_frame, text="Нет данных", text_color="gray")
        self._preview_label.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)

    def _get_preset_names(self):
        presets = self._settings_service.get_setting('sticker_presets', {})
        return list(presets.keys()) if presets else ['default']

    def _on_preset_change(self, choice: str):
        self._settings_service.set_setting('current_preset_name', choice)
        self._generate_preview()

    def _open_editor(self):
        self._editor = StickerEditor(self, self._settings_service, product=self._current_product)
        self._editor.grab_set()
        self._editor.bind("<Destroy>", lambda e: self._on_editor_close())

    def _on_editor_close(self):
        self._preset_combo.configure(values=self._get_preset_names())
        current = self._settings_service.get_setting('current_preset_name', 'default')
        if current in self._get_preset_names():
            self._preset_combo.set(current)
        self._generate_preview()

    def set_product(self, product: Optional[Product]):
        self._current_product = product
        self._generate_preview()

    def clear(self):
        self.set_product(None)

    def _generate_preview(self):
        if not self._current_product:
            self._preview_label.configure(image=None, text="Нет данных")
            return
        try:
            preset_name = self._settings_service.get_setting('current_preset_name', 'default')
            preset = self._settings_service.get_setting('sticker_presets', {}).get(preset_name, {})
            
            article = self._current_product.article or ""
            name = self._current_product.name or ""
            pil_img = StickerGenerator(preset).generate(article=article, name=name)
            
            lw, lh = self._preview_frame.winfo_width(), self._preview_frame.winfo_height()
            if lw > 1 and lh > 1:
                pil_img.thumbnail((lw-20, lh-20), Image.Resampling.LANCZOS)
            
            self._ctk_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
            self._preview_label.configure(image=self._ctk_image, text="")
        except Exception as e:
            logger.error(f"Preview generation failed: {e}")
            self._preview_label.configure(image=None, text=f"Ошибка: {e}")