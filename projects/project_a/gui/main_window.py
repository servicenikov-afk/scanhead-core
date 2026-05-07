# gui/main_window.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, colorchooser
import threading, queue, os, csv, traceback
from pathlib import Path
from PIL import Image, ImageTk
import pandas as pd
from config_manager import ConfigManager
from nomenclature import NomenclatureCSV
from sticker_generator import StickerGenerator
from barcode_checker import BarcodeChecker
from invoice_parser import InvoiceParser
from scrollable_frame import ScrollableFrame, VerticalScrollableFrame
from address_manager import AddressManager
import tempfile
import time

APPDATA_DIR = Path.home() / "AppData" / "Local" / "StickerMakerV3"
OUTPUT_DIR = Path.home() / "Desktop" / "Stickers"

class AccordionFrame(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.sections = {}
    def add_section(self, title, content_frame, initially_expanded=True):
        h = ttk.Frame(self); h.pack(fill=tk.X, pady=(5,0))
        arrow = tk.Label(h, text="▼" if initially_expanded else "▶", font=("Arial",8))
        arrow.pack(side=tk.LEFT, padx=(5,10))
        tk.Label(h, text=title, font=("Arial",8,"bold")).pack(side=tk.LEFT)
        ttk.Separator(h, orient='horizontal').pack(side=tk.BOTTOM, fill=tk.X, pady=(5,0))
        def toggle():
            if content_frame.winfo_viewable(): content_frame.pack_forget(); arrow.config(text="▶")
            else: content_frame.pack(fill=tk.X, pady=(5,0)); arrow.config(text="▼")
        for w in (arrow, h): w.bind("<Button-1>", lambda e: toggle())
        if initially_expanded: content_frame.pack(fill=tk.X, pady=(5,0))
        self.sections[title] = {'content': content_frame, 'arrow': arrow}

class PreviewDialog(tk.Toplevel):
    def __init__(self, parent, positions, generator, addr_mgr):
        super().__init__(parent)
        self.parent, self.positions, self.generator, self.addr_mgr = parent, positions, generator, addr_mgr
        for p in self.positions:
            if 'address' not in p:
                art = p.get('article_found') or p['article_source']
                p['address'] = addr_mgr.find_address(art) or ''
        self.result = None; self.title("Предпросмотр"); self.geometry("900x500")
        self.transient(parent); self.grab_set()
        f = ttk.Frame(self, padding=10); f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="Редактирование позиций", font=('Arial',10,'bold')).pack()
        frame = ttk.Frame(f); frame.pack(fill=tk.BOTH, expand=True, pady=5)
        vsb = ttk.Scrollbar(frame); vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree = ttk.Treeview(frame, columns=('sel','art','name','addr','qty','unit'), show='headings', yscrollcommand=vsb.set, height=15)
        self.tree.pack(fill=tk.BOTH, expand=True); vsb.config(command=self.tree.yview)
        cols = [('sel',40,'c'), ('art',120,'w'), ('name',350,'w'), ('addr',80,'c'), ('qty',70,'c'), ('unit',50,'c')]
        for c,w,a in cols: self.tree.heading(c, text=c.upper()); self.tree.column(c, width=w, anchor=a)
        self.tree.bind('<Double-1>', self.on_edit); self.tree.bind('<space>', self.toggle)
        self.select_vars = []
        for i,p in enumerate(positions):
            art = p.get('article_found') or p['article_source']
            addr = p.get('address', '')  # Берем из поля address
            var = tk.BooleanVar(value=True); self.select_vars.append(var)
            self.tree.insert('','end', values=('☑', art, p.get('name_found') or p['name_source'], addr, p.get('quantity',''), p.get('unit','шт')), tags=(str(i),))
        bf = ttk.Frame(f); bf.pack(fill=tk.X)
        for txt,cmd in [("💾 Сохранить",'save'), ("🖨️ Печать",'print'), ("💾🖨️ Сохр+печ",'save_print'), ("✕ Отмена",'cancel')]:
            ttk.Button(bf, text=txt, command=lambda c=cmd: self.close(c)).pack(side=tk.RIGHT, padx=2)
    def toggle(self, e=None):
        sel = self.tree.selection()
        if not sel: return
        item = sel[0]; vals = list(self.tree.item(item,'values'))
        idx = int(self.tree.item(item,'tags')[0])
        vals[0] = '☐' if vals[0]=='☑' else '☑'
        self.select_vars[idx].set(vals[0]=='☑')
        self.tree.item(item, values=vals)
    def on_edit(self, e):
        col = int(self.tree.identify_column(e.x)[1:])-1
        if col==0: self.toggle(); return
        item = self.tree.selection()[0]; vals = list(self.tree.item(item,'values'))
        x,y,w,h = self.tree.bbox(item, self.tree.identify_column(e.x))
        entry = ttk.Entry(self.tree); entry.place(x=x,y=y,width=w,height=h); entry.insert(0,vals[col]); entry.focus_set()
        def save(ev):
            new = entry.get(); vals[col]=new; self.tree.item(item,values=vals); entry.destroy()
            idx = int(self.tree.item(item,'tags')[0])
            if col==1: self.positions[idx]['article_found']=new
            elif col==2: self.positions[idx]['name_found']=new
            elif col==3: self.positions[idx]['address']=new
            elif col==4: self.positions[idx]['quantity']=new
            elif col==5: self.positions[idx]['unit']=new
        entry.bind('<Return>', save); entry.bind('<FocusOut>', lambda ev: entry.destroy())
    def get_selected(self):
        return [p for i,p in enumerate(self.positions) if self.select_vars[i].get()]
    def close(self, res):
        self.result = res; self.destroy()

