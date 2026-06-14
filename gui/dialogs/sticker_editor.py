import logging
import customtkinter as ctk
from typing import Any, Optional
from services.interfaces import ISettingsService
from libs.domain_models import Product
from libs.printing.sticker_generator import StickerGenerator
from PIL import Image
logger = logging.getLogger(__name__)
class MiniSpinbox(ctk.CTkFrame):
    def __init__(self, master, from_=0, to=100, width=60, command=None, **kwargs):
        super().__init__(master, **kwargs)
        self._min, self._max, self._command = from_, to, command
        self.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(self, text="−", width=24, command=self._dec).grid(row=0, column=0, padx=1)
        self._entry = ctk.CTkEntry(self, width=width, justify="center")
        self._entry.grid(row=0, column=1, padx=1)
        self._entry.bind("<KeyRelease>", lambda e: self._fire()) # Фикс: реакция на ввод с клавиатуры
        ctk.CTkButton(self, text="+", width=24, command=self._inc).grid(row=0, column=2, padx=1)
        self.set(from_)
    def _inc(self):
        try: v = int(self._entry.get()) + 1
        except: v = self._min
        self.set(min(v, self._max)); self._fire()
    def _dec(self):
        try: v = int(self._entry.get()) - 1
        except: v = self._max
        self.set(max(v, self._min)); self._fire()
    def _fire(self):
        if self._command: self._command()
    def get(self):
        try: return int(self._entry.get())
        except: return 0
    def set(self, v): 
        self._entry.delete(0, "end"); self._entry.insert(0, str(v))
