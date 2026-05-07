# gui/tabs/count_tab.py
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict

from gui.widgets.article_entry import ArticleEntry
from core.nomenclature import NomenclatureDB
from core.address_manager import AddressDB
from models.count_item import CountItem
from exporters.excel_exporter import ExcelExporter
from exporters.csv_exporter import CSVExporter
from commands import CommandHandler

logger = logging.getLogger(__name__)

class CountTab(ttk.Frame):
    def __init__(self, parent, nomenclature, addresses, settings):
        super().__init__(parent)
        self.nomenclature = nomenclature
        self.addresses = addresses
        self.settings = settings
        self.items: Dict[str, CountItem] = {}
        self.auto_mode = tk.BooleanVar(value=self.settings.is_auto_add())
        self.last_article = None
        self.active_article = None
        self._create_widgets()
        self._update_table()
    
    def _create_widgets(self):
        control = ttk.LabelFrame(self, text="Управление подсчетом", padding="10")
        control.pack(fill=tk.X, padx=5, pady=5)
        self.article_entry = ArticleEntry(control, on_submit_callback=self._on_article_submit)
        self.article_entry.pack(fill=tk.X)
        quick = ttk.Frame(control)
        quick.pack(fill=tk.X, pady=(10,0))
        ttk.Button(quick, text="+1", command=lambda: self._add_to_last(1), width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick, text="+10", command=lambda: self._add_to_last(10), width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick, text="Очистить", command=self._clear_all, width=10).pack(side=tk.RIGHT, padx=2)
        
        table_frame = ttk.LabelFrame(self, text="Список подсчета", padding="5")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        columns = ('article','name','quantity','address','actions')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        self.tree.heading('article',text='Артикул')
        self.tree.heading('name',text='Наименование')
        self.tree.heading('quantity',text='Кол-во')
        self.tree.heading('address',text='Адрес')
        self.tree.heading('actions',text='Действия')
        self.tree.column('article',width=150)
        self.tree.column('name',width=400)
        self.tree.column('quantity',width=80,anchor=tk.CENTER)
        self.tree.column('address',width=100)
        self.tree.column('actions',width=100,anchor=tk.CENTER)
        v = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v.set, xscrollcommand=h.set)
        self.tree.grid(row=0,column=0,sticky='nsew')
        v.grid(row=0,column=1,sticky='ns')
        h.grid(row=1,column=0,sticky='ew')
        table_frame.grid_rowconfigure(0,weight=1)
        table_frame.grid_columnconfigure(0,weight=1)
        self.tree.bind('<ButtonRelease-1>', self._on_tree_click)
        
        export = ttk.Frame(self)
        export.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(export, text="Excel", command=self._export_to_excel, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(export, text="CSV", command=self._export_to_csv, width=10).pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(self, text="Готов к подсчету", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, padx=5, pady=5)
    
    def _set_active_row(self, article: str):
        if self.active_article:
            for item_id in self.tree.get_children():
                vals = self.tree.item(item_id, 'values')
                if vals and vals[0] == self.active_article:
                    self.tree.item(item_id, tags=())
                    break
        self.active_article = article
        for item_id in self.tree.get_children():
            vals = self.tree.item(item_id, 'values')
            if vals and vals[0] == article:
                self.tree.item(item_id, tags=('active',))
                self.tree.see(item_id)
                break
    
    def _on_article_submit(self, code: str, is_command: bool = False):
        if is_command:
            self._handle_command(code)
            return
        
        prod = self.nomenclature.find_by_article_or_barcode(code)
        if prod:
            art, name, addr = prod.article, prod.name, self.addresses.get_address(prod.article)
            if art in self.items:
                self._set_active_row(art)
                self.status_label.config(text=f"✓ Найден: {name[:40]} (уже {self.items[art].quantity:.0f} шт.)", foreground="green")
                self.after(2000, lambda: self.status_label.config(foreground="black"))
        else:
            art, name, addr = code, "Не найдено в базе", None
            self.status_label.config(
                text=f"✗ Товар '{code}' не найден в базе",
                foreground="red"
            )
            self.after(2000, lambda: self.status_label.config(foreground="black"))
        
        if self.auto_mode.get():
            self._add_item(art, name, addr, 1)
        else:
            self._show_quantity_dialog(art, name, addr)
        
        self.last_article = art
    
    def _handle_command(self, cmd_code: str):
        cmd = CommandHandler.parse(cmd_code)
        if cmd == 'CMD_ADD1':
            self._add_to_last(1)
        elif cmd == 'CMD_ADD10':
            self._add_to_last(10)
        elif cmd == 'CMD_ADD100':
            self._add_to_last(100)
        elif cmd == 'CMD_SUB1':
            self._add_to_last(-1)
        elif cmd == 'CMD_SUB10':
            self._add_to_last(-10)
        elif cmd == 'CMD_SUB100':
            self._add_to_last(-100)
        elif cmd == 'CMD_RESET_ACTUAL':
            self._clear_all()
        self.article_entry.clear()
        self.article_entry.focus()
    
    def _add_item(self, art, name, addr, qty):
        if art in self.items:
            self.items[art].add(qty)
            self._set_active_row(art)
        else:
            self.items[art] = CountItem(art, name, qty, addr)
            self._set_active_row(art)
        self._update_table()
        self.status_label.config(text=f"✓ {name[:40]} +{qty}")
        self.after(2000, lambda: self.status_label.config(text="Готов к подсчету"))
    
    def _add_to_last(self, amt):
        if self.last_article and self.last_article in self.items:
            self._set_active_row(self.last_article)
            self.items[self.last_article].add(amt)
            self._update_table()
            self.status_label.config(text=f"✓ +{amt} к {self.items[self.last_article].name[:30]}")
            self.after(2000, lambda: self.status_label.config(text="Готов к подсчету"))
        else:
            messagebox.showinfo("Инфо", "Сначала отсканируйте товар")
    
    def _show_quantity_dialog(self, art, name, addr):
        d = tk.Toplevel(self)
        d.title("Ввод количества")
        d.geometry("400x350")
        d.transient(self)
        d.grab_set()
        d.update_idletasks()
        x = self.winfo_x() + self.winfo_width()//2 - 200
        y = self.winfo_y() + self.winfo_height()//2 - 175
        d.geometry(f"+{x}+{y}")
        ttk.Label(d, text=name, font=('Arial',10,'bold'), wraplength=350).pack(pady=10)
        ttk.Label(d, text=f"Артикул: {art}").pack()
        ttk.Label(d, text="Количество:").pack(pady=(10,0))
        q_var = tk.StringVar(value="1")
        e = ttk.Entry(d, textvariable=q_var, font=('Arial',14), width=15)
        e.pack(pady=5)
        e.focus()
        e.select_range(0,tk.END)
        btn = ttk.Frame(d)
        btn.pack(pady=10)
        for v in [1,5,10,20,50,100]:
            ttk.Button(btn, text=str(v), width=5, command=lambda val=v: q_var.set(str(val))).pack(side=tk.LEFT, padx=2)
        def ok():
            try:
                q = float(q_var.get().replace(',','.'))
                if q <= 0:
                    messagebox.showwarning("Ошибка", "Количество должно быть > 0")
                    return
                self._add_item(art, name, addr, q)
                d.destroy()
            except:
                messagebox.showerror("Ошибка", "Введите число")
        ttk.Button(d, text="OK", command=ok, width=10).pack(pady=5)
        ttk.Button(d, text="Отмена", command=d.destroy, width=10).pack()
        e.bind('<Return>', lambda e: ok())
    
    def _on_tree_click(self, e):
        region = self.tree.identify_region(e.x, e.y)
        if region == 'cell' and self.tree.identify_column(e.x) == '#5':
            item = self.tree.identify_row(e.y)
            if item:
                vals = self.tree.item(item,'values')
                if vals and vals[0] in self.items:
                    self._show_item_actions(vals[0], e.x_root, e.y_root)
    
    def _show_item_actions(self, art, x, y):
        m = tk.Menu(self, tearoff=0)
        m.add_command(label="+1", command=lambda: self._add_to_item(art,1))
        m.add_command(label="+5", command=lambda: self._add_to_item(art,5))
        m.add_command(label="+10", command=lambda: self._add_to_item(art,10))
        m.add_separator()
        m.add_command(label="Установить", command=lambda: self._set_item_quantity(art))
        m.add_separator()
        m.add_command(label="Удалить", command=lambda: self._remove_item(art))
        m.post(x,y)
    
    def _add_to_item(self, art, amt):
        if art in self.items:
            self.items[art].add(amt)
            self._update_table()
            self._set_active_row(art)
    
    def _set_item_quantity(self, art):
        if art in self.items:
            i = self.items[art]
            d = tk.Toplevel(self)
            d.title("Установить количество")
            d.geometry("300x220")
            d.transient(self)
            d.grab_set()
            ttk.Label(d, text=i.name, wraplength=280).pack(pady=10)
            ttk.Label(d, text=f"Текущее: {i.quantity}").pack()
            ttk.Label(d, text="Новое количество:").pack(pady=(10,0))
            q_var = tk.StringVar(value=str(i.quantity))
            e = ttk.Entry(d, textvariable=q_var, font=('Arial',12))
            e.pack(pady=5)
            e.focus()
            e.select_range(0,tk.END)
            def ok():
                try:
                    i.quantity = float(q_var.get().replace(',','.'))
                    if i.quantity < 0:
                        messagebox.showwarning("Ошибка", "Количество не может быть отрицательным")
                        return
                    self._update_table()
                    d.destroy()
                except:
                    messagebox.showerror("Ошибка", "Введите число")
            ttk.Button(d, text="OK", command=ok, width=10).pack(pady=10)
            e.bind('<Return>', lambda e: ok())
    
    def _remove_item(self, art):
        if art in self.items:
            name = self.items[art].name
            if messagebox.askyesno("Удалить", f"Удалить '{name[:50]}'?"):
                del self.items[art]
                if self.active_article == art:
                    self.active_article = None
                self._update_table()
    
    def _clear_all(self):
        if self.items and messagebox.askyesno("Подтверждение", "Очистить весь список?"):
            self.items.clear()
            self.active_article = None
            self._update_table()
            self.status_label.config(text="Список очищен")
            self.after(2000, lambda: self.status_label.config(text="Готов к подсчету"))
    
    def _update_table(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for art, it in sorted(self.items.items(), key=lambda x: x[1].name):
            q = f"{it.quantity:.2f}".rstrip('0').rstrip('.') if '.' in f"{it.quantity:.2f}" else f"{it.quantity:.0f}"
            tags = ('active',) if self.active_article and art == self.active_article else ()
            self.tree.insert('', tk.END, values=(art, it.name[:60], q, it.address or "", "⚙"), tags=tags)
        self.tree.tag_configure('active', background='#ffb74d')
        total = len(self.items)
        total_q = sum(i.quantity for i in self.items.values())
        self.status_label.config(text=f"Позиций: {total} | Общее кол-во: {total_q:.2f}")
    
    def _export_to_excel(self):
        if not self.items:
            messagebox.showwarning("Внимание", "Нет данных")
            return
        folder = self.settings.get_export_folder()
        folder.mkdir(parents=True, exist_ok=True)
        fname = folder / f"count_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        data = [{'Артикул':i.article,'Наименование':i.name,'Количество':i.quantity,'Адрес':i.address or ''} for i in self.items.values()]
        if ExcelExporter.export(data, fname):
            messagebox.showinfo("Успех", f"Сохранен: {fname}")
            if messagebox.askyesno("Открыть папку", "Открыть папку с файлом?"):
                import os; os.startfile(folder)
    
    def _export_to_csv(self):
        if not self.items:
            messagebox.showwarning("Внимание", "Нет данных")
            return
        folder = self.settings.get_export_folder()
        folder.mkdir(parents=True, exist_ok=True)
        fname = folder / f"count_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        data = [{'Артикул':i.article,'Наименование':i.name,'Количество':i.quantity,'Адрес':i.address or ''} for i in self.items.values()]
        if CSVExporter.export(data, fname):
            messagebox.showinfo("Успех", f"Сохранен: {fname}")
            if messagebox.askyesno("Открыть папку", "Открыть папку с файлом?"):
                import os; os.startfile(folder)