class MainWindow:
    def __init__(self, root, config, nomenclature, generator, invoice_parser):
        self.root = root; self.config = config; self.nomenclature = nomenclature
        self.generator = generator; self.invoice_parser = invoice_parser
        self.address_manager = AddressManager(config)
        self.queue = queue.Queue()
        self.invoice_path = tk.StringVar(value=config.get('paths.last_invoice_path',''))
        self.output_folder = tk.StringVar(value=config.get('paths.last_output_folder', str(OUTPUT_DIR)))
        self.status_text = tk.StringVar(value="Готов к работе")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.width_var = tk.IntVar(value=config.get('sticker.width_mm',40))
        self.height_var = tk.IntVar(value=config.get('sticker.height_mm',20))
        self.orientation_var = tk.StringVar(value=config.get('sticker.orientation','portrait'))
        self.border_var = tk.BooleanVar(value=config.get('sticker.border',False))
        self.bg_color_var = tk.StringVar(value=config.get('sticker.background_color','#FFFFFF'))
        self.article_enabled_var = tk.BooleanVar(value=config.get('elements.article.enabled',True))
        self.article_size_var = tk.IntVar(value=config.get('elements.article.font_size',8))
        self.article_bold_var = tk.BooleanVar(value=config.get('elements.article.bold',True))
        self.article_align_var = tk.StringVar(value=config.get('elements.article.align','top'))
        self.article_color_var = tk.StringVar(value=config.get('elements.article.color','#000000'))
        self.article_offset_x_var = tk.IntVar(value=config.get('elements.article.offset_x',0))
        self.article_offset_y_var = tk.IntVar(value=config.get('elements.article.offset_y',0))
        self.name_enabled_var = tk.BooleanVar(value=config.get('elements.name.enabled',True))
        self.name_size_var = tk.IntVar(value=config.get('elements.name.font_size',6))
        self.name_bold_var = tk.BooleanVar(value=config.get('elements.name.bold',False))
        self.name_italic_var = tk.BooleanVar(value=config.get('elements.name.italic',False))
        self.name_align_var = tk.StringVar(value=config.get('elements.name.align','left'))
        self.name_color_var = tk.StringVar(value=config.get('elements.name.color','#000000'))
        self.name_max_lines_var = tk.IntVar(value=config.get('elements.name.max_lines',5))
        self.name_offset_x_var = tk.IntVar(value=config.get('elements.name.offset_x',0))
        self.name_offset_y_var = tk.IntVar(value=config.get('elements.name.offset_y',0))
        self.qty_enabled_var = tk.BooleanVar(value=config.get('elements.quantity.enabled',False))
        self.qty_size_var = tk.IntVar(value=config.get('elements.quantity.font_size',6))
        self.qty_bold_var = tk.BooleanVar(value=config.get('elements.quantity.bold',False))
        self.qty_italic_var = tk.BooleanVar(value=config.get('elements.quantity.italic',True))
        self.qty_align_var = tk.StringVar(value=config.get('elements.quantity.align','right'))
        self.qty_color_var = tk.StringVar(value=config.get('elements.quantity.color','#666666'))
        self.qty_offset_x_var = tk.IntVar(value=config.get('elements.quantity.offset_x',0))
        self.qty_offset_y_var = tk.IntVar(value=config.get('elements.quantity.offset_y',0))
        self.address_enabled_var = tk.BooleanVar(value=config.get('elements.address.enabled',False))
        self.address_size_var = tk.IntVar(value=config.get('elements.address.font_size',6))
        self.address_bold_var = tk.BooleanVar(value=config.get('elements.address.bold',False))
        self.address_italic_var = tk.BooleanVar(value=config.get('elements.address.italic',False))
        self.address_align_var = tk.StringVar(value=config.get('elements.address.align','right'))
        self.address_color_var = tk.StringVar(value=config.get('elements.address.color','#606060'))
        self.address_offset_x_var = tk.IntVar(value=config.get('elements.address.offset_x',0))
        self.address_offset_y_var = tk.IntVar(value=config.get('elements.address.offset_y',0))
        self.address_border_var = tk.BooleanVar(value=config.get('elements.address.border',False))
        self.address_bg_color_var = tk.StringVar(value=config.get('elements.address.background_color','#FFFFFF'))
        self.barcode_enabled_var = tk.BooleanVar(value=config.get('barcode.enabled',True))
        self.barcode_type_var = tk.StringVar(value=config.get('barcode.type','auto'))
        self.barcode_size_var = tk.IntVar(value=config.get('barcode.size_mm',16))
        self.barcode_position_var = tk.StringVar(value=config.get('barcode.position','top_right'))
        self.barcode_border_var = tk.BooleanVar(value=config.get('barcode.border',False))
        self.code128_width_var = tk.IntVar(value=config.get('barcode.code128_width_mm',36))
        self.code128_height_var = tk.IntVar(value=config.get('barcode.code128_height_mm',6))
        self.barcode_show_text_var = tk.BooleanVar(value=config.get('barcode.show_text',False))
        self.barcode_text_size_var = tk.IntVar(value=config.get('barcode.text_size',4))
        self.barcode_offset_x_var = tk.IntVar(value=config.get('barcode.offset_x',0))
        self.barcode_offset_y_var = tk.IntVar(value=config.get('barcode.offset_y',0))
        self.barcode_text_offset_x_var = tk.IntVar(value=config.get('barcode.text_offset_x',0))
        self.barcode_text_offset_y_var = tk.IntVar(value=config.get('barcode.text_offset_y',0))
        self.barcode_text_scale_x_var = tk.DoubleVar(value=config.get('barcode.text_scale_x', 1.0))
        self.barcode_text_scale_y_var = tk.DoubleVar(value=config.get('barcode.text_scale_y', 1.0))
        self.fallback_qr_var = tk.BooleanVar(value=config.get('barcode.auto_rules.fallback_to_qr',True))
        self.skip_invalid_var = tk.BooleanVar(value=config.get('barcode.auto_rules.skip_if_invalid',False))
        self.db_url_var = tk.StringVar(value=config.get('paths.database_url','https://partsd.hardserver.ru/data/zero_inventory.csv'))
        self.preview_article_var = tk.StringVar(value="560.0004.852")
        self.preview_name_var = tk.StringVar(value="Быстроразъем прямой D6 мм для к/м А400, А600, А800, А1000, S700, SB1200, FM series, Spectra S")
        self.preview_address_var = tk.StringVar(value="A0702")
        self.search_article_var = tk.StringVar()
        self.search_name_var = tk.StringVar()
        self.overwrite_var = tk.BooleanVar(value=config.get('behavior.overwrite_files',True))
        self.open_after_var = tk.BooleanVar(value=config.get('behavior.open_after_process',False))
        self.skip_errors_var = tk.BooleanVar(value=config.get('behavior.skip_errors',True))
        self.temp_files = []
        self.preview_image = None; self.preview_photo = None; self.big_preview_photo = None
        self.setup_window()
        self.presets={};self.current_preset=tk.StringVar();self.new_preset_name=tk.StringVar()
        self._load_presets()
        self.create_widgets()
        self.setup_style()
        self.check_queue(); self.check_database(); self.check_address_database()
        if not self.presets:self.save_preset("Базовый")
        self.root.after(500, self.update_preview)

    def setup_window(self):
        self.root.title("Sticker Maker v3.3"); self.root.geometry("1200x800"); self.root.minsize(800,600)
        try:
            icon_path = Path(__file__).parent.parent / "icon.ico"
            if icon_path.exists(): self.root.iconbitmap(str(icon_path))
        except: pass
        self.root.update_idletasks()
        w=self.root.winfo_width(); h=self.root.winfo_height()
        x=(self.root.winfo_screenwidth()//2)-(w//2); y=(self.root.winfo_screenheight()//2)-(h//2)
        self.root.geometry(f'{w}x{h}+{x}+{y}')
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind('<Key>', self.on_key)
    def setup_style(self):
        style = ttk.Style(); style.theme_use('clam')
        style.configure('Title.TLabel', font=('Arial',8,'bold'))
        style.configure('Section.TLabel', font=('Arial',6,'bold'))
        style.configure('Accent.TButton', font=('Arial',6,'bold'))
        style.configure("Custom.Horizontal.TProgressbar", background='#4CAF50', troughcolor='#e0e0e0')
        style.configure('Loaded.TCombobox', fieldbackground='#e8f5e8')

    def on_key(self, event):
        if event.state & 4:  # Ctrl нажат
            if event.keysym in ('c', 'C', 'ы', 'с'):
                self.copy_text()
            elif event.keysym in ('v', 'V', 'м', 'M'):
                self.paste_text()
            elif event.keysym in ('s', 'S', 'ы'):
                self.save_settings()
    
    def create_widgets(self):
        main = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        left = ttk.Frame(main); main.add(left, weight=1)
        right = ttk.Frame(main); main.add(right, weight=1)
        self.create_left_panel(left); self.create_right_panel(right)
        self.create_status_bar()

    def create_left_panel(self, parent):
        self.left_notebook = ttk.Notebook(parent)  # сохраняем ссылку
        self.left_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        f1 = ttk.Frame(self.left_notebook); self.create_process_tab(f1); self.left_notebook.add(f1, text="📄 Обработка")
        f2 = ScrollableFrame(self.left_notebook); self.create_settings_tab(f2); self.left_notebook.add(f2, text="⚙ Настройки")
        f3 = ttk.Frame(self.left_notebook); self.create_database_tab(f3); self.left_notebook.add(f3, text="🗃️ База данных")
        f4 = ttk.Frame(self.left_notebook); self.create_address_tab(f4); self.left_notebook.add(f4, text="🏢 Адреса")
        f5 = ttk.Frame(self.left_notebook); self.create_preview_tab(f5); self.left_notebook.add(f5, text="👁️ Предпросмотр")

    def create_settings_tab(self, scrollable_parent):
        f = scrollable_parent.scrollable_frame
        acc = AccordionFrame(f)
        acc.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 1. Размеры стикера
        sf = ttk.LabelFrame(f, text="📏 Размеры и ориентация", padding=10)
        sc = ttk.Frame(sf, padding=5)
        sc.pack(fill=tk.X)
        sg = ttk.Frame(sc)
        sg.pack(fill=tk.X)
        
        ttk.Label(sg, text="Ширина (мм):").grid(row=0, column=0, sticky=tk.W, padx=(0,5))
        ttk.Spinbox(sg, from_=1, to=1000, textvariable=self.width_var, width=8, 
                    command=self.on_settings_change).grid(row=0, column=1, sticky=tk.W, padx=(0,20))
        ttk.Label(sg, text="Высота (мм):").grid(row=0, column=2, sticky=tk.W, padx=(0,5))
        ttk.Spinbox(sg, from_=1, to=1000, textvariable=self.height_var, width=8, 
                    command=self.on_settings_change).grid(row=0, column=3, sticky=tk.W, padx=(0,20))
        ttk.Label(sg, text="Ориентация:").grid(row=0, column=4, sticky=tk.W, padx=(0,5))
        oc = ttk.Combobox(sg, textvariable=self.orientation_var, values=['portrait','landscape'], 
                          state='readonly', width=10)
        oc.grid(row=0, column=5, sticky=tk.W)
        oc.bind('<<ComboboxSelected>>', lambda e: self.on_settings_change())
        
        ttk.Label(sg, text="Цвет фона:").grid(row=1, column=0, sticky=tk.W, padx=(0,5), pady=(10,0))
        cf = ttk.Frame(sg)
        cf.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=(10,0))
        cp = tk.Frame(cf, width=20, height=20, bg=self.bg_color_var.get())
        cp.pack(side=tk.LEFT, padx=(0,5))
        ttk.Entry(cf, textvariable=self.bg_color_var, width=10).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(cf, text="...", command=lambda: self.choose_color(self.bg_color_var, cp)).pack(side=tk.LEFT)
        ttk.Checkbutton(sg, text="Рамка вокруг стикера", variable=self.border_var,
                       command=self.on_settings_change).grid(row=1, column=3, columnspan=3, sticky=tk.W, pady=(10,0))
        acc.add_section("Размеры", sf, True)
        
        # 2. Настройки артикула
        af = ttk.LabelFrame(f, text="🔤 Артикул", padding=10)
        ac = ttk.Frame(af, padding=5)
        ac.pack(fill=tk.X)
        ttk.Checkbutton(ac, text="Показывать артикул", variable=self.article_enabled_var,
                       command=self.on_settings_change).pack(anchor=tk.W)
        ag = ttk.Frame(ac)
        ag.pack(fill=tk.X, pady=(5,0))
        
        ttk.Label(ag, text="Размер:").grid(row=0, column=0, sticky=tk.W, padx=(20,5))
        ttk.Spinbox(ag, from_=2, to=128, textvariable=self.article_size_var, width=6,
                    command=self.on_settings_change).grid(row=0, column=1, sticky=tk.W, padx=(0,20))
        ttk.Label(ag, text="Выравнивание:").grid(row=0, column=2, sticky=tk.W, padx=(0,5))
        aac = ttk.Combobox(ag, textvariable=self.article_align_var, values=['left','center','right'],
                           state='readonly', width=10)
        aac.grid(row=0, column=3, sticky=tk.W, padx=(0,20))
        aac.bind('<<ComboboxSelected>>', lambda e: self.on_settings_change())
        ttk.Checkbutton(ag, text="Жирный", variable=self.article_bold_var,
                       command=self.on_settings_change).grid(row=0, column=4, sticky=tk.W)
        
        ttk.Label(ag, text="Цвет:").grid(row=1, column=0, sticky=tk.W, padx=(20,5), pady=(10,0))
        acf = ttk.Frame(ag)
        acf.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=(10,0))
        acp = tk.Frame(acf, width=20, height=20, bg=self.article_color_var.get())
        acp.pack(side=tk.LEFT, padx=(0,5))
        ttk.Entry(acf, textvariable=self.article_color_var, width=10).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(acf, text="...", command=lambda: self.choose_color(self.article_color_var, acp)).pack(side=tk.LEFT)
        
        of = ttk.Frame(ac)
        of.pack(fill=tk.X, pady=(10,0))
        ttk.Label(of, text="Смещение X:").pack(side=tk.LEFT, padx=(20,5))
        ttk.Spinbox(of, from_=-500, to=500, textvariable=self.article_offset_x_var, width=6,
                    command=self.on_settings_change).pack(side=tk.LEFT, padx=(0,20))
        ttk.Label(of, text="Смещение Y:").pack(side=tk.LEFT, padx=(0,5))
        ttk.Spinbox(of, from_=-500, to=500, textvariable=self.article_offset_y_var, width=6,
                    command=self.on_settings_change).pack(side=tk.LEFT)
        acc.add_section("Артикул", af, False)
        
        # 3. Настройки названия
        nf = ttk.LabelFrame(f, text="📝 Название", padding=10)
        nc = ttk.Frame(nf, padding=5)
        nc.pack(fill=tk.X)
        ttk.Checkbutton(nc, text="Показывать название", variable=self.name_enabled_var,
                       command=self.on_settings_change).pack(anchor=tk.W)
        ng1 = ttk.Frame(nc)
        ng1.pack(fill=tk.X, pady=(5,0))
        
        ttk.Label(ng1, text="Размер:").grid(row=0, column=0, sticky=tk.W, padx=(20,5))
        ttk.Spinbox(ng1, from_=2, to=128, textvariable=self.name_size_var, width=6,
                    command=self.on_settings_change).grid(row=0, column=1, sticky=tk.W, padx=(0,20))
        ttk.Label(ng1, text="Выравнивание:").grid(row=0, column=2, sticky=tk.W, padx=(0,5))
        nac = ttk.Combobox(ng1, textvariable=self.name_align_var, values=['left','center','right'],
                           state='readonly', width=10)
        nac.grid(row=0, column=3, sticky=tk.W, padx=(0,20))
        nac.bind('<<ComboboxSelected>>', lambda e: self.on_settings_change())
        ttk.Checkbutton(ng1, text="Жирный", variable=self.name_bold_var,
                       command=self.on_settings_change).grid(row=0, column=4, sticky=tk.W, padx=(0,10))
        ttk.Checkbutton(ng1, text="Курсив", variable=self.name_italic_var,
                       command=self.on_settings_change).grid(row=0, column=5, sticky=tk.W)
        
        ng2 = ttk.Frame(nc)
        ng2.pack(fill=tk.X, pady=(5,0))
        ttk.Label(ng2, text="Макс. строк:").grid(row=0, column=0, sticky=tk.W, padx=(20,5))
        ttk.Spinbox(ng2, from_=0, to=10, textvariable=self.name_max_lines_var, width=6,
                    command=self.on_settings_change).grid(row=0, column=1, sticky=tk.W, padx=(0,20))
        ttk.Label(ng2, text="(0 = без огр.)").grid(row=0, column=2, sticky=tk.W)
        
        ttk.Label(ng2, text="Цвет:").grid(row=1, column=0, sticky=tk.W, padx=(20,5), pady=(10,0))
        ncf = ttk.Frame(ng2)
        ncf.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=(10,0))
        ncp = tk.Frame(ncf, width=20, height=20, bg=self.name_color_var.get())
        ncp.pack(side=tk.LEFT, padx=(0,5))
        ttk.Entry(ncf, textvariable=self.name_color_var, width=10).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(ncf, text="...", command=lambda: self.choose_color(self.name_color_var, ncp)).pack(side=tk.LEFT)
        
        of2 = ttk.Frame(nc)
        of2.pack(fill=tk.X, pady=(10,0))
        ttk.Label(of2, text="Смещение X:").pack(side=tk.LEFT, padx=(20,5))
        ttk.Spinbox(of2, from_=-500, to=500, textvariable=self.name_offset_x_var, width=6,
                    command=self.on_settings_change).pack(side=tk.LEFT, padx=(0,20))
        ttk.Label(of2, text="Смещение Y:").pack(side=tk.LEFT, padx=(0,5))
        ttk.Spinbox(of2, from_=-500, to=500, textvariable=self.name_offset_y_var, width=6,
                    command=self.on_settings_change).pack(side=tk.LEFT)
        acc.add_section("Название", nf, False)
        
        # 4. Настройки количества
        qf = ttk.LabelFrame(f, text="🔢 Количество", padding=10)
        qc = ttk.Frame(qf, padding=5)
        qc.pack(fill=tk.X)
        ttk.Checkbutton(qc, text="Показывать количество", variable=self.qty_enabled_var,
                       command=self.on_settings_change).pack(anchor=tk.W)
        qg = ttk.Frame(qc)
        qg.pack(fill=tk.X, pady=(5,0))
        
        ttk.Label(qg, text="Размер:").grid(row=0, column=0, sticky=tk.W, padx=(20,5))
        ttk.Spinbox(qg, from_=2, to=128, textvariable=self.qty_size_var, width=6,
                    command=self.on_settings_change).grid(row=0, column=1, sticky=tk.W, padx=(0,20))
        ttk.Label(qg, text="Выравнивание:").grid(row=0, column=2, sticky=tk.W, padx=(0,5))
        qac = ttk.Combobox(qg, textvariable=self.qty_align_var, values=['left','center','right'],
                           state='readonly', width=10)
        qac.grid(row=0, column=3, sticky=tk.W, padx=(0,20))
        qac.bind('<<ComboboxSelected>>', lambda e: self.on_settings_change())
        ttk.Checkbutton(qg, text="Жирный", variable=self.qty_bold_var,
                       command=self.on_settings_change).grid(row=0, column=4, sticky=tk.W, padx=(0,10))
        ttk.Checkbutton(qg, text="Курсив", variable=self.qty_italic_var,
                       command=self.on_settings_change).grid(row=0, column=5, sticky=tk.W)
        
        ttk.Label(qg, text="Цвет:").grid(row=1, column=0, sticky=tk.W, padx=(20,5), pady=(10,0))
        qcf = ttk.Frame(qg)
        qcf.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=(10,0))
        qcp = tk.Frame(qcf, width=20, height=20, bg=self.qty_color_var.get())
        qcp.pack(side=tk.LEFT, padx=(0,5))
        ttk.Entry(qcf, textvariable=self.qty_color_var, width=10).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(qcf, text="...", command=lambda: self.choose_color(self.qty_color_var, qcp)).pack(side=tk.LEFT)
        
        of3 = ttk.Frame(qc)
        of3.pack(fill=tk.X, pady=(10,0))
        ttk.Label(of3, text="Смещение X:").pack(side=tk.LEFT, padx=(20,5))
        ttk.Spinbox(of3, from_=-500, to=500, textvariable=self.qty_offset_x_var, width=6,
                    command=self.on_settings_change).pack(side=tk.LEFT, padx=(0,20))
        ttk.Label(of3, text="Смещение Y:").pack(side=tk.LEFT, padx=(0,5))
        ttk.Spinbox(of3, from_=-500, to=500, textvariable=self.qty_offset_y_var, width=6,
                    command=self.on_settings_change).pack(side=tk.LEFT)
        acc.add_section("Количество", qf, False)
        
        # 5. Настройки адреса
        adf = ttk.LabelFrame(f, text="🏢 Адрес хранения", padding=10)
        adc = ttk.Frame(adf, padding=5)
        adc.pack(fill=tk.X)
        ttk.Checkbutton(adc, text="Показывать адрес", variable=self.address_enabled_var,
                       command=self.on_settings_change).pack(anchor=tk.W)
        adg = ttk.Frame(adc)
        adg.pack(fill=tk.X, pady=(5,0))
        
        ttk.Label(adg, text="Размер:").grid(row=0, column=0, sticky=tk.W, padx=(20,5))
        ttk.Spinbox(adg, from_=2, to=128, textvariable=self.address_size_var, width=6,
                    command=self.on_settings_change).grid(row=0, column=1, sticky=tk.W, padx=(0,20))
        ttk.Label(adg, text="Выравнивание:").grid(row=0, column=2, sticky=tk.W, padx=(0,5))
        adac = ttk.Combobox(adg, textvariable=self.address_align_var, values=['left','center','right'],
                            state='readonly', width=10)
        adac.grid(row=0, column=3, sticky=tk.W, padx=(0,20))
        adac.bind('<<ComboboxSelected>>', lambda e: self.on_settings_change())
        ttk.Checkbutton(adg, text="Жирный", variable=self.address_bold_var,
                       command=self.on_settings_change).grid(row=0, column=4, sticky=tk.W, padx=(0,10))
        ttk.Checkbutton(adg, text="Курсив", variable=self.address_italic_var,
                       command=self.on_settings_change).grid(row=0, column=5, sticky=tk.W)
        
        ttk.Checkbutton(adg, text="Рамка вокруг адреса", variable=self.address_border_var,
                       command=self.on_settings_change).grid(row=1, column=0, columnspan=2, 
                                                             sticky=tk.W, padx=(20,0), pady=(10,0))
        
        ttk.Label(adg, text="Цвет:").grid(row=1, column=2, sticky=tk.W, padx=(20,5), pady=(10,0))
        adcf = ttk.Frame(adg)
        adcf.grid(row=1, column=3, columnspan=1, sticky=tk.W, pady=(10,0))
        adcp = tk.Frame(adcf, width=20, height=20, bg=self.address_color_var.get())
        adcp.pack(side=tk.LEFT, padx=(0,5))
        ttk.Entry(adcf, textvariable=self.address_color_var, width=10).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(adcf, text="...", command=lambda: self.choose_color(self.address_color_var, adcp)).pack(side=tk.LEFT)
        
        ttk.Label(adg, text="Цвет фона:").grid(row=2, column=0, sticky=tk.W, padx=(20,5), pady=(10,0))
        adbf = ttk.Frame(adg)
        adbf.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=(10,0))
        adbp = tk.Frame(adbf, width=20, height=20, bg=self.address_bg_color_var.get())
        adbp.pack(side=tk.LEFT, padx=(0,5))
        ttk.Entry(adbf, textvariable=self.address_bg_color_var, width=10).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(adbf, text="...", command=lambda: self.choose_color(self.address_bg_color_var, adbp)).pack(side=tk.LEFT)
        
        of4 = ttk.Frame(adc)
        of4.pack(fill=tk.X, pady=(10,0))
        ttk.Label(of4, text="Смещение X:").pack(side=tk.LEFT, padx=(20,5))
        ttk.Spinbox(of4, from_=-500, to=500, textvariable=self.address_offset_x_var, width=6,
                    command=self.on_settings_change).pack(side=tk.LEFT, padx=(0,20))
        ttk.Label(of4, text="Смещение Y:").pack(side=tk.LEFT, padx=(0,5))
        ttk.Spinbox(of4, from_=-500, to=500, textvariable=self.address_offset_y_var, width=6,
                    command=self.on_settings_change).pack(side=tk.LEFT)
        acc.add_section("Адрес", adf, False)
        
        # 6. Настройки кодов
        bf = ttk.LabelFrame(f, text="📊 Коды (QR/Штрих-код)", padding=10)
        bc = ttk.Frame(bf, padding=5)
        bc.pack(fill=tk.X)
        ttk.Checkbutton(bc, text="Показывать код", variable=self.barcode_enabled_var,
                       command=self.on_settings_change).pack(anchor=tk.W)
        bg1 = ttk.Frame(bc)
        bg1.pack(fill=tk.X, pady=(5,0))
        
        ttk.Label(bg1, text="Тип:").grid(row=0, column=0, sticky=tk.W, padx=(20,5))
        btc = ttk.Combobox(bg1, textvariable=self.barcode_type_var, values=['auto','code128','qr','none'],
                           state='readonly', width=12)
        btc.grid(row=0, column=1, sticky=tk.W, padx=(0,20))
        btc.bind('<<ComboboxSelected>>', lambda e: self.on_settings_change())
        
        ttk.Label(bg1, text="Размер QR (мм):").grid(row=0, column=2, sticky=tk.W, padx=(0,5))
        ttk.Spinbox(bg1, from_=4, to=100, textvariable=self.barcode_size_var, width=6,
                    command=self.on_settings_change).grid(row=0, column=3, sticky=tk.W, padx=(0,20))
        ttk.Checkbutton(bg1, text="Рамка кода", variable=self.barcode_border_var,
                       command=self.on_settings_change).grid(row=0, column=4, sticky=tk.W)
        
        bg2 = ttk.Frame(bc)
        bg2.pack(fill=tk.X, pady=(5,0))
        ttk.Label(bg2, text="Позиция:").grid(row=0, column=0, sticky=tk.W, padx=(20,5))
        bpc = ttk.Combobox(bg2, textvariable=self.barcode_position_var,
                           values=['top_right','top_left','bottom_right','bottom_left',
                                  'right','left','top','bottom'], state='readonly', width=12)
        bpc.grid(row=0, column=1, sticky=tk.W)
        bpc.bind('<<ComboboxSelected>>', lambda e: self.on_settings_change())
        
        of5 = ttk.Frame(bc)
        of5.pack(fill=tk.X, pady=(10,0))
        ttk.Label(of5, text="Смещение кода X:").pack(side=tk.LEFT, padx=(20,5))
        ttk.Spinbox(of5, from_=-500, to=500, textvariable=self.barcode_offset_x_var, width=6,
                    command=self.on_settings_change).pack(side=tk.LEFT, padx=(0,20))
        ttk.Label(of5, text="Y:").pack(side=tk.LEFT, padx=(0,5))
        ttk.Spinbox(of5, from_=-500, to=500, textvariable=self.barcode_offset_y_var, width=6,
                    command=self.on_settings_change).pack(side=tk.LEFT)
        
        cs = ttk.Frame(bc)
        cs.pack(fill=tk.X, pady=(5,0))
        ttk.Label(cs, text="Ширина Code128 (мм):").grid(row=0, column=0, sticky=tk.W, padx=(20,5))
        ttk.Spinbox(cs, from_=2, to=128, textvariable=self.code128_width_var, width=6,
                    command=self.on_barcode_settings_change).grid(row=0, column=1, sticky=tk.W, padx=(0,20))
        ttk.Label(cs, text="Высота Code128 (мм):").grid(row=0, column=2, sticky=tk.W, padx=(0,5))
        ttk.Spinbox(cs, from_=2, to=64, textvariable=self.code128_height_var, width=6,
                    command=self.on_barcode_settings_change).grid(row=0, column=3, sticky=tk.W)
        
        ttk.Checkbutton(bc, text="Показывать текст под штрих-кодом", variable=self.barcode_show_text_var,
                       command=self.on_barcode_settings_change).pack(anchor=tk.W, pady=(5,0))
        
        btf = ttk.Frame(bc)
        btf.pack(fill=tk.X, pady=(5,0))
        ttk.Label(btf, text="Размер шрифта текста:").grid(row=0, column=0, sticky=tk.W, padx=(20,5))
        ttk.Spinbox(btf, from_=2, to=100, textvariable=self.barcode_text_size_var, width=6,
                    command=self.on_barcode_settings_change).grid(row=0, column=1, sticky=tk.W)
        
        tof = ttk.Frame(bc)
        tof.pack(fill=tk.X, pady=(5,0))
        ttk.Label(tof, text="Смещение текста X:").pack(side=tk.LEFT, padx=(20,5))
        ttk.Spinbox(tof, from_=-500, to=500, textvariable=self.barcode_text_offset_x_var, width=6,
                    command=self.on_settings_change).pack(side=tk.LEFT, padx=(0,20))
        ttk.Label(tof, text="Y:").pack(side=tk.LEFT, padx=(0,5))
        ttk.Spinbox(tof, from_=-500, to=500, textvariable=self.barcode_text_offset_y_var, width=6,
                    command=self.on_settings_change).pack(side=tk.LEFT)
        
        scale_frame = ttk.Frame(bc)
        scale_frame.pack(fill=tk.X, pady=(5,0))
        ttk.Label(scale_frame, text="Масштаб X:").pack(side=tk.LEFT, padx=(20,5))
        ttk.Spinbox(scale_frame, from_=0.1, to=3.0, increment=0.1, 
                    textvariable=self.barcode_text_scale_x_var, width=6,
                    command=self.on_barcode_settings_change).pack(side=tk.LEFT, padx=(0,20))
        ttk.Label(scale_frame, text="Масштаб Y:").pack(side=tk.LEFT, padx=(0,5))
        ttk.Spinbox(scale_frame, from_=0.1, to=3.0, increment=0.1,
                    textvariable=self.barcode_text_scale_y_var, width=6,
                    command=self.on_barcode_settings_change).pack(side=tk.LEFT)
        
        rf = ttk.LabelFrame(bc, text="Автоправила", padding=10)
        rf.pack(fill=tk.X, pady=(10,0))
        ttk.Checkbutton(rf, text="QR если Code128 невозможен", variable=self.fallback_qr_var,
                       command=self.on_settings_change).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(rf, text="Пропускать если невозможно", variable=self.skip_invalid_var,
                       command=self.on_settings_change).pack(anchor=tk.W, pady=2)
        
        acc.add_section("Коды", bf, False)
        
        # Кнопки сохранения
        sv = ttk.Frame(f)
        sv.pack(fill=tk.X, pady=(15,0))
        ttk.Button(sv, text="💾 Сохранить", command=self.save_settings).pack(side=tk.LEFT)
        ttk.Button(sv, text="🔄 Сброс", command=self.reset_settings).pack(side=tk.LEFT, padx=(10,0))

    def create_address_tab(self, parent):
        f = ttk.Frame(parent, padding=5); f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="🏢 База адресов", style='Title.TLabel').pack(anchor=tk.W, pady=(0,5))
        sf = ttk.LabelFrame(f, text="Статус", padding=5); sf.pack(fill=tk.X, pady=(0,5))
        si = ttk.Frame(sf); si.pack(fill=tk.X)
        self.address_status_label = ttk.Label(si, text="Проверка..."); self.address_status_label.pack(side=tk.LEFT, padx=(0,20))
        self.address_stats_label = ttk.Label(si, text=""); self.address_stats_label.pack(side=tk.LEFT)
        imp = ttk.LabelFrame(f, text="Импорт", padding=5); imp.pack(fill=tk.X, pady=(0,5))
        ttk.Label(imp, text="Excel:").pack(anchor=tk.W)
        ff = ttk.Frame(imp); ff.pack(fill=tk.X, pady=2)
        self.address_file_var = tk.StringVar()
        ttk.Entry(ff, textvariable=self.address_file_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        ttk.Button(ff, text="📁", command=self.select_address_file).pack(side=tk.RIGHT)
        ib = ttk.Frame(imp); ib.pack(fill=tk.X, pady=2)
        ttk.Button(ib, text="🔍 Анализ", command=self.analyze_address_file).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(ib, text="⬆ Импорт", command=self.import_addresses).pack(side=tk.LEFT)
        self.analysis_text = scrolledtext.ScrolledText(imp, height=3, wrap=tk.WORD, font=('Consolas',9))
        self.analysis_text.pack(fill=tk.X)
        exp = ttk.LabelFrame(f, text="Экспорт", padding=5); exp.pack(fill=tk.X, pady=(5,5))
        eb = ttk.Frame(exp); eb.pack(fill=tk.X)
        ttk.Button(eb, text="📤 CSV", command=self.export_addresses_csv).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(eb, text="📤 Excel", command=self.export_addresses_excel).pack(side=tk.LEFT)
        sr = ttk.LabelFrame(f, text="Поиск", padding=5); sr.pack(fill=tk.X)
        sg = ttk.Frame(sr); sg.pack(fill=tk.X, pady=2)
        ttk.Label(sg, text="Артикул:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(sg, textvariable=self.search_article_var, width=20).grid(row=0, column=1, sticky=tk.W, padx=(0,20))
        ttk.Label(sg, text="Наименование:").grid(row=0, column=2, sticky=tk.W)
        ttk.Entry(sg, textvariable=self.search_name_var, width=30).grid(row=0, column=3, sticky=tk.W)
        ttk.Button(sg, text="🔍", command=self.search_address).grid(row=0, column=4, padx=(10,0))
        rc = ttk.Frame(sr); rc.pack(fill=tk.X, pady=2)
        ttk.Label(rc, text="Результат:", font=('Arial',8,'bold')).pack(side=tk.LEFT, padx=(0,10))
        self.search_result_label = ttk.Label(rc, text="", font=('Arial',9))
        self.search_result_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def create_process_tab(self, parent):
        f = ttk.Frame(parent, padding=10); f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="📄 Обработка", style='Title.TLabel').pack(anchor=tk.W, pady=(0,5))
        ff = ttk.LabelFrame(f, text="Файл", padding=5); ff.pack(fill=tk.X, pady=(0,5))
        ttk.Label(ff, text="Накладная:").pack(anchor=tk.W)
        inp = ttk.Frame(ff); inp.pack(fill=tk.X, pady=5)
        ttk.Entry(inp, textvariable=self.invoice_path).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        bf = ttk.Frame(inp); bf.pack(side=tk.RIGHT)
        ttk.Button(bf, text="📁", command=self.select_invoice_file).pack(side=tk.LEFT, padx=(0,2))
        ttk.Button(bf, text="🧪", command=self.test_invoice).pack(side=tk.LEFT, padx=(0,2))
        ttk.Button(bf, text="🗑️", command=self.clear_invoice).pack(side=tk.LEFT)
        of = ttk.LabelFrame(f, text="Сохранение", padding=5); of.pack(fill=tk.X, pady=(0,5))
        ttk.Label(of, text="Папка:").pack(anchor=tk.W)
        oi = ttk.Frame(of); oi.pack(fill=tk.X, pady=5)
        ttk.Entry(oi, textvariable=self.output_folder).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        ob = ttk.Frame(oi); ob.pack(side=tk.RIGHT)
        ttk.Button(ob, text="📁", command=self.select_output_folder).pack(side=tk.LEFT, padx=(0,2))
        ttk.Button(ob, text="📂", command=self.open_stickers_folder).pack(side=tk.LEFT)
        opt = ttk.LabelFrame(f, text="Опции", padding=5); opt.pack(fill=tk.X, pady=(0,5))
        og = ttk.Frame(opt); og.pack(fill=tk.X)
        ttk.Checkbutton(og, text="Перезапись", variable=self.overwrite_var).grid(row=0, column=0, sticky=tk.W, padx=(0,20))
        ttk.Checkbutton(og, text="Открыть папку", variable=self.open_after_var).grid(row=0, column=1, sticky=tk.W, padx=(0,20))
        ttk.Checkbutton(og, text="Пропуск ошибок", variable=self.skip_errors_var).grid(row=0, column=2, sticky=tk.W)
        pb = ttk.Frame(f); pb.pack(fill=tk.X, pady=(0,10))
        style = ttk.Style(); style.theme_use('clam')
        style.configure('Accent.TButton', font=('Arial',9,'bold'), foreground='white', background='#4CAF50', padding=(10,5))
        style.map('Accent.TButton', background=[('active','#45a049'), ('pressed','#3d8b40')])
        self.process_btn = ttk.Button(pb, text="🚀 Создать", command=self.process_invoice, style='Accent.TButton')
        self.process_btn.pack(side=tk.LEFT, padx=(0,10))
        ttk.Button(pb, text="💾 Лог", command=self.save_process_log).pack(side=tk.LEFT, padx=(0,10))
        ttk.Button(pb, text="❓", command=self.show_help).pack(side=tk.LEFT)
        pr = ttk.Frame(f); pr.pack(fill=tk.X, pady=(0,10))
        ttk.Label(pr, text="Прогресс:").pack(side=tk.LEFT, padx=(0,10))
        self.progress_bar = ttk.Progressbar(pr, variable=self.progress_var, maximum=100, length=300)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        lf = ttk.LabelFrame(f, text="Лог", padding=5); lf.pack(fill=tk.BOTH, expand=True)
        self.process_log = scrolledtext.ScrolledText(lf, height=8, wrap=tk.WORD, font=('Consolas',9))
        self.process_log.pack(fill=tk.BOTH, expand=True)
        for lvl,col in [('info','black'), ('success','darkgreen'), ('warning','darkorange'), ('error','darkred')]:
            self.process_log.tag_config(f"tag_{lvl}", foreground=col)

    def create_database_tab(self, parent):
        f = ttk.Frame(parent, padding=5); f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="🗃️ База CSV", style='Title.TLabel').pack(anchor=tk.W, pady=(0,5))
        sf = ttk.LabelFrame(f, text="Статус", padding=5); sf.pack(fill=tk.X, pady=(0,5))
        self.db_status_label = ttk.Label(sf, text="Проверка..."); self.db_status_label.pack(anchor=tk.W)
        self.db_stats_label = ttk.Label(sf, text=""); self.db_stats_label.pack(anchor=tk.W, pady=2)
        uf = ttk.LabelFrame(f, text="Обновление", padding=5); uf.pack(fill=tk.X, pady=(0,5))
        ttk.Label(uf, text="URL:").pack(anchor=tk.W)
        uf2 = ttk.Frame(uf); uf2.pack(fill=tk.X, pady=2)
        ttk.Entry(uf2, textvariable=self.db_url_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        ttk.Button(uf2, text="🔄", command=self.update_database).pack(side=tk.RIGHT)
        bf = ttk.Frame(uf); bf.pack(fill=tk.X, pady=2)
        ttk.Button(bf, text="📊 Стат", command=self.show_database_stats).pack(side=tk.LEFT, padx=(0,10))
        ttk.Button(bf, text="📂 Папка", command=self.open_settings_folder).pack(side=tk.LEFT, padx=(0,10))
        ttk.Button(bf, text="💾 Лог", command=self.save_log).pack(side=tk.LEFT)
        lf = ttk.LabelFrame(f, text="Лог БД", padding=5); lf.pack(fill=tk.BOTH, expand=True)
        self.db_log_text = scrolledtext.ScrolledText(lf, height=8, wrap=tk.WORD, font=('Consolas',9))
        self.db_log_text.pack(fill=tk.BOTH, expand=True)
        for lvl,col in [('info','black'), ('success','darkgreen'), ('warning','darkorange'), ('error','darkred')]:
            self.db_log_text.tag_config(f"db_tag_{lvl}", foreground=col)

    def create_right_panel(self, parent):
        nb = ttk.Notebook(parent); nb.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        f1 = ttk.Frame(nb); self.create_big_preview_tab(f1); nb.add(f1, text="👁️‍🗨️ Большой")
        f2 = ttk.Frame(nb); self.create_log_tab(f2); nb.add(f2, text="📋 Лог")

    def create_big_preview_tab(self, parent):
        f = ttk.Frame(parent, padding=5); f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="Большой предпросмотр", style='Title.TLabel').pack(anchor=tk.W, pady=(0,5))
        ctrl=ttk.Frame(f);ctrl.pack(fill=tk.X,pady=(0,5))
        ttk.Label(ctrl,text="Пресет:").pack(side=tk.LEFT)
        self.preset_combo=ttk.Combobox(ctrl,textvariable=self.current_preset,values=list(self.presets.keys()),
                                       state='readonly',width=20)
        self.preset_combo.pack(side=tk.LEFT,padx=5)
        self.preset_combo.bind('<<ComboboxSelected>>',lambda e:self.load_preset(self.current_preset.get()))
        ttk.Button(ctrl,text="💾",width=3,command=self.show_save_preset_dialog).pack(side=tk.LEFT,padx=2)
        ttk.Button(ctrl,text="🗑️",width=3,command=self.confirm_delete_preset).pack(side=tk.LEFT)
        ttk.Button(ctrl,text="⚙",width=3,command=lambda:self._select_tab(1)).pack(side=tk.LEFT,padx=(20,0))
        pc = ttk.Frame(f); pc.pack(fill=tk.BOTH, expand=True)
        self.big_preview_canvas = tk.Canvas(pc, bg='white', highlightthickness=1, highlightbackground='#ccc')
        self.big_preview_canvas.pack(fill=tk.BOTH, expand=True)

    def _select_tab(self,idx):self.left_notebook.select(idx)

    def show_save_preset_dialog(self):
        d=tk.Toplevel(self.root);d.title("Сохранить пресет");d.geometry("300x120");d.transient(self.root);d.grab_set()
        ttk.Label(d,text="Имя пресета:").pack(pady=5)
        e=ttk.Entry(d,textvariable=self.new_preset_name,width=30);e.pack(pady=5);e.focus()
        ttk.Button(d,text="Сохранить",command=lambda:[self.save_preset(self.new_preset_name.get()),d.destroy()]).pack(pady=5)

    def save_preset(self,name):
        if not name:return
        cfg={}
        for k,v in self._get_all_vars().items():
            try:cfg[k]=v.get()
            except:pass
        self.presets[name]=cfg
        self._save_presets()
        self.preset_combo['values']=list(self.presets.keys())
        self.new_preset_name.set("")
        self.log_message(f"Пресет '{name}' сохранён")

    def load_preset(self,name):
        if name not in self.presets:return
        for k,v in self.presets[name].items():
            if hasattr(self,f"{k}_var"):
                try:getattr(self,f"{k}_var").set(v)
                except:pass
        self.save_settings_to_config()
        self.update_preview()
        self.preset_combo.config(style='Loaded.TCombobox')
        self.root.after(1000, lambda: self.preset_combo.config(style='TCombobox'))
        self.log_message(f"✅ Пресет '{name}' загружен", "success")

    def confirm_delete_preset(self):
        if not self.current_preset.get():return
        if messagebox.askyesno("Удаление",f"Удалить '{self.current_preset.get()}'?"):
            del self.presets[self.current_preset.get()]
            self._save_presets()
            self.preset_combo['values']=list(self.presets.keys())
            self.current_preset.set(list(self.presets.keys())[0] if self.presets else "")
            self.log_message("Пресет удалён")

    def _get_all_vars(self):
        return {k.replace('_var',''):v for k,v in self.__dict__.items() if k.endswith('_var') and isinstance(v,(tk.BooleanVar,tk.IntVar,tk.StringVar))}

    def _save_presets(self):
        try:
            import json
            (APPDATA_DIR/"presets.json").write_text(json.dumps(self.presets,ensure_ascii=False),encoding='utf-8')
        except:pass

    def _load_presets(self):
        try:
            import json
            p=APPDATA_DIR/"presets.json"
            if p.exists():self.presets=json.loads(p.read_text(encoding='utf-8'))
        except:self.presets={}
    
    def create_log_tab(self, parent):
        f = ttk.Frame(parent, padding=5); f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="Лог приложения", style='Title.TLabel').pack(anchor=tk.W, pady=(0,5))
        self.log_text = scrolledtext.ScrolledText(f, wrap=tk.WORD, font=('Consolas',9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        for lvl,col in [('info','black'), ('success','darkgreen'), ('warning','darkorange'), ('error','darkred')]:
            self.log_text.tag_config(f"main_tag_{lvl}", foreground=col)

    def create_preview_tab(self, parent):
        f = ttk.Frame(parent, padding=5); f.pack(fill=tk.BOTH, expand=True)
        ttk.Label(f, text="Предпросмотр", style='Title.TLabel').pack(anchor=tk.W, pady=(0,5))
        c1 = ttk.Frame(f); c1.pack(fill=tk.X, pady=(0,5))
        ttk.Label(c1, text="Артикул:").pack(side=tk.LEFT)
        self.article_entry = ttk.Entry(c1, textvariable=self.preview_article_var, width=20)
        self.article_entry.pack(side=tk.LEFT, padx=(5,2))
        ttk.Button(c1, text="🔍", width=3, command=self.search_and_fill).pack(side=tk.LEFT, padx=(0,20))
        ttk.Label(c1, text="Название:").pack(side=tk.LEFT)
        self.name_entry = ttk.Entry(c1, textvariable=self.preview_name_var, width=30)
        self.name_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(c1, text="🔍", width=3, command=self.search_and_fill_name).pack(side=tk.LEFT)
        c2 = ttk.Frame(f); c2.pack(fill=tk.X, pady=(0,5))
        ttk.Label(c2, text="Адрес:").pack(side=tk.LEFT)
        self.addr_entry = ttk.Entry(c2, textvariable=self.preview_address_var, width=10)
        self.addr_entry.pack(side=tk.LEFT, padx=(5,2))
        ttk.Button(c2, text="🔍", width=3, command=self.search_and_fill_addr).pack(side=tk.LEFT, padx=(5,20))
        ttk.Button(c2, text="🔄", command=self.update_preview).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(c2, text="💾", command=self.save_single_sticker).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(c2, text="🖨️", command=self.print_preview).pack(side=tk.LEFT)
        self.barcode_info_label = ttk.Label(f, text=""); self.barcode_info_label.pack(anchor=tk.W)
        ps = VerticalScrollableFrame(f); ps.pack(fill=tk.BOTH, expand=True)
        self.preview_canvas = tk.Canvas(ps.scrollable_frame, bg='white', highlightthickness=1, highlightbackground='#ccc')
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        self.preview_info_label = ttk.Label(f, text=""); self.preview_info_label.pack(anchor=tk.W)

    def create_status_bar(self):
        sb = ttk.Frame(self.root, relief=tk.SUNKEN); sb.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Label(sb, textvariable=self.status_text).pack(side=tk.LEFT, padx=5)
        self.address_status_label = ttk.Label(sb, text=""); self.address_status_label.pack(side=tk.RIGHT, padx=5)
        ttk.Label(sb, text="|").pack(side=tk.RIGHT)
        self.db_status_label = ttk.Label(sb, text=""); self.db_status_label.pack(side=tk.RIGHT, padx=5)

    def on_settings_change(self): self.save_settings_to_config(); self.update_preview()
    def on_barcode_settings_change(self): self.save_settings_to_config(); self.update_preview()

    def choose_color(self, var, preview):
        c = colorchooser.askcolor(title="Выберите цвет", initialcolor=var.get())
        if c[1]: var.set(c[1]); preview.config(bg=c[1]); self.on_settings_change()

    def save_single_sticker(self):
        try:
            img = self.generator.generate_preview(self.preview_article_var.get(), self.preview_name_var.get(),
                                                 address=self.preview_address_var.get() if self.address_enabled_var.get() else None)
            fp = filedialog.asksaveasfilename(defaultextension=".png", initialfile=f"sticker_{self.preview_article_var.get()}.png",
                                             filetypes=[("PNG","*.png")])
            if fp and self.generator.save_image(img, Path(fp)):
                self.log_message(f"Сохранено: {fp}"); messagebox.showinfo("Успех", f"Сохранено:\n{fp}")
        except Exception as e: self.log_message(f"Ошибка: {e}", "error"); messagebox.showerror("Ошибка", str(e))

    def print_preview(self):
        if not self.preview_image: messagebox.showwarning("Внимание", "Создайте предпросмотр!"); return
        tf = APPDATA_DIR/"temp_print.png"; tf.parent.mkdir(parents=True, exist_ok=True)
        self.preview_image.save(tf, 'PNG', dpi=(300,300)); os.startfile(str(tf), "print")

    def update_preview(self):
        self.cleanup_temp_files()
        try:
            a=self.preview_article_var.get(); n=self.preview_name_var.get(); ad=self.preview_address_var.get() if self.address_enabled_var.get() else None
            img = self.generator.generate_preview(article=a, name=n, address=ad)
            if img.width<=0: return
            self.preview_image = img; photo = ImageTk.PhotoImage(img); self.preview_photo = photo
            if hasattr(self,'preview_canvas'):
                self.preview_canvas.delete("all"); self.preview_canvas.create_image(10,10,anchor=tk.NW,image=photo)
                self.preview_canvas.config(width=img.width+20, height=img.height+20)
            if hasattr(self,'big_preview_canvas'):
                self.big_preview_canvas.delete("all")
                mw=max(1,self.big_preview_canvas.winfo_width()-40); mh=max(1,self.big_preview_canvas.winfo_height()-40)
                if img.width>mw or img.height>mh:
                    s=min(mw/img.width, mh/img.height); nw,nz=int(img.width*s),int(img.height*s)
                    ri=img.resize((nw,nz), Image.Resampling.LANCZOS); bp=ImageTk.PhotoImage(ri)
                    self.big_preview_canvas.create_image((mw-nw)//2,(mh-nz)//2,anchor=tk.NW,image=bp)
                    self.big_preview_photo = bp
                else: self.big_preview_canvas.create_image((mw-img.width)//2,(mh-img.height)//2,anchor=tk.NW,image=photo)
            self.update_barcode_info(a)
            self.preview_info_label.config(text=f"Размер: {self.config.get('sticker.width_mm')}×{self.config.get('sticker.height_mm')} мм ({self.config.get('sticker.orientation')})")
        except Exception as e: self.log_message(f"Ошибка: {e}", "error"); traceback.print_exc()

    def update_barcode_info(self, article):
        ch = BarcodeChecker(); ok,_ = ch.check_code128_compatibility(article); bt = self.barcode_type_var.get()
        if bt=='auto':
            r = ch.get_recommended_barcode_type(article, self.config.config)
            txt = f"✅ Code128" if ok else f"⚠ QR" if r=='qr' else f"❌ нет кода"
        elif bt=='code128': txt = "✅ Code128" if ok else "❌ несовместим"
        elif bt=='qr': txt = "ℹ QR"
        else: txt = "ℹ без кода"
        if hasattr(self,'barcode_info_label'): self.barcode_info_label.config(text=txt)

    def select_invoice_file(self):
        d = Path(self.invoice_path.get()).parent if self.invoice_path.get() else self.config.get('paths.default_input_folder')
        fp = filedialog.askopenfilename(filetypes=[("Excel","*.xls *.xlsx *.xlsm")], initialdir=d)
        if fp: self.invoice_path.set(fp); self.config.set('paths.last_invoice_path', fp); self.log_message(f"Файл: {fp}")

    def select_output_folder(self):
        d = Path(self.output_folder.get()) if self.output_folder.get() else self.config.get('paths.default_output_folder')
        fp = filedialog.askdirectory(initialdir=d)
        if fp: self.output_folder.set(fp); self.config.set('paths.last_output_folder', fp); self.log_message(f"Папка: {fp}")

    def open_stickers_folder(self): os.startfile(str(Path(self.output_folder.get())))
    def open_settings_folder(self): os.startfile(str(APPDATA_DIR))

    def check_database(self):
        def c():
            try:
                p = self.config.get('paths.csv_path')
                if p and Path(p).exists() and self.nomenclature.load_from_file(p):
                    self.queue.put(("db_status", f"✅ CSV загружена ({len(self.nomenclature.data)} зап.)", None))
                else: self.queue.put(("db_status", "⚠ CSV не найдена", None))
            except Exception as e: self.queue.put(("db_status", f"❌ {str(e)[:50]}", None))
        threading.Thread(target=c, daemon=True).start()

    def update_database(self):
        def u():
            try:
                self.db_log_message("Обновление...")
                url = self.db_url_var.get(); self.config.set('paths.database_url', url)
                if self.nomenclature.download_and_load(url, local_path=self.config.get('paths.csv_path')):
                    self.queue.put(("db_status", f"✅ Обновлено ({len(self.nomenclature.data)} зап.)", None))
                    self.db_log_message(f"Обновлено! Записей: {len(self.nomenclature.data)}")
                else: self.queue.put(("db_status", "❌ Ошибка", None))
            except Exception as e: self.queue.put(("db_status", "❌ Ошибка", None)); self.db_log_message(f"Ошибка: {e}", "error")
        threading.Thread(target=u, daemon=True).start()

    def show_database_stats(self):
        if not self.nomenclature.loaded: messagebox.showinfo("Статистика", "База не загружена"); return
        s = self.nomenclature.get_stats(); msg = f"Записей: {s.get('total_records',0)}\nКолонки: {', '.join(s.get('columns',[]))}"
        messagebox.showinfo("Статистика", msg)

    def process_invoice(self):
        self.cleanup_temp_files()
        if not self.invoice_path.get(): messagebox.showwarning("Внимание", "Выберите файл!"); return
        self.save_settings()
        def p():
            try:
                self.log_message(f"Обработка: {self.invoice_path.get()}"); self.set_processing_state(True); self.progress_var.set(0)
                pos = self.invoice_parser.parse_invoice(self.invoice_path.get(), self.nomenclature)
                if not pos: self.queue.put(("error", "Нет позиций")); return
                self.progress_var.set(50); self.queue.put(("show_preview", pos))
            except Exception as e: self.queue.put(("error", str(e))); traceback.print_exc()
            finally: self.set_processing_state(False)
        threading.Thread(target=p, daemon=True).start()

    def process_selected(self, positions, action):
        if not positions: messagebox.showinfo("Информация", "Нет выбранных позиций"); return
        inv = self.invoice_parser.extract_invoice_info(self.invoice_path.get())
        num = inv.get('invoice_number','01')
        out = Path(self.output_folder.get()); name = Path(self.invoice_path.get()).stem
        res = out / f"stickers_{name}"; res.mkdir(parents=True, exist_ok=True)
        saved = []
        images_for_print = []
        
        for i,p in enumerate(positions):
            art = p.get('article_found') or p['article_source']
            nm = p.get('name_found') or p['name_source']
            addr = p.get('address', None)
            try:
                img = self.generator.generate_preview(
                    article=art, 
                    name=nm, 
                    quantity=p['quantity'], 
                    unit=p['unit'],
                    address=addr
                )
                fn = f"{num}_{i+1:03d}_{''.join(c for c in art if c.isalnum() or c in '._-') or f'pos_{i+1:03d}'}.png"
                sp = res/fn
                if self.generator.save_image(img, sp):
                    saved.append(sp)
                    images_for_print.append(img)
                    self.log_message(f"Создан: {fn}")
            except Exception as e: self.log_message(f"Ошибка: {str(e)[:100]}", "error")
        
        if action in ['save','save_print']:
            messagebox.showinfo("Результат", f"Сохранено: {len(saved)}/{len(positions)}\nПапка: {res}")
            if self.open_after_var.get(): os.startfile(str(res))
        
        if action in ['print', 'save_print'] and images_for_print:
            self.print_multiple_images(images_for_print)

    def on_closing(self): 
        self.cleanup_temp_files()
        self.save_settings(); 
        self.root.destroy()

    def test_invoice(self):
        if not self.invoice_path.get(): messagebox.showwarning("Внимание", "Выберите файл!"); return
        def t():
            try:
                self.log_message(f"Тест: {self.invoice_path.get()}"); self.set_processing_state(True)
                pos = self.invoice_parser.test_parse(self.invoice_path.get())
                if not pos: self.queue.put(("error", "Нет позиций")); return
                self.log_message(f"Найдено: {len(pos)}")
                for i,p in enumerate(pos[:5]): self.log_message(f"{i+1}. {p['article_source'][:20]} | {p['name_source'][:40]}")
            except Exception as e: self.queue.put(("error", str(e)))
            finally: self.set_processing_state(False)
        threading.Thread(target=t, daemon=True).start()

    def clear_invoice(self): self.invoice_path.set(""); self.log_message("Очищено")

    def print_multiple_images(self, images):
        """Печатает несколько изображений по очереди"""
        # Очищаем старые временные файлы
        self.cleanup_temp_files()
        
        def print_job():
            temp_paths = []
            for i, img in enumerate(images):
                try:
                    # Сохраняем во временный файл
                    fd, path = tempfile.mkstemp(suffix='.png', prefix='sticker_')
                    os.close(fd)
                    img.save(path, 'PNG', dpi=(300,300))
                    temp_paths.append(Path(path))
                    
                    # Отправляем на печать
                    os.startfile(path, "print")
                    
                    # Задержка между заданиями
                    if i < len(images) - 1:
                        time.sleep(2)
                    
                except Exception as e:
                    self.log_message(f"Ошибка печати: {e}", "error")
            
            # Добавляем файлы в общий список для последующего удаления
            if temp_paths:
                self.temp_files.extend(temp_paths)
                self.log_message(f"Создано временных файлов: {len(temp_paths)}")
        
        threading.Thread(target=print_job, daemon=True).start()    
    def cleanup_temp_files(self):
        """Удаляет все временные файлы"""
        for f in self.temp_files[:]:  # Копируем список для безопасного удаления
            try:
                if f.exists():
                    f.unlink()
                    self.temp_files.remove(f)
            except Exception as e:
                self.log_message(f"Ошибка удаления {f}: {e}", "warning")
        
        if self.temp_files:
            self.log_message(f"Очищено временных файлов: {len(self.temp_files)}")
    def on_settings_change(self): 
        self.cleanup_temp_files()  # Очищаем временные файлы
        self.save_settings_to_config(); 
        self.update_preview()

    def on_barcode_settings_change(self): 
        self.cleanup_temp_files()  # Очищаем временные файлы
        self.save_settings_to_config(); 
        self.update_preview()
    def save_settings(self):
        try: self.save_settings_to_config(); self.config.save(); self.log_message("Сохранено")
        except Exception as e: messagebox.showerror("Ошибка", str(e))

    def save_settings_to_config(self):
        self.config.set('sticker.width_mm', self.width_var.get())
        self.config.set('sticker.height_mm', self.height_var.get())
        self.config.set('sticker.orientation', self.orientation_var.get())
        self.config.set('sticker.border', self.border_var.get())
        self.config.set('sticker.background_color', self.bg_color_var.get())
        self.config.set('elements.article.enabled', self.article_enabled_var.get())
        self.config.set('elements.article.font_size', self.article_size_var.get())
        self.config.set('elements.article.bold', self.article_bold_var.get())
        self.config.set('elements.article.align', self.article_align_var.get())
        self.config.set('elements.article.color', self.article_color_var.get())
        self.config.set('elements.article.offset_x', self.article_offset_x_var.get())
        self.config.set('elements.article.offset_y', self.article_offset_y_var.get())
        self.config.set('elements.name.enabled', self.name_enabled_var.get())
        self.config.set('elements.name.font_size', self.name_size_var.get())
        self.config.set('elements.name.bold', self.name_bold_var.get())
        self.config.set('elements.name.italic', self.name_italic_var.get())
        self.config.set('elements.name.align', self.name_align_var.get())
        self.config.set('elements.name.color', self.name_color_var.get())
        self.config.set('elements.name.max_lines', self.name_max_lines_var.get())
        self.config.set('elements.name.offset_x', self.name_offset_x_var.get())
        self.config.set('elements.name.offset_y', self.name_offset_y_var.get())
        self.config.set('elements.quantity.enabled', self.qty_enabled_var.get())
        self.config.set('elements.quantity.font_size', self.qty_size_var.get())
        self.config.set('elements.quantity.bold', self.qty_bold_var.get())
        self.config.set('elements.quantity.italic', self.qty_italic_var.get())
        self.config.set('elements.quantity.align', self.qty_align_var.get())
        self.config.set('elements.quantity.color', self.qty_color_var.get())
        self.config.set('elements.quantity.offset_x', self.qty_offset_x_var.get())
        self.config.set('elements.quantity.offset_y', self.qty_offset_y_var.get())
        self.config.set('elements.address.enabled', self.address_enabled_var.get())
        self.config.set('elements.address.font_size', self.address_size_var.get())
        self.config.set('elements.address.bold', self.address_bold_var.get())
        self.config.set('elements.address.italic', self.address_italic_var.get())
        self.config.set('elements.address.align', self.address_align_var.get())
        self.config.set('elements.address.color', self.address_color_var.get())
        self.config.set('elements.address.offset_x', self.address_offset_x_var.get())
        self.config.set('elements.address.offset_y', self.address_offset_y_var.get())
        self.config.set('elements.address.border', self.address_border_var.get())
        self.config.set('elements.address.background_color', self.address_bg_color_var.get())
        self.config.set('barcode.enabled', self.barcode_enabled_var.get())
        self.config.set('barcode.type', self.barcode_type_var.get())
        self.config.set('barcode.size_mm', self.barcode_size_var.get())
        self.config.set('barcode.position', self.barcode_position_var.get())
        self.config.set('barcode.border', self.barcode_border_var.get())
        self.config.set('barcode.code128_width_mm', self.code128_width_var.get())
        self.config.set('barcode.code128_height_mm', self.code128_height_var.get())
        self.config.set('barcode.show_text', self.barcode_show_text_var.get())
        self.config.set('barcode.text_size', self.barcode_text_size_var.get())
        self.config.set('barcode.offset_x', self.barcode_offset_x_var.get())
        self.config.set('barcode.offset_y', self.barcode_offset_y_var.get())
        self.config.set('barcode.text_offset_x', self.barcode_text_offset_x_var.get())
        self.config.set('barcode.text_offset_y', self.barcode_text_offset_y_var.get())
        self.config.set('barcode.auto_rules.fallback_to_qr', self.fallback_qr_var.get())
        self.config.set('barcode.auto_rules.skip_if_invalid', self.skip_invalid_var.get())
        self.config.set('behavior.overwrite_files', self.overwrite_var.get())
        self.config.set('behavior.open_after_process', self.open_after_var.get())
        self.config.set('behavior.skip_errors', self.skip_errors_var.get())
        self.config.set('paths.database_url', self.db_url_var.get())
        self.config.set('barcode.text_scale_x', self.barcode_text_scale_x_var.get())
        self.config.set('barcode.text_scale_y', self.barcode_text_scale_y_var.get())

    def reset_settings(self):
        if not messagebox.askyesno("Сброс", "Сбросить настройки?"): return
        try:
            for k,v in ConfigManager.DEFAULT_CONFIG.items(): self.config.set(k,v)
            self.width_var.set(self.config.get('sticker.width_mm')); self.height_var.set(self.config.get('sticker.height_mm'))
            self.orientation_var.set(self.config.get('sticker.orientation')); self.border_var.set(self.config.get('sticker.border'))
            self.bg_color_var.set(self.config.get('sticker.background_color'))
            self.article_enabled_var.set(self.config.get('elements.article.enabled')); self.article_size_var.set(self.config.get('elements.article.font_size'))
            self.article_bold_var.set(self.config.get('elements.article.bold')); self.article_align_var.set(self.config.get('elements.article.align'))
            self.article_color_var.set(self.config.get('elements.article.color'))
            self.name_enabled_var.set(self.config.get('elements.name.enabled')); self.name_size_var.set(self.config.get('elements.name.font_size'))
            self.name_bold_var.set(self.config.get('elements.name.bold')); self.name_italic_var.set(self.config.get('elements.name.italic'))
            self.name_align_var.set(self.config.get('elements.name.align')); self.name_color_var.set(self.config.get('elements.name.color'))
            self.name_max_lines_var.set(self.config.get('elements.name.max_lines'))
            self.qty_enabled_var.set(self.config.get('elements.quantity.enabled')); self.qty_size_var.set(self.config.get('elements.quantity.font_size'))
            self.qty_bold_var.set(self.config.get('elements.quantity.bold')); self.qty_italic_var.set(self.config.get('elements.quantity.italic'))
            self.qty_align_var.set(self.config.get('elements.quantity.align')); self.qty_color_var.set(self.config.get('elements.quantity.color'))
            self.barcode_enabled_var.set(self.config.get('barcode.enabled')); self.barcode_type_var.set(self.config.get('barcode.type'))
            self.barcode_size_var.set(self.config.get('barcode.size_mm')); self.barcode_position_var.set(self.config.get('barcode.position'))
            self.barcode_border_var.set(self.config.get('barcode.border')); self.code128_width_var.set(self.config.get('barcode.code128_width_mm'))
            self.code128_height_var.set(self.config.get('barcode.code128_height_mm')); self.barcode_show_text_var.set(self.config.get('barcode.show_text'))
            self.barcode_text_size_var.set(self.config.get('barcode.text_size')); self.fallback_qr_var.set(self.config.get('barcode.auto_rules.fallback_to_qr'))
            self.skip_invalid_var.set(self.config.get('barcode.auto_rules.skip_if_invalid'))
            self.address_border_var.set(self.config.get('elements.address.border',False))
            self.address_bg_color_var.set(self.config.get('elements.address.background_color','#FFFFFF'))
            self.db_url_var.set(self.config.get('paths.database_url'))
            self.update_preview(); self.log_message("Настройки сброшены"); messagebox.showinfo("Успех", "Сброс выполнен")
        except Exception as e: messagebox.showerror("Ошибка", str(e))

    def save_process_log(self):
        t = self.process_log.get(1.0, tk.END).strip()
        if not t: messagebox.showwarning("Внимание", "Лог пуст"); return
        fp = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text","*.txt")])
        if fp: open(fp,'w',encoding='utf-8').write(t); self.log_message(f"Лог сохранён: {fp}")

    def save_log(self):
        t = self.db_log_text.get(1.0, tk.END).strip()
        if not t: messagebox.showwarning("Внимание", "Лог пуст"); return
        fp = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text","*.txt")])
        if fp: open(fp,'w',encoding='utf-8').write(t); self.db_log_message(f"Лог сохранён: {fp}")

    def log_message(self, msg, level="info"):
        tag = f"tag_{level}"
        if tag not in self.process_log.tag_names(): self.process_log.tag_config(tag, foreground={'info':'black','success':'darkgreen','warning':'darkorange','error':'darkred'}[level])
        self.process_log.insert(tk.END, f"{msg}\n", tag); self.process_log.see(tk.END)
        if hasattr(self,'log_text'):
            tag2 = f"main_tag_{level}"
            if tag2 not in self.log_text.tag_names(): self.log_text.tag_config(tag2, foreground={'info':'black','success':'darkgreen','warning':'darkorange','error':'darkred'}[level])
            self.log_text.insert(tk.END, f"{msg}\n", tag2); self.log_text.see(tk.END)
        if level in ["error","warning"]: self.status_text.set(msg[:100])
        else: self.status_text.set("Обработка...")

    def db_log_message(self, msg, level="info"):
        tag = f"db_tag_{level}"
        if tag not in self.db_log_text.tag_names(): self.db_log_text.tag_config(tag, foreground={'info':'black','success':'darkgreen','warning':'darkorange','error':'darkred'}[level])
        self.db_log_text.insert(tk.END, f"{msg}\n", tag); self.db_log_text.see(tk.END)
        self.log_message(f"[БД] {msg}", level)

    def set_processing_state(self, state): self.queue.put(("processing", state))

    def show_help(self):
        h = tk.Toplevel(self.root); h.title("Справка"); h.geometry("600x500")
        t = scrolledtext.ScrolledText(h, wrap=tk.WORD, font=('Segoe UI',10)); t.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        try:
            hf = Path(__file__).parent/"help.txt"
            t.insert(1.0, hf.read_text(encoding='utf-8') if hf.exists() else "Справка не найдена")
        except: t.insert(1.0, "Ошибка загрузки")
        t.config(state='disabled'); ttk.Button(h, text="Закрыть", command=h.destroy).pack(pady=5)

    def check_queue(self):
        try:
            while True:
                t, *a = self.queue.get_nowait()
                if t=="db_status": self.db_status_label.config(text=a[0])
                elif t=="show_preview":
                    d = PreviewDialog(self.root, a[0], self.generator, self.address_manager)
                    self.root.wait_window(d)
                    if d.result in ['save','print','save_print']:
                        self.process_selected(d.get_selected(), d.result)
                    else: self.log_message("Отменено"); self.status_text.set("Готов")
                elif t=="error": messagebox.showerror("Ошибка", a[0]); self.status_text.set("Ошибка")
                elif t=="processing":
                    if a[0]: self.process_btn.config(state='disabled', text="⏳"); self.status_text.set("Обработка...")
                    else: self.process_btn.config(state='normal', text="🚀 Создать"); self.status_text.set("Готов")
                elif t=="address_status": self.address_status_label.config(text=a[0])
                elif t=="analysis_result":
                    an = a[0]; self.analysis_text.delete(1.0,tk.END)
                    self.analysis_text.insert(1.0, f"Колонки: {', '.join(an.get('columns',[]))}\n")
                    self.analysis_text.insert(tk.END, f"Артикул: {an.get('suggestions',{}).get('article',[])}\n")
                    self.analysis_text.insert(tk.END, f"Адрес: {an.get('suggestions',{}).get('address',[])}")
        except queue.Empty: pass
        self.root.after(100, self.check_queue)

    def check_address_database(self):
        def c():
            try:
                if self.address_manager.load_addresses():
                    self.queue.put(("address_status", f"✅ Адресов: {len(self.address_manager.data)}", None))
                else: self.queue.put(("address_status", "⚠ Не загружена", None))
            except Exception as e: self.queue.put(("address_status", f"❌ {str(e)[:50]}", None))
        threading.Thread(target=c, daemon=True).start()

    def select_address_file(self):
        fp = filedialog.askopenfilename(filetypes=[("Excel","*.xls *.xlsx *.xlsm")])
        if fp: self.address_file_var.set(fp); self.log_message(f"Файл: {fp}")

    def analyze_address_file(self):
        if not self.address_file_var.get(): messagebox.showwarning("Внимание", "Выберите файл!"); return
        def a():
            try: self.queue.put(("analysis_result", self.address_manager.analyze_excel_file(self.address_file_var.get())))
            except Exception as e: self.queue.put(("error", str(e)))
        threading.Thread(target=a, daemon=True).start()

    def import_addresses(self):
        fp = self.address_file_var.get()
        if not fp: messagebox.showwarning("Внимание", "Выберите файл!"); return
        d = tk.Toplevel(self.root); d.title("Импорт"); d.geometry("400x250")
        an = self.address_manager.analyze_excel_file(fp)
        ttk.Label(d, text="Колонка артикулов:").pack(pady=5)
        av = tk.StringVar(); ac = ttk.Combobox(d, textvariable=av, values=an.get('suggestions',{}).get('article',[]))
        ac.pack(pady=5); ac.current(0) if ac['values'] else None
        ttk.Label(d, text="Колонка адресов:").pack(pady=5)
        adv = tk.StringVar(); adc = ttk.Combobox(d, textvariable=adv, values=an.get('suggestions',{}).get('address',[]))
        adc.pack(pady=5); adc.current(0) if adc['values'] else None
        def do():
            ok,msg = self.address_manager.import_from_excel(fp, av.get(), adv.get())
            if ok: messagebox.showinfo("Успех", msg); self.check_address_database()
            else: messagebox.showerror("Ошибка", msg)
            d.destroy()
        ttk.Button(d, text="Импорт", command=do).pack(pady=10)

    def search_address(self):
        a = self.search_article_var.get().strip(); n = self.search_name_var.get().strip()
        if not a and not n: messagebox.showwarning("Внимание", "Введите данные!"); return
        addr = self.address_manager.find_address(a, n)
        if addr: self.search_result_label.config(text=f"✓ {addr}", foreground="green", font=('Arial',9,'bold'))
        else: self.search_result_label.config(text="✗ Не найден", foreground="red", font=('Arial',9))

    def flash_red(self, widget):
        orig_bg = widget.cget('background')
        widget.config(background='#ff9999')
        self.root.after(100, lambda: widget.config(background='#ff6666'))
        self.root.after(200, lambda: widget.config(background='#ff9999'))
        self.root.after(300, lambda: widget.config(background=orig_bg))
    def check_search_field(self, var, widget):
        """Проверка длины ввода"""
        text = var.get().strip()
        if len(text) < 3 and len(text) > 0:
            self.flash_red(widget)
    def search_and_fill(self):
        text = self.preview_article_var.get().strip()
        if len(text) < 3:
            self.flash_red(self.article_entry)
            return
        addr = self.address_manager.find_address(text)
        if addr:
            self.preview_address_var.set(addr)
            self.log_message(f"Найден адрес: {addr}", "success")
            return
        if self.nomenclature and self.nomenclature.loaded:
            result = self.nomenclature.find_by_source_article(text)
            if result:
                name, article = result
                self.preview_name_var.set(name)
                self.preview_article_var.set(article)
                self.log_message(f"Найдено: {article}", "success")
                addr2 = self.address_manager.find_address(article)
                if addr2:
                    self.preview_address_var.set(addr2)
                else:
                    self.preview_address_var.set("")
                return
        self.flash_red(self.article_entry)
        self.show_search_results(text)
    def search_and_fill_name(self):
        text = self.preview_name_var.get().strip()
        if len(text) < 8:
            results = self.nomenclature.find_by_name_fuzzy(text, threshold=0.4, limit=50)
        else:
            results = self.nomenclature.find_by_name_fuzzy(text, threshold=0.8, limit=10)
        if self.nomenclature and self.nomenclature.loaded:
            results = self.nomenclature.find_by_name_fuzzy(text, limit=20)
            if len(results) == 1:
                name, article = results[0]
                self.preview_name_var.set(name)
                self.preview_article_var.set(article)
                addr = self.address_manager.find_address(article)
                self.preview_address_var.set(addr or "")
                self.log_message(f"Найдено: {article}", "success")
            elif len(results) > 1:
                self.show_name_search_results(results, text)
            else:
                self.flash_red(self.name_entry)
    def search_and_fill_addr(self):
        text = self.preview_address_var.get().strip()
        if len(text) < 3:
            self.flash_red(self.addr_entry)
            return
        found = []
        for art, addr in self.address_manager.data.items():
            if text.upper() in addr.upper():
                found.append((art, addr))
        if len(found) == 1:
            art, addr = found[0]
            self.preview_article_var.set(art)
            self.preview_address_var.set(addr)
            if self.nomenclature and self.nomenclature.loaded:
                res = self.nomenclature.find_by_source_article(art)
                if res:
                    self.preview_name_var.set(res[0])
            self.log_message(f"Найден: {art}", "success")
        elif len(found) > 1:
            self.show_addr_results(found)
        else:
            self.flash_red(self.addr_entry)
    def show_search_results(self, query, by_name=False):
        if not self.nomenclature or not self.nomenclature.loaded:
            return
        d = tk.Toplevel(self.root)
        d.title("Результаты поиска")
        d.geometry("640x480")
        d.transient(self.root)
        ttk.Label(d, text=f"Результаты для: {query}", font=('Arial',9,'bold')).pack(pady=5)
        frame = ttk.Frame(d)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        vsb = ttk.Scrollbar(frame)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        tree = ttk.Treeview(frame, columns=('article','name','address'), show='headings',
                            yscrollcommand=vsb.set, height=15)
        tree.pack(fill=tk.BOTH, expand=True)
        vsb.config(command=tree.yview)

        tree.heading('article', text='Артикул')
        tree.heading('name', text='Наименование')
        tree.heading('address', text='Адрес')
        tree.column('article', width=120)
        tree.column('name', width=350)
        tree.column('address', width=40)
        results = []
        if by_name:
            for name, art, _ in self.nomenclature.data:
                if query.lower() in name.lower():
                    addr = self.address_manager.find_address(art) or ""
                    tree.insert('', 'end', values=(art, name[:100], addr))
        else:
            for name, art, _ in self.nomenclature.data:
                if query in art or query.lower() in name.lower():
                    addr = self.address_manager.find_address(art) or ""
                    tree.insert('', 'end', values=(art, name[:100], addr))
        def select():
            sel = tree.selection()
            if not sel:
                return
            values = tree.item(sel[0], 'values')
            art = values[0]
            name = values[1]
            addr = values[2]
            self.preview_article_var.set(art)
            self.preview_name_var.set(name)
            self.preview_address_var.set(addr)
            d.destroy()
        ttk.Button(d, text="Выбрать", command=select).pack(pady=5)
    def show_name_search_results(self, results, query):
        """Показать результаты поиска по названию"""
        d = tk.Toplevel(self.root)
        d.title("Результаты поиска по названию")
        d.geometry("840x600")
        d.transient(self.root)
        ttk.Label(d, text=f"Найдено вариантов для: {query}", font=('Arial',9,'bold')).pack(pady=5)
        frame = ttk.Frame(d)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        vsb = ttk.Scrollbar(frame)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        tree = ttk.Treeview(frame, columns=('article','name','address'), show='headings',
                            yscrollcommand=vsb.set, height=20)
        tree.pack(fill=tk.BOTH, expand=True)
        vsb.config(command=tree.yview)
        tree.heading('article', text='Артикул')
        tree.heading('name', text='Наименование')
        tree.heading('address', text='Адрес')
        tree.column('article', width=120)
        tree.column('name', width=500)
        tree.column('address', width=80)
        for name, article in results:
            addr = self.address_manager.find_address(article) or ""
            tree.insert('', 'end', values=(article, name[:150], addr))
        def select():
            sel = tree.selection()
            if not sel:
                return
            values = tree.item(sel[0], 'values')
            art = values[0]
            name = values[1]
            addr = values[2]
            self.preview_article_var.set(art)
            self.preview_name_var.set(name)
            self.preview_address_var.set(addr)
            d.destroy()
        btn_frame = ttk.Frame(d)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Выбрать", command=select).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=d.destroy).pack(side=tk.LEFT, padx=5)    
    def show_addr_results(self, results):
        d = tk.Toplevel(self.root)
        d.title("Результаты поиска по адресу")
        d.geometry("840x600")
        d.transient(self.root)
        ttk.Label(d, text="Найденные позиции:", font=('Arial',9,'bold')).pack(pady=5)
        frame = ttk.Frame(d)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        vsb = ttk.Scrollbar(frame)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        tree = ttk.Treeview(frame, columns=('article','name','address'), show='headings',
                            yscrollcommand=vsb.set, height=15)
        tree.pack(fill=tk.BOTH, expand=True)
        vsb.config(command=tree.yview)
        tree.heading('article', text='Артикул')
        tree.heading('name', text='Наименование')
        tree.heading('address', text='Адрес')
        tree.column('article', width=120)
        tree.column('name', width=400)
        tree.column('address', width=80)
        for art, addr in results:
            name = ""
            if self.nomenclature and self.nomenclature.loaded:
                res = self.nomenclature.find_by_source_article(art)
                if res:
                    name = res[0][:100]
            tree.insert('', 'end', values=(art, name, addr))
        def select():
            sel = tree.selection()
            if not sel:
                return
            values = tree.item(sel[0], 'values')
            art = values[0]
            name = values[1]
            addr = values[2]
            self.preview_article_var.set(art)
            self.preview_name_var.set(name)
            self.preview_address_var.set(addr)
            d.destroy()
        ttk.Button(d, text="Выбрать", command=select).pack(pady=5)
    def export_addresses_csv(self):
        if not self.address_manager.data: messagebox.showwarning("Внимание", "База пуста!"); return
        fp = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if fp:
            try:
                with open(fp,'w',encoding='utf-8',newline='') as f:
                    w = csv.DictWriter(f, fieldnames=['article','address']); w.writeheader()
                    for art,addr in self.address_manager.data.items(): w.writerow({'article':art,'address':addr})
                self.log_message(f"Экспорт: {fp}"); messagebox.showinfo("Успех", f"Сохранено:\n{fp}")
            except Exception as e: messagebox.showerror("Ошибка", str(e))
    def export_addresses_excel(self):
        if not self.address_manager.data: messagebox.showwarning("Внимание", "База пуста!"); return
        fp = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel","*.xlsx")])
        if fp:
            try:
                pd.DataFrame(list(self.address_manager.data.items()), columns=['Артикул','Адрес']).to_excel(fp, index=False)
                self.log_message(f"Экспорт: {fp}"); messagebox.showinfo("Успех", f"Сохранено:\n{fp}")
            except Exception as e: messagebox.showerror("Ошибка", str(e))
    def copy_text(self, e=None):
        w = self.root.focus_get()
        if hasattr(w,'tag_ranges') and w.tag_ranges('sel'):
            self.root.clipboard_clear()
            self.root.clipboard_append(w.get('sel.first','sel.last'))
        elif hasattr(w,'selection_get'):
            self.root.clipboard_clear()
            self.root.clipboard_append(w.selection_get())
    def paste_text(self, e=None):
        w = self.root.focus_get()
        if hasattr(w,'insert'):
            try:
                t = self.root.clipboard_get()
                if hasattr(w,'tag_ranges') and w.tag_ranges('sel'):
                    w.delete('sel.first','sel.last')
                w.insert(tk.INSERT, t)
            except:
                pass
def run_gui(config, nomenclature, generator, invoice_parser):
    root = tk.Tk(); app = MainWindow(root, config, nomenclature, generator, invoice_parser); root.mainloop()