class StickerEditor(ctk.CTkToplevel):
    FIELDS = {
        "📏 Размеры": [
            {"label": "Ширина (мм)", "key": "width_mm", "type": "spin", "min": 10, "max": 200, "default": 60},
            {"label": "Высота (мм)", "key": "height_mm", "type": "spin", "min": 10, "max": 200, "default": 40},
            {"label": "Ориентация", "key": "orientation", "type": "combo", "values": ["portrait", "landscape"], "default": "portrait"},
            {"label": "Цвет фона", "key": "background_color", "type": "entry", "default": "#FFFFFF"},
            {"label": "Рамка", "key": "border", "type": "check", "default": False}
        ],
        "🔤 Артикул": [
            {"label": "Включить", "key": "article_enabled", "type": "check", "default": True},
            {"label": "Размер шрифта", "key": "article_size", "type": "spin", "min": 2, "max": 72, "default": 8},
            {"label": "Выравнивание", "key": "article_align", "type": "combo", "values": ["left", "center", "right"], "default": "left"},
            {"label": "Жирный", "key": "article_bold", "type": "check", "default": True},
            {"label": "Цвет", "key": "article_color", "type": "entry", "default": "#000000"},
            {"label": "Смещение X / Y", "key": "article_offset_x", "key2": "article_offset_y", "type": "pair_spin", "min": -500, "max": 500, "default": 0, "default2": 0}
        ],
        "📝 Название": [
            {"label": "Включить", "key": "name_enabled", "type": "check", "default": True},
            {"label": "Размер шрифта", "key": "name_size", "type": "spin", "min": 2, "max": 72, "default": 6},
            {"label": "Выравнивание", "key": "name_align", "type": "combo", "values": ["left", "center", "right"], "default": "left"},
            {"label": "Макс. строк", "key": "name_max_lines", "type": "spin", "min": 0, "max": 20, "default": 5},
            {"label": "Жирный / Курсив", "key": "name_bold", "key2": "name_italic", "type": "dual_check", "default": False, "default2": False},
            {"label": "Цвет", "key": "name_color", "type": "entry", "default": "#000000"},
            {"label": "Смещение X / Y", "key": "name_offset_x", "key2": "name_offset_y", "type": "pair_spin", "min": -500, "max": 500, "default": 0, "default2": 0}
        ],
        "🔢 Количество": [
            {"label": "Включить", "key": "qty_enabled", "type": "check", "default": False},
            {"label": "Размер шрифта", "key": "qty_size", "type": "spin", "min": 2, "max": 72, "default": 6},
            {"label": "Выравнивание", "key": "qty_align", "type": "combo", "values": ["left", "center", "right"], "default": "right"},
            {"label": "Жирный / Курсив", "key": "qty_bold", "key2": "qty_italic", "type": "dual_check", "default": False, "default2": True},
            {"label": "Цвет", "key": "qty_color", "type": "entry", "default": "#666666"},
            {"label": "Смещение X / Y", "key": "qty_offset_x", "key2": "qty_offset_y", "type": "pair_spin", "min": -500, "max": 500, "default": 0, "default2": 0}
        ],
        "🏢 Адрес": [
            {"label": "Включить", "key": "address_enabled", "type": "check", "default": False},
            {"label": "Размер шрифта", "key": "address_size", "type": "spin", "min": 2, "max": 72, "default": 6},
            {"label": "Выравнивание", "key": "address_align", "type": "combo", "values": ["left", "center", "right"], "default": "right"},
            {"label": "Жирный / Курсив", "key": "address_bold", "key2": "address_italic", "type": "dual_check", "default": False, "default2": False},
            {"label": "Цвет / Фон", "key": "address_color", "key2": "address_bg_color", "type": "dual_entry", "default": "#606060", "default2": "#FFFFFF"},
            {"label": "Рамка", "key": "address_border", "type": "check", "default": False},
            {"label": "Смещение X / Y", "key": "address_offset_x", "key2": "address_offset_y", "type": "pair_spin", "min": -500, "max": 500, "default": 0, "default2": 0}
        ],
        "Коды": [
            {"label": "Включить", "key": "barcode_enabled", "type": "check", "default": True},
            {"label": "Тип", "key": "barcode_type", "type": "combo", "values": ["auto", "code128", "qr", "none"], "default": "auto"},
            {"label": "Позиция", "key": "barcode_position", "type": "combo", "values": ["top_right", "top_left", "bottom_right", "bottom_left", "right", "left", "top", "bottom"], "default": "top_right"},
            {"label": "Размер QR (мм)", "key": "barcode_size_mm", "type": "spin", "min": 4, "max": 100, "default": 16},
            {"label": "Code128 Ш / В (мм)", "key": "code128_width_mm", "key2": "code128_height_mm", "type": "pair_spin_wrap", "min": 2, "max": 128, "default": 36, "min2": 2, "max2": 64, "default2": 6},
            {"label": "Текст под кодом", "key": "barcode_show_text", "type": "check", "default": False},
            {"label": "Размер текста", "key": "barcode_text_size", "type": "spin", "min": 2, "max": 72, "default": 4},
            {"label": "Смещение кода X / Y", "key": "barcode_offset_x", "key2": "barcode_offset_y", "type": "pair_spin_wrap", "min": -500, "max": 500, "default": 0, "default2": 0},
            {"label": "Смещение текста X / Y", "key": "barcode_text_offset_x", "key2": "barcode_text_offset_y", "type": "pair_spin_wrap", "min": -500, "max": 500, "default": 0, "default2": 0},
            {"label": "Масштаб текста X / Y", "key": "barcode_text_scale_x", "key2": "barcode_text_scale_y", "type": "pair_spin_wrap", "min": 0.1, "max": 3.0, "default": 1.0, "min2": 0.1, "max2": 3.0, "default2": 1.0},
            {"label": "QR если Code128 невозможен", "key": "fallback_qr", "type": "check", "default": True},
            {"label": "Пропускать если невозможно", "key": "skip_invalid", "type": "check", "default": False}
        ]
    }
    def __init__(self, master: Any, settings_service: ISettingsService, product: Optional[Product] = None):
        super().__init__(master)
        self._settings_service = settings_service
        self._product = product
        self.title("⚙ Редактор пресетов")
        self.geometry("1100x585")
        self.resizable(True, True)
        self.transient(master)
        self._presets = self._settings_service.get_setting('sticker_presets', {})
        self._current_name = self._settings_service.get_setting('current_preset_name', 'default')
        self._current_preset = self._presets.get(self._current_name, {})
        self._widgets = {}
        self._ctk_image = None
        self._preview_update_scheduled = False
        self._create_ui()
        self._show_group(list(self.FIELDS.keys())[0])
        self._update_preview()
    def _create_ui(self):
        self.grid_columnconfigure(0, weight=1, minsize=180)
        self.grid_columnconfigure(1, weight=4)
        self.grid_columnconfigure(2, weight=2)
        self.grid_rowconfigure(0, weight=1)
        left = ctk.CTkFrame(self)
        left.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(left, text="Пресеты", font=ctk.CTkFont(weight="bold")).pack(pady=(5, 2))
        self._preset_list = ctk.CTkComboBox(left, values=list(self._presets.keys()), command=self._on_select)
        self._preset_list.pack(fill="x", padx=5, pady=2)
        self._preset_list.set(self._current_name)
        btn_frame = ctk.CTkFrame(left, fg_color="transparent")
        btn_frame.pack(fill="x", padx=5, pady=2)
        ctk.CTkButton(btn_frame, text="+", width=30, command=self._add).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="−", width=30, fg_color="#808080", command=self._del).pack(side="left", padx=2)
        ctk.CTkFrame(left, height=2, fg_color=("gray50", "gray50")).pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(left, text="Группы", font=ctk.CTkFont(weight="bold")).pack(pady=(0, 2))
        self._nav_btns = {}
        for group in self.FIELDS.keys():
            btn = ctk.CTkButton(left, text=group, fg_color=("gray60", "gray40"), hover_color=("gray50", "gray30"), 
                                text_color=("black", "white"), anchor="w", command=lambda g=group: self._show_group(g))
            btn.pack(fill="x", padx=5, pady=1)
            self._nav_btns[group] = btn
        self._right_frame = ctk.CTkScrollableFrame(self)
        self._right_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=5, pady=5)
        preview_container = ctk.CTkFrame(self)
        preview_container.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=5, pady=5)
        preview_container.grid_rowconfigure(0, weight=1)
        preview_container.grid_columnconfigure(0, weight=1)
        self._preview_frame = ctk.CTkFrame(preview_container, fg_color=("gray90", "gray20"))
        self._preview_frame.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)
        self._preview_frame.grid_rowconfigure(0, weight=1)
        self._preview_frame.grid_columnconfigure(0, weight=1)
        self._preview_label = ctk.CTkLabel(self._preview_frame, text="Нет данных", text_color="gray")
        self._preview_label.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.grid(row=2, column=0, columnspan=3, sticky="e", padx=10, pady=10)
        ctk.CTkButton(bottom, text="Сброс", fg_color="#808080", command=self._reset).pack(side="right", padx=5)
        ctk.CTkButton(bottom, text="Отмена", fg_color="#808080", command=self.destroy).pack(side="right", padx=5)
        ctk.CTkButton(bottom, text="Сохранить", command=self._save).pack(side="right", padx=5)
    def _show_group(self, group: str):
        for btn in self._nav_btns.values(): btn.configure(fg_color=("gray60", "gray40"))
        self._nav_btns[group].configure(fg_color=("gray40", "gray60"))
        for w in self._right_frame.winfo_children(): w.destroy()
        self._widgets = {}
        for row, item in enumerate(self.FIELDS[group]):
            ctk.CTkLabel(self._right_frame, text=item["label"]).grid(row=row, column=0, padx=5, pady=3, sticky="w")
            self._render_widget(self._right_frame, row, item)
    def _schedule_preview_update(self):
        if not self._preview_update_scheduled:
            self._preview_update_scheduled = True
            self.after(300, self._debounced_preview_update)
    def _debounced_preview_update(self):
        self._preview_update_scheduled = False
        self._update_preview()
    def _update_preview(self):
        try:
            preset = self._collect_current_preset()
            article = self._product.article if self._product else "TEST-001"
            name = self._product.name if self._product else "Тестовый товар для превью"
            pil_img = StickerGenerator(preset).generate(article=article, name=name)
            fw, fh = self._preview_frame.winfo_width(), self._preview_frame.winfo_height()
            if fw > 10 and fh > 10:
                pil_img = pil_img.copy()
                pil_img.thumbnail((fw-20, fh-20), Image.Resampling.LANCZOS)
            self._ctk_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
            self._preview_label.configure(image=self._ctk_image, text="")
        except Exception as e:
            logger.warning(f"Preview update failed: {e}")
            self._preview_label.configure(image=None, text=f"Ошибка: {str(e)[:40]}")
    def _collect_current_preset(self):
        preset = dict(self._current_preset)
        for group in self.FIELDS.values():
            for item in group:
                key, dtype = item["key"], item["type"]
                w = self._widgets.get(key)
                if not w: continue
                if dtype in ("spin", "pair_spin", "pair_spin_wrap"): preset[key] = w.get()
                elif dtype == "combo": preset[key] = w.get()
                elif dtype == "check": preset[key] = bool(w.get())
                elif dtype == "entry": preset[key] = w.get()
                elif dtype == "dual_check": preset[key] = bool(w.get())
                elif dtype == "dual_entry": preset[key] = w.get()
                if "key2" in item:
                    k2, w2 = item["key2"], self._widgets.get(item["key2"])
                    if w2:
                        if dtype in ("pair_spin", "pair_spin_wrap"): preset[k2] = w2.get()
                        elif dtype == "dual_check": preset[k2] = bool(w2.get())
                        else: preset[k2] = w2.get()
        return preset
    def _update_preset_value(self, key: str, value: Any):
        self._current_preset[key] = value
        self._schedule_preview_update()
    def _render_widget(self, parent, row, item):
        key, dtype, default = item["key"], item["type"], item["default"]
        val = self._current_preset.get(key, default)
        def make_callback(k):
            def cb(v=None):
                w = self._widgets.get(k)
                if w:
                    if isinstance(w, MiniSpinbox): val = w.get()
                    elif isinstance(w, ctk.CTkComboBox): val = w.get()
                    elif isinstance(w, ctk.CTkCheckBox): val = bool(w.get())
                    elif isinstance(w, ctk.CTkEntry): val = w.get()
                    self._update_preset_value(k, val)
            return cb
        if dtype == "spin":
            w = MiniSpinbox(parent, from_=item["min"], to=item["max"], width=70, command=make_callback(key))
            w.grid(row=row, column=1, padx=5, pady=3, sticky="w"); w.set(val); self._widgets[key] = w
        elif dtype == "combo":
            w = ctk.CTkComboBox(parent, values=item["values"], width=120, command=make_callback(key))
            w.grid(row=row, column=1, padx=5, pady=3, sticky="w"); w.set(str(val)); self._widgets[key] = w
        elif dtype == "check":
            w = ctk.CTkCheckBox(parent, text="", command=make_callback(key))
            w.grid(row=row, column=1, padx=5, pady=3, sticky="w")
            if val: w.select(); self._widgets[key] = w
        elif dtype == "entry":
            w = ctk.CTkEntry(parent, width=100)
            w.grid(row=row, column=1, padx=5, pady=3, sticky="w"); w.insert(0, str(val)); self._widgets[key] = w
            w.bind("<KeyRelease>", lambda e, k=key: self._update_preset_value(k, self._widgets[k].get()))
        elif dtype in ("pair_spin", "pair_spin_wrap", "dual_check", "dual_entry"):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.grid(row=row, column=1, columnspan=2, padx=5, pady=3, sticky="w")
            if dtype == "pair_spin_wrap":
                f.grid_columnconfigure(0, weight=1)
                w1 = MiniSpinbox(f, from_=item["min"], to=item["max"], width=60, command=make_callback(key))
                w1.grid(row=0, column=0, sticky="w", padx=(0, 5))
                w1.set(self._current_preset.get(key, default))
                self._widgets[key] = w1
                k2 = item["key2"]
                val2 = self._current_preset.get(k2, item["default2"])
                w2 = MiniSpinbox(f, from_=item.get("min2", item["min"]), to=item.get("max2", item["max"]), width=60, command=make_callback(k2))
                w2.grid(row=1, column=0, sticky="w", padx=(0, 5))
                w2.set(val2)
                self._widgets[k2] = w2
            else:
                if dtype == "pair_spin":
                    w1 = MiniSpinbox(f, from_=item["min"], to=item["max"], width=60, command=make_callback(key))
                    w1.set(self._current_preset.get(key, default))
                elif dtype == "dual_check":
                    w1 = ctk.CTkCheckBox(f, text="", command=make_callback(key))
                    if self._current_preset.get(key, default): w1.select()
                else:
                    w1 = ctk.CTkEntry(f, width=80)
                    w1.insert(0, str(val))
                    w1.bind("<KeyRelease>", lambda e, k=key: self._update_preset_value(k, self._widgets[k].get()))
                w1.pack(side="left", padx=(0, 5))
                self._widgets[key] = w1
                k2 = item["key2"]
                val2 = self._current_preset.get(k2, item["default2"])
                if dtype == "pair_spin":
                    w2 = MiniSpinbox(f, from_=item.get("min2", item["min"]), to=item.get("max2", item["max"]), width=60, command=make_callback(k2))
                    w2.set(val2)
                elif dtype == "dual_check":
                    w2 = ctk.CTkCheckBox(f, text="", command=make_callback(k2))
                    if val2: w2.select()
                else:
                    w2 = ctk.CTkEntry(f, width=80)
                    w2.insert(0, str(val2))
                    w2.bind("<KeyRelease>", lambda e, k=k2: self._update_preset_value(k, self._widgets[k].get()))
                w2.pack(side="left")
                self._widgets[k2] = w2
    def _on_select(self, choice: str): 
        self._load_preset(choice)
    def _load_preset(self, name: str):
        self._current_name = name
        saved = self._presets.get(name, {})
        self._current_preset = {}
        for group in self.FIELDS.values():
            for item in group:
                self._current_preset[item["key"]] = item["default"]
                if "key2" in item:
                    self._current_preset[item["key2"]] = item.get("default2", item["default"])
        self._current_preset.update(saved)
        self._preset_list.set(name)
        self._show_group(list(self.FIELDS.keys())[0])
        self._update_preview()
    def _add(self):
        name = f"preset_{len(self._presets) + 1}"
        self._presets[name] = {"name": name}
        self._preset_list.configure(values=list(self._presets.keys()))
        self._load_preset(name)
    def _del(self):
        if len(self._presets) <= 1: return
        del self._presets[self._current_name]
        self._preset_list.configure(values=list(self._presets.keys()))
        self._load_preset(next(iter(self._presets)))
    def _save(self):
        preset = self._collect_current_preset()
        self._presets[self._current_name] = preset
        self._settings_service.set_setting('sticker_presets', self._presets)
        self._settings_service.set_setting('current_preset_name', self._current_name)
        self.destroy()
    def _reset(self):
        self._load_preset(self._current_name)