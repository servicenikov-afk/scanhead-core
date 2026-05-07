import tkinter as tk
from tkinter import ttk, messagebox
from modules.barcode_checker import BarcodeChecker

class SettingsDialog:
    def __init__(self, parent, settings):
        self.settings = settings
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Настройки")
        self.dialog.geometry("500x450")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self._create_widgets()
        self._load_settings()
    
    def _create_widgets(self):
        main = ttk.Frame(self.dialog, padding="20")
        main.pack(fill=tk.BOTH, expand=True)
        
        # Поведение
        beh_frame = ttk.LabelFrame(main, text="Поведение", padding="10")
        beh_frame.pack(fill=tk.X, pady=(0,10))
        
        self.auto_fix_layout = tk.BooleanVar()
        ttk.Checkbutton(beh_frame, text="Автоисправление раскладки RU-EN", variable=self.auto_fix_layout).pack(anchor=tk.W)
        
        self.auto_mode = tk.BooleanVar()
        ttk.Radiobutton(beh_frame, text="Авто (Enter = +1)", variable=self.auto_mode, value=True).pack(anchor=tk.W)
        ttk.Radiobutton(beh_frame, text="Вручную (Enter = запрос количества)", variable=self.auto_mode, value=False).pack(anchor=tk.W)
        
        # Пути
        path_frame = ttk.LabelFrame(main, text="Пути", padding="10")
        path_frame.pack(fill=tk.X, pady=(0,10))
        
        ttk.Label(path_frame, text="Папка экспорта:").pack(anchor=tk.W)
        self.export_folder = ttk.Entry(path_frame)
        self.export_folder.pack(fill=tk.X)
        ttk.Button(path_frame, text="Выбрать", command=self._select_export_folder).pack(anchor=tk.W, pady=(5,0))
        
        # Кнопки
        btn_frame = ttk.Frame(main)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Сохранить", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        focus_frame = ttk.LabelFrame(main, text="Автофокус", padding="10")
        focus_frame.pack(fill=tk.X, pady=(0,10))
        
        self.auto_focus = tk.BooleanVar()
        cb = ttk.Checkbutton(focus_frame, text="Автофокус на поле ввода", variable=self.auto_focus, command=self._toggle_focus_timeout)
        cb.pack(anchor=tk.W)
        
        timeout_frame = ttk.Frame(focus_frame)
        timeout_frame.pack(anchor=tk.W, pady=(5,0))
        ttk.Label(timeout_frame, text="Время переключения:").pack(side=tk.LEFT)
        self.focus_timeout = ttk.Spinbox(timeout_frame, from_=1.0, to=10.0, increment=0.5, width=5)
        self.focus_timeout.pack(side=tk.LEFT, padx=(5,0))
        ttk.Label(timeout_frame, text="сек").pack(side=tk.LEFT)
        
        self.auto_manual_unit = tk.BooleanVar()
        ttk.Checkbutton(focus_frame, text="Авто-ручной ввод если ед.изм. не шт", variable=self.auto_manual_unit).pack(anchor=tk.W)
        
        timeout_frame = ttk.Frame(focus_frame)
        timeout_frame.pack(anchor=tk.W, pady=(5,0))
        ttk.Label(timeout_frame, text="Время переключения:").pack(side=tk.LEFT)
        self.focus_timeout = ttk.Spinbox(timeout_frame, from_=1.0, to=10.0, increment=0.5, width=5)
        self.focus_timeout.pack(side=tk.LEFT, padx=(5,0))
        ttk.Label(timeout_frame, text="сек").pack(side=tk.LEFT)
    
    def _toggle_focus_timeout(self):
        state = 'normal' if self.auto_focus.get() else 'disabled'
        self.focus_timeout.config(state=state)    
    def _select_export_folder(self):
        from tkinter import filedialog
        folder = filedialog.askdirectory()
        if folder:
            self.export_folder.delete(0, tk.END)
            self.export_folder.insert(0, folder)
    
    def _load_settings(self):
        self.auto_fix_layout.set(self.settings.get('behavior.auto_fix_layout', True))
        self.auto_mode.set(self.settings.get('scanner.auto_add', True))
        self.export_folder.insert(0, self.settings.get('paths.export_folder', ''))
        self.auto_focus.set(self.settings.get('behavior.auto_focus', True))
        self.auto_manual_unit.set(self.settings.get('behavior.auto_manual_unit', True))
        self.focus_timeout.delete(0, tk.END)
        self.focus_timeout.insert(0, str(self.settings.get('behavior.focus_timeout', 3.0)))
        self._toggle_focus_timeout()
    
    def _save(self):
        self.settings.set('behavior.auto_fix_layout', self.auto_fix_layout.get())
        self.settings.set('scanner.auto_add', self.auto_mode.get())
        if self.export_folder.get():
            self.settings.set('paths.export_folder', self.export_folder.get())
        self.dialog.destroy()
        self.settings.set('behavior.auto_manual_unit', self.auto_manual_unit.get())
        self.settings.set('behavior.auto_focus', self.auto_focus.get())
        try:
            timeout = float(self.focus_timeout.get())
            self.settings.set('behavior.focus_timeout', timeout)
        except:
            pass        