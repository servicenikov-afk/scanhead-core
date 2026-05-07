# gui/main_window.py
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import os

from utils.path_utils import resource_path
from config.settings import Settings
from core.nomenclature import NomenclatureDB
from core.address_manager import AddressDB
from gui.tabs.count_tab import CountTab
from gui.tabs.inventory_tab import InventoryTab
from gui.tabs.search_tab import SearchTab

logger = logging.getLogger(__name__)

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ScanHead 1.2.4")
        self.root.geometry("1000x800")
        
        # Установка иконки
        icon_path = resource_path("icons/app.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
                logger.info(f"Иконка загружена: {icon_path}")
            except Exception as e:
                logger.warning(f"Не удалось загрузить иконку: {e}")
        
        self.settings = Settings()
        self.nomenclature = NomenclatureDB(self.settings.get_nomenclature_path())
        self.addresses = AddressDB(self.settings.get_addresses_path())
        
        self._load_databases()
        self._create_menu()
        self._create_notebook()
        
        self.focus_timer = None
        self._start_focus_timer()
        
        self.root.bind('<Key>', self._reset_focus_timer)
        self.root.bind('<Button-1>', self._reset_focus_timer)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _on_tab_changed(self, event):
        if not self.settings.get('behavior.auto_focus', True):
            return
        self._focus_current_entry()
    
    def _start_focus_timer(self):
        if self.focus_timer:
            self.root.after_cancel(self.focus_timer)
        timeout = self.settings.get('behavior.focus_timeout', 3.0) * 1000
        self.focus_timer = self.root.after(int(timeout), self._focus_current_entry)
    
    def _focus_current_entry(self):
        if self.settings.get('behavior.auto_focus', True):
            current = self.notebook.select()
            if current:
                tab = self.notebook.nametowidget(current)
                if hasattr(tab, 'article_entry'):
                    tab.article_entry.focus()
        self._start_focus_timer()
    
    def _reset_focus_timer(self, event=None):
        if self.settings.get('behavior.auto_focus', True):
            self._start_focus_timer()
    
    def _load_databases(self):
        self.nomenclature.load()
        self.addresses.load()
        if not self.nomenclature.loaded:
            messagebox.showwarning(
                "Предупреждение",
                f"Не удалось загрузить номенклатуру из:\n{self.settings.get_nomenclature_path()}\n\n"
                "Поиск будет работать только по введенным артикулам."
            )
    
    def _create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Настройки", command=self._show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self._on_closing)
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self._show_about)
    
    def _create_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)
        
        self.count_tab = CountTab(self.notebook, self.nomenclature, self.addresses, self.settings)
        self.notebook.add(self.count_tab, text="Подсчет")
        
        self.inventory_tab = InventoryTab(self.notebook, self.nomenclature, self.addresses, self.settings)
        self.notebook.add(self.inventory_tab, text="Инвентаризация")
        
        self.search_tab = SearchTab(self.notebook, self.nomenclature, self.addresses, self.settings)
        self.notebook.add(self.search_tab, text="Поиск")
    
    def _show_settings(self):
        from gui.settings_dialog import SettingsDialog
        SettingsDialog(self.root, self.settings)
    
    def _show_about(self):
        messagebox.showinfo(
            "О программе",
            "ScanHead 1.2.1\n\nПрограмма для складского учета и инвентаризации\nПоддерживает сканирование штрих-кодов и ручной ввод"
        )
    
    def _on_closing(self):
        if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти?"):
            self.root.destroy()
    
    def run(self):
        self.root.mainloop()