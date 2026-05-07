# gui/tabs/inventory_tab.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from PIL import Image, ImageTk

from gui.widgets.article_entry import ArticleEntry
from core.nomenclature import NomenclatureDB
from core.address_manager import AddressDB
from core.inventory_parser import InventoryParser
from models.inventory_item import InventoryItem
from exporters.excel_exporter import ExcelExporter
from exporters.csv_exporter import CSVExporter
from utils.article_normalizer import ArticleNormalizer
from commands import CommandHandler

logger = logging.getLogger(__name__)

class InventoryTab(ttk.Frame):
    def __init__(self, parent, nomenclature, addresses, settings):
        super().__init__(parent)
        self.nomenclature = nomenclature
        self.addresses = addresses
        self.settings = settings
        self.items: Dict[str, InventoryItem] = {}
        self.current_file_path: Optional[Path] = None
        self.auto_mode = tk.BooleanVar(value=self.settings.is_auto_add())
        self.auto_manual_unit = tk.BooleanVar(value=self.settings.get('behavior.auto_manual_unit', True))
        self.show_only_mismatch = tk.BooleanVar(value=False)
        self.last_article = None
        self.active_article = None
        self._create_widgets()
        self._update_table()

    def _create_widgets(self):
        load_frame = ttk.LabelFrame(self, text="Загрузка ведомости", padding="10")
        load_frame.pack(fill=tk.X, padx=5, pady=5)
        load_buttons = ttk.Frame(load_frame)
        load_buttons.pack(fill=tk.X)
        ttk.Button(load_buttons, text="📂 Загрузить ведомость", command=self._load_inventory_file, width=18).pack(side=tk.LEFT, padx=2)
        ttk.Button(load_buttons, text="🔄 Очистить данные", command=self._clear_inventory, width=14).pack(side=tk.LEFT, padx=2)
        ttk.Button(load_buttons, text="✅ Завершить и сохранить", command=self._finish_inventory, width=18).pack(side=tk.LEFT, padx=2)
        self.file_label = ttk.Label(load_frame, text="Файл не загружен", foreground="gray")
        self.file_label.pack(anchor=tk.W, pady=(10,0))

        input_frame = ttk.LabelFrame(self, text="Сканирование товаров", padding="10")
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        self.article_entry = ArticleEntry(input_frame, on_submit_callback=self._on_article_submit)
        self.article_entry.pack(fill=tk.X)

        quick_buttons = ttk.Frame(input_frame)
        quick_buttons.pack(fill=tk.X, pady=(10,0))
        ttk.Button(quick_buttons, text="Установить количество", command=self._set_last_quantity, width=15).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_buttons, text="🖨️", command=self._open_print_window, width=3).pack(side=tk.RIGHT, padx=2)
        #self.last_item_label = ttk.Label(quick_buttons, text="", foreground="blue")
        self.last_item_label = tk.Label(quick_buttons, text="", font=('Arial', 20, 'bold'), fg='#000000', bg='#ffffff', relief=tk.SUNKEN, padx=5)
        self.last_item_label.pack(side=tk.RIGHT, padx=10)

        table_frame = ttk.LabelFrame(self, text="Результаты инвентаризации", padding="5")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        columns = ('article','name','expected','actual','diff','address','status')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        for c in columns:
            self.tree.heading(c, text={'article':'Артикул','name':'Наименование','expected':'Ожидаемый','actual':'Фактический','diff':'Разница','address':'Адрес','status':'Статус'}[c])
        self.tree.column('article',width=150)
        self.tree.column('name',width=400)
        self.tree.column('expected',width=80,anchor=tk.CENTER)
        self.tree.column('actual',width=80,anchor=tk.CENTER)
        self.tree.column('diff',width=80,anchor=tk.CENTER)
        self.tree.column('address',width=100)
        self.tree.column('status',width=150)
        v_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.tree.grid(row=0,column=0,sticky='nsew')
        v_scroll.grid(row=0,column=1,sticky='ns')
        h_scroll.grid(row=1,column=0,sticky='ew')
        table_frame.grid_rowconfigure(0,weight=1)
        table_frame.grid_columnconfigure(0,weight=1)
        self.tree.bind('<Button-3>', self._on_tree_right_click)

        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)
        stats_frame = ttk.LabelFrame(bottom_frame, text="Статистика", padding="5")
        stats_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        self.stats_label = ttk.Label(stats_frame, text="Загрузите ведомость")
        self.stats_label.pack(anchor=tk.W)
        export_frame = ttk.Frame(bottom_frame)
        export_frame.pack(side=tk.RIGHT)
        ttk.Button(export_frame, text="📊 Excel", command=self._export_report_excel, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(export_frame, text="📄 CSV", command=self._export_report_csv, width=10).pack(side=tk.LEFT, padx=2)

        self.status_label = ttk.Label(self, text="Готов к работе", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, padx=5, pady=5)

    def _get_row_tag(self, item: InventoryItem) -> str:
        if item.actual == item.expected:
            return 'match'
        elif item.actual < item.expected:
            return 'shortage'
        else:
            return 'surplus'

    def _set_active_row(self, article: str):
        if self.active_article:
            for item_id in self.tree.get_children():
                vals = self.tree.item(item_id, 'values')
                if vals and vals[0] == self.active_article:
                    old_item = self.items.get(self.active_article)
                    if old_item:
                        self.tree.item(item_id, tags=(self._get_row_tag(old_item),))
                    break
        self.active_article = article
        for item_id in self.tree.get_children():
            vals = self.tree.item(item_id, 'values')
            if vals and vals[0] == article:
                current_tags = list(self.tree.item(item_id, 'tags'))
                if 'active' in current_tags:
                    current_tags.remove('active')
                current_tags.append('active')
                self.tree.item(item_id, tags=current_tags)
                self.tree.see(item_id)
                break

    def _load_inventory_file(self):
        fp = filedialog.askopenfilename(title="Выберите ведомость", filetypes=[("Excel","*.xlsx *.xls")])
        if not fp:
            return
        self.status_label.config(text="Загрузка...")
        self.update_idletasks()
        try:
            parser = InventoryParser()
            positions = parser.parse_inventory_file(fp)
            if not positions:
                messagebox.showwarning("Ошибка", "Не найдено позиций")
                return
            self.items.clear()
            for p in positions:
                art = p['article']
                prod = self.nomenclature.find_by_article_or_barcode(art)
                name = p['name'] or (prod.name if prod else "Неизвестно")
                addr = self.addresses.get_address(art)
                self.items[art] = InventoryItem(art, name, p['expected'], 0, addr, p.get('source_row',0))
            self.current_file_path = Path(fp)
            self.file_label.config(text=f"Загружен: {self.current_file_path.name} ({len(self.items)})", foreground="green")
            self._update_table()
            self._update_stats()
            self.status_label.config(text=f"✓ Загружено {len(self.items)} позиций", foreground="green")
            self.after(3000, lambda: self.status_label.config(foreground="black"))
            self.article_entry.focus()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _clear_inventory(self):
        if self.items and messagebox.askyesno("Подтверждение", "Очистить данные?"):
            self.items.clear()
            self.current_file_path = None
            self.active_article = None
            self.file_label.config(text="Файл не загружен", foreground="gray")
            self._update_table()
            self._update_stats()

    def _get_unit_for_article(self, article: str) -> str:
        prod = self.nomenclature.find_by_article_or_barcode(article)
        if prod and hasattr(prod, 'unit'):
            return prod.unit
        return 'шт'

    def _on_article_submit(self, code: str, is_command: bool = False):
        if is_command:
            self._handle_command(code)
            return

        if not self.items:
            messagebox.showwarning("Внимание", "Сначала загрузите ведомость")
            self.article_entry.clear()
            return

        norm = ArticleNormalizer.normalize(code)
        item = None
        found_article = None
        for art, inv in self.items.items():
            if norm == ArticleNormalizer.normalize(art):
                item = inv
                found_article = art
                break

        if not item:
            product = self.nomenclature.find_by_article_or_barcode(code)
            if product:
                msg = f"Позиция отсутствует в ведомости!\n\nАртикул: {product.article}\nНаименование: {product.name}"
                messagebox.showwarning("Отсутствует в ведомости", msg)
                self.status_label.config(text=f"⚠ {product.name[:40]} - отсутствует в ведомости", foreground="orange")
            else:
                msg = f"Позиция отсутствует в ведомости!\n\nКод: {code}\nТовар не найден в базе номенклатуры"
                messagebox.showwarning("Отсутствует в ведомости", msg)
                self.status_label.config(text=f"✗ Код '{code}' не найден в базе и ведомости", foreground="red")
            self.article_entry.clear()
            return

        self.last_article = found_article
        self._update_last_item_label()
        self._set_active_row(item.article)

        if item.expected == 0:
            self.status_label.config(
                text=f"⚠ ВНИМАНИЕ: '{item.name[:40]}' ожидаемый остаток = 0 (позиции нет на складе)",
                foreground="orange"
            )
            self.after(3000, lambda: self.status_label.config(foreground="black"))

        if self.auto_mode.get():
            unit = self._get_unit_for_article(item.article)
            if self.auto_manual_unit.get() and unit and unit.lower() != 'шт':
                self._show_quantity_dialog(item)
            else:
                if item.actual == 0:
                    item.actual = 1.0
                else:
                    item.actual = item.actual + 1.0
                self._update_table()
                self._update_stats()
                self._update_last_item_label()
                self.status_label.config(
                    text=f"✓ {item.name[:40]} +1 (факт:{item.actual:.0f}/ожид:{item.expected:.0f})",
                    foreground="green"
                )
                self.after(2000, lambda: self.status_label.config(foreground="black"))
        else:
            self._show_quantity_dialog(item)

        self.article_entry.clear()

    def _update_last_item_label(self):
        if self.last_article and self.last_article in self.items:
            item = self.items[self.last_article]
            self.last_item_label.config(text=f"{item.article} | {item.name[:50]} | {item.actual:.0f}шт.")
        else:
            self.last_item_label.config(text="")

    def _open_print_window(self):
        if not self.last_article or self.last_article not in self.items:
            messagebox.showwarning("Внимание", "Нет последнего отсканированного товара")
            return
        item = self.items[self.last_article]
        PrintDialog(self, item, self.nomenclature, self.addresses, self.settings)

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
            self._reset_actual()
        elif cmd == 'CMD_START_INV':
            self._start_inventory()
        elif cmd == 'CMD_FINISH_INV':
            self._finish_inventory()
        elif cmd == 'CMD_MANUAL_NEXT':
            self._manual_next()
        elif cmd == 'CMD_MANUAL_LAST':
            self._manual_last()
        elif cmd == 'CMD_ZERO_LAST':
            self._zero_last()
        elif cmd == 'CMD_SHOW_LAST':
            self._show_last()
        elif cmd == 'CMD_SHOW_EXPECTED':
            self._show_expected()
        elif cmd == 'CMD_SHOW_STATS':
            self._show_stats()
        self.article_entry.clear()
        self.article_entry.focus()

    def _add_to_last(self, amt):
        if self.last_article and self.last_article in self.items:
            item = self.items[self.last_article]
            item.add(amt)
            self._update_table()
            self._update_stats()
            self._set_active_row(self.last_article)
            self._update_last_item_label()
            self.status_label.config(text=f"✓ +{amt} к {item.name[:30]} ({item.actual:.0f})", foreground="green")
            self.after(2000, lambda: self.status_label.config(foreground="black"))
        else:
            messagebox.showinfo("Инфо", "Сначала отсканируйте товар")

    def _set_last_quantity(self):
        if self.last_article and self.last_article in self.items:
            self._set_active_row(self.last_article)
            self._show_quantity_dialog(self.items[self.last_article], set_mode=True)
        else:
            messagebox.showinfo("Инфо", "Сначала отсканируйте товар")

    def _show_quantity_dialog(self, item: InventoryItem, set_mode: bool = False):
        d = tk.Toplevel(self)
        d.title("Ввод количества")
        d.geometry("450x350")
        d.transient(self)
        d.grab_set()
        d.update_idletasks()
        x = self.winfo_x() + self.winfo_width()//2 - 225
        y = self.winfo_y() + self.winfo_height()//2 - 175
        d.geometry(f"+{x}+{y}")
        ttk.Label(d, text=item.name, font=('Arial',10,'bold'), wraplength=400).pack(pady=10)
        ttk.Label(d, text=f"Артикул: {item.article}").pack()
        ttk.Label(d, text=f"Ожидаемый: {item.expected:.2f}").pack()
        ttk.Label(d, text=f"Текущий: {item.actual:.2f}").pack()
        ttk.Label(d, text="Количество:").pack(pady=(10,0))
        q_var = tk.StringVar(value=str(item.actual if set_mode else 1))
        e = ttk.Entry(d, textvariable=q_var, font=('Arial',14), width=15)
        e.pack(pady=5)
        e.focus()
        e.select_range(0,tk.END)
        btn_frame = ttk.Frame(d)
        btn_frame.pack(pady=10)
        for v in [1,5,10,20,50,100]:
            ttk.Button(btn_frame, text=str(v), width=5, command=lambda val=v: q_var.set(str(val))).pack(side=tk.LEFT, padx=2)
        def ok():
            try:
                q = float(q_var.get().replace(',','.'))
                if q < 0:
                    messagebox.showwarning("Ошибка", "Количество не может быть отрицательным")
                    return
                if set_mode:
                    item.actual = q
                else:
                    item.add(q)
                self._update_table()
                self._update_stats()
                self._update_last_item_label()
                d.destroy()
            except:
                messagebox.showerror("Ошибка", "Введите число")
        ttk.Button(d, text="OK", command=ok, width=10).pack(pady=5)
        ttk.Button(d, text="Отмена", command=d.destroy, width=10).pack()
        e.bind('<Return>', lambda e: ok())

    def _reset_actual(self):
        if messagebox.askyesno("Подтверждение", "Сбросить ВСЕ фактические остатки?"):
            for i in self.items.values():
                i.actual = 0
            self._update_table()
            self._update_stats()

    def _start_inventory(self):
        if not self.items:
            messagebox.showwarning("Внимание", "Загрузите ведомость")
            return
        for i in self.items.values():
            i.actual = 0
        self.last_article = None
        self.active_article = None
        self._update_table()
        self._update_stats()
        self.status_label.config(text="✓ Инвентаризация начата", foreground="green")
        self.after(2000, lambda: self.status_label.config(foreground="black"))

    def _finish_inventory(self):
        if not self.items:
            messagebox.showwarning("Внимание", "Нет данных для сохранения")
            return
        
        if not self.current_file_path:
            messagebox.showwarning("Внимание", "Не загружена ведомость")
            return
        
        total, matched = len(self.items), sum(1 for i in self.items.values() if i.actual == i.expected)
        
        if not messagebox.askyesno("Завершить", f"Всего: {total}\nСовпало: {matched}\nСохранить отчет?"):
            return
        
        from shutil import copy2
        import xlrd
        import xlwt
        
        save_path = filedialog.asksaveasfilename(
            title="Сохранить отчет как",
            defaultextension=".xls",
            filetypes=[("Excel files", "*.xls"), ("All files", "*.*")],
            initialfile=f"inventory_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xls"
        )
        
        if not save_path:
            return
        
        try:
            copy2(self.current_file_path, save_path)
            
            rb = xlrd.open_workbook(save_path, formatting_info=False)
            src_sheet = rb.sheet_by_index(0)
            
            wb = xlwt.Workbook()
            ws = wb.add_sheet(src_sheet.name)
            
            for r in range(src_sheet.nrows):
                for c in range(src_sheet.ncols):
                    ws.write(r, c, src_sheet.cell_value(r, c))
            
            header_row = None
            for r in range(min(30, src_sheet.nrows)):
                row_str = ' '.join([str(src_sheet.cell_value(r, c)).lower() for c in range(src_sheet.ncols) if src_sheet.cell_value(r, c)])
                if 'номенклатура.артикул' in row_str or 'артикул' in row_str:
                    header_row = r
                    break
            
            if header_row is None:
                messagebox.showerror("Ошибка", "Не найдена строка заголовков")
                return
            
            col_article = None
            col_article2 = None
            
            for c in range(src_sheet.ncols):
                val = str(src_sheet.cell_value(header_row, c)).lower().replace(' ', '').replace('_', '').replace('.', '')
                if 'номенклатураартикул2' in val or 'артикул2' in val:
                    col_article2 = c
                elif 'артикул' in val and 'номенклатура' not in val and 'артикул2' not in val:
                    col_article = c
            
            col_actual = src_sheet.ncols
            ws.write(header_row, col_actual, "Факт")
            
            green = xlwt.easyxf('pattern: pattern solid, fore_colour light_green;')
            red = xlwt.easyxf('pattern: pattern solid, fore_colour red;')
            yellow = xlwt.easyxf('pattern: pattern solid, fore_colour yellow;')
            
            updated = 0
            for r in range(header_row + 1, src_sheet.nrows):
                article = None
                if col_article2 is not None:
                    val = src_sheet.cell_value(r, col_article2)
                    if val:
                        article = str(val).strip()
                if not article and col_article is not None:
                    val = src_sheet.cell_value(r, col_article)
                    if val:
                        article = str(val).strip()
                
                if article and article in self.items:
                    item = self.items[article]
                    updated += 1
                    if item.actual == item.expected:
                        ws.write(r, col_actual, item.actual, green)
                    elif item.actual < item.expected:
                        ws.write(r, col_actual, item.actual, red)
                    else:
                        ws.write(r, col_actual, item.actual, yellow)
            
            wb.save(save_path)
            messagebox.showinfo("Успех", f"Отчет сохранен: {save_path}\nОбновлено позиций: {updated}")
            
            if messagebox.askyesno("Открыть папку", "Открыть папку с файлом?"):
                import os
                os.startfile(str(Path(save_path).parent))
                
        except Exception as e:
            logger.error(f"Ошибка сохранения: {e}", exc_info=True)
            messagebox.showerror("Ошибка", f"Не удалось сохранить отчет:\n{str(e)}")
            
    def _manual_next(self):
        if not self.items:
            return
        unscanned = [a for a,i in self.items.items() if i.actual==0]
        if unscanned:
            self.last_article = unscanned[0]
            self._set_active_row(self.last_article)
            self._show_quantity_dialog(self.items[self.last_article])
        else:
            messagebox.showinfo("Готово", "Все позиции отсканированы")

    def _manual_last(self):
        if self.last_article and self.last_article in self.items:
            self._set_active_row(self.last_article)
            self._show_quantity_dialog(self.items[self.last_article])

    def _zero_last(self):
        if self.last_article and self.last_article in self.items:
            self.items[self.last_article].actual = 0
            self._update_table()
            self._update_stats()
            self._update_last_item_label()

    def _show_last(self):
        if self.last_article and self.last_article in self.items:
            i = self.items[self.last_article]
            messagebox.showinfo("Последний", f"{i.name}\nОжидаемый: {i.expected}\nФактический: {i.actual}")

    def _show_expected(self):
        if self.last_article and self.last_article in self.items:
            i = self.items[self.last_article]
            messagebox.showinfo("Ожидаемый", f"{i.name}\nОстаток: {i.expected}")

    def _show_stats(self):
        if not self.items:
            return
        total, matched = len(self.items), sum(1 for i in self.items.values() if i.actual == i.expected)
        shortage = sum(1 for i in self.items.values() if i.actual < i.expected)
        surplus = sum(1 for i in self.items.values() if i.actual > i.expected)
        exp_sum = sum(i.expected for i in self.items.values())
        act_sum = sum(i.actual for i in self.items.values())
        messagebox.showinfo("Статистика", f"Всего: {total}\nСовпало: {matched}\nНедосдача: {shortage}\nИзлишек: {surplus}\n\nСумма ожид: {exp_sum:.2f}\nСумма факт: {act_sum:.2f}\nРазница: {act_sum-exp_sum:+.2f}")

    def _add_to_item(self, art, amt):
        if art in self.items:
            self.items[art].add(amt)
            self._update_table()
            self._update_stats()

    def _set_item_quantity(self, art):
        if art in self.items:
            self._show_quantity_dialog(self.items[art], True)

    def _remove_item(self, art):
        if art in self.items and messagebox.askyesno("Удалить", f"Удалить {self.items[art].name}?"):
            del self.items[art]
            if self.active_article == art:
                self.active_article = None
            self._update_table()
            self._update_stats()

    def _on_tree_right_click(self, e):
        item = self.tree.identify_row(e.y)
        if item:
            self.tree.selection_set(item)
            vals = self.tree.item(item,'values')
            if vals and vals[0] in self.items:
                self._show_item_menu(vals[0], e.x_root, e.y_root)

    def _show_item_menu(self, art, x, y):
        m = tk.Menu(self, tearoff=0)
        m.add_command(label="+1", command=lambda: self._add_to_item(art,1))
        m.add_command(label="+5", command=lambda: self._add_to_item(art,5))
        m.add_command(label="+10", command=lambda: self._add_to_item(art,10))
        m.add_separator()
        m.add_command(label="Установить кол-во", command=lambda: self._set_item_quantity(art))
        m.add_separator()
        m.add_command(label="Удалить", command=lambda: self._remove_item(art))
        m.post(x,y)

    def _update_table(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        items = list(self.items.values())
        if self.show_only_mismatch.get():
            items = [i for i in items if i.actual != i.expected]
        items.sort(key=lambda x: (x.actual==x.expected, x.name))
        for i in items:
            exp = f"{i.expected:.2f}".rstrip('0').rstrip('.') if '.' in f"{i.expected:.2f}" else f"{i.expected:.0f}"
            act = f"{i.actual:.2f}".rstrip('0').rstrip('.') if '.' in f"{i.actual:.2f}" else f"{i.actual:.0f}"
            diff = f"{i.diff:+.2f}".rstrip('0').rstrip('.') if '.' in f"{i.diff:.2f}" else f"{i.diff:+.0f}"
            tag = self._get_row_tag(i)
            tags = [tag]
            if self.active_article and i.article == self.active_article:
                tags.append('active')
            item_id = self.tree.insert('', tk.END, values=(i.article,i.name[:80],exp,act,diff,i.address or "",i.status), tags=tags)
            if self.active_article and i.article == self.active_article:
                self.tree.see(item_id)
        self.tree.tag_configure('match', background='#e8f5e9')
        self.tree.tag_configure('shortage', background='#fff3e0')
        self.tree.tag_configure('surplus', background='#e3f2fd')
        self.tree.tag_configure('active', background='#ffb74d')

    def _update_stats(self):
        if not self.items:
            self.stats_label.config(text="Нет данных")
            return
        total = len(self.items)
        matched = sum(1 for i in self.items.values() if i.actual==i.expected)
        shortage = sum(1 for i in self.items.values() if i.actual<i.expected)
        surplus = sum(1 for i in self.items.values() if i.actual>i.expected)
        self.stats_label.config(text=f"Всего:{total} ✓:{matched} ⚠:{shortage} ➕:{surplus}")
        exp_sum = sum(i.expected for i in self.items.values())
        act_sum = sum(i.actual for i in self.items.values())
        self.status_label.config(text=f"Ожид:{exp_sum:.2f} Факт:{act_sum:.2f} Разн:{act_sum-exp_sum:+.2f}")

    def _export_report_excel(self):
        if not self.items:
            return
        folder = self.settings.get_export_folder()
        folder.mkdir(parents=True, exist_ok=True)
        fname = folder / f"inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        data = [{'Артикул':i.article,'Наименование':i.name,'Ожидаемый':i.expected,'Фактический':i.actual,'Разница':i.diff,'Адрес':i.address or '','Статус':i.status} for i in self.items.values()]
        if ExcelExporter.export(data, fname):
            messagebox.showinfo("Успех", f"Сохранен: {fname}")

    def _export_report_csv(self):
        if not self.items:
            return
        folder = self.settings.get_export_folder()
        folder.mkdir(parents=True, exist_ok=True)
        fname = folder / f"inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        data = [{'Артикул':i.article,'Наименование':i.name,'Ожидаемый':i.expected,'Фактический':i.actual,'Разница':i.diff,'Адрес':i.address or '','Статус':i.status} for i in self.items.values()]
        if CSVExporter.export(data, fname):
            messagebox.showinfo("Успех", f"Сохранен: {fname}")


class PrintDialog(tk.Toplevel):
    def __init__(self, parent, item, nomenclature, addresses, settings):
        super().__init__(parent)
        self.parent = parent
        self.item = item
        self.nomenclature = nomenclature
        self.addresses = addresses
        self.settings = settings
        self.title("Печать")
        self.geometry("800x700")
        self.transient(parent)
        self.grab_set()
        
        from modules.sticker_generator import StickerGenerator
        from modules.config_manager import ConfigManager
        from modules.address_manager import AddressManager
        
        self.config = ConfigManager()
        self.sticker_gen = StickerGenerator(self.config)
        self.addr_mgr = AddressManager(self.config)
        self.addr_mgr.load_addresses()
        
        self.preset_var = tk.StringVar()
        self.presets = self._load_presets()
        
        self.article_var = tk.StringVar(value=item.article)
        self.name_var = tk.StringVar(value=item.name)
        self.address_var = tk.StringVar(value=item.address or "")
        self.quantity_var = tk.StringVar(value=str(int(item.actual)) if item.actual == int(item.actual) else str(item.actual))
        self.unit_var = tk.StringVar(value="шт")
        
        self.preview_image = None
        self.preview_photo = None
        
        self._create_widgets()
        self._load_last_preset()
        self._update_preview()
    
    def _load_presets(self):
        import json
        presets = {}
        p = Path.home() / "AppData" / "Local" / "StickerMakerV3" / "presets.json"
        if p.exists():
            try:
                presets = json.loads(p.read_text(encoding='utf-8'))
            except:
                pass
        if not presets:
            presets = {"Стандартный": {}}
        return presets
    
    def _load_last_preset(self):
        last = self.settings.get('print.last_preset', '')
        if last in self.presets:
            self.preset_var.set(last)
        elif self.presets:
            self.preset_var.set(list(self.presets.keys())[0])
    
    def _save_last_preset(self):
        self.settings.set('print.last_preset', self.preset_var.get())
    
    def _create_widgets(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill=tk.BOTH, expand=True)
        
        preset_frame = ttk.LabelFrame(main, text="Пресеты", padding=5)
        preset_frame.pack(fill=tk.X, pady=(0,10))
        pf = ttk.Frame(preset_frame)
        pf.pack(fill=tk.X)
        ttk.Label(pf, text="Пресет:").pack(side=tk.LEFT)
        self.preset_combo = ttk.Combobox(pf, textvariable=self.preset_var, 
                                          values=list(self.presets.keys()), state='readonly', width=20)
        self.preset_combo.pack(side=tk.LEFT, padx=5)
        ttk.Button(pf, text="Обновить", command=self._update_preview).pack(side=tk.LEFT, padx=2)
        ttk.Button(pf, text="Сохранить", command=self._save_current_preset).pack(side=tk.LEFT, padx=2)
        ttk.Button(pf, text="Печать", command=self._print).pack(side=tk.RIGHT, padx=5)
        
        fields = ttk.LabelFrame(main, text="Данные", padding=5)
        fields.pack(fill=tk.X, pady=(0,10))
        ff = ttk.Frame(fields)
        ff.pack(fill=tk.X)
        
        ttk.Label(ff, text="Артикул:").grid(row=0, column=0, sticky=tk.W, padx=5)
        e1 = ttk.Entry(ff, textvariable=self.article_var, width=20)
        e1.grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Button(ff, text="🔍", command=self._search_article, width=3).grid(row=0, column=2, padx=2)
        
        ttk.Label(ff, text="Название:").grid(row=1, column=0, sticky=tk.W, padx=5)
        e2 = ttk.Entry(ff, textvariable=self.name_var, width=50)
        e2.grid(row=1, column=1, columnspan=2, sticky=tk.W, padx=5)
        ttk.Button(ff, text="🔍", command=self._search_name, width=3).grid(row=1, column=3, padx=2)
        
        ttk.Label(ff, text="Адрес:").grid(row=2, column=0, sticky=tk.W, padx=5)
        e3 = ttk.Entry(ff, textvariable=self.address_var, width=15)
        e3.grid(row=2, column=1, sticky=tk.W, padx=5)
        ttk.Button(ff, text="🔍", command=self._search_address, width=3).grid(row=2, column=2, padx=2)
        
        ttk.Label(ff, text="Кол-во:").grid(row=2, column=3, sticky=tk.W, padx=(20,5))
        ttk.Entry(ff, textvariable=self.quantity_var, width=8).grid(row=2, column=4, sticky=tk.W, padx=5)
        ttk.Label(ff, text="Ед.:").grid(row=2, column=5, sticky=tk.W, padx=5)
        ttk.Combobox(ff, textvariable=self.unit_var, values=["шт", "кг", "м", "л", "уп"], width=5).grid(row=2, column=6, sticky=tk.W)
        
        preview_frame = ttk.LabelFrame(main, text="Предпросмотр", padding=5)
        preview_frame.pack(fill=tk.BOTH, expand=True)
        self.preview_canvas = tk.Canvas(preview_frame, bg='white', highlightthickness=1)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        for v in [self.article_var, self.name_var, self.address_var, self.quantity_var, self.unit_var]:
            v.trace('w', lambda *a: self._update_preview())
    
    def _save_current_preset(self):
        d = tk.Toplevel(self)
        d.title("Сохранить пресет")
        d.geometry("300x120")
        d.transient(self)
        d.grab_set()
        ttk.Label(d, text="Имя пресета:").pack(pady=5)
        name_var = tk.StringVar()
        e = ttk.Entry(d, textvariable=name_var, width=30)
        e.pack(pady=5)
        e.focus()
        def save():
            name = name_var.get().strip()
            if name:
                self.presets[name] = {}
                self._save_presets()
                self.preset_combo['values'] = list(self.presets.keys())
                self.preset_var.set(name)
                self._save_last_preset()
                d.destroy()
        ttk.Button(d, text="Сохранить", command=save).pack(pady=5)
    
    def _save_presets(self):
        import json
        p = Path.home() / "AppData" / "Local" / "StickerMakerV3" / "presets.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.presets, ensure_ascii=False), encoding='utf-8')
    
    def _update_preview(self):
        try:
            qty = float(self.quantity_var.get().replace(',', '.')) if self.quantity_var.get() else None
        except:
            qty = None
        
        img = self.sticker_gen.generate_simple_preview(
            article=self.article_var.get(),
            name=self.name_var.get(),
            quantity=qty,
            unit=self.unit_var.get() if qty else None,
            address=self.address_var.get() if self.address_var.get() else None
        )
        self.preview_image = img
        
        # Масштабирование под размер канваса
        canvas_w = self.preview_canvas.winfo_width()
        canvas_h = self.preview_canvas.winfo_height()
        if canvas_w > 10 and canvas_h > 10:
            scale = min(canvas_w / img.width, canvas_h / img.height) * 0.9
            new_w, new_h = int(img.width * scale), int(img.height * scale)
            if new_w > 10 and new_h > 10:
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        self.preview_photo = ImageTk.PhotoImage(img)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(self.preview_canvas.winfo_width()//2, self.preview_canvas.winfo_height()//2, 
                                          anchor=tk.CENTER, image=self.preview_photo)
    
    def _print(self):
        if not self.preview_image:
            return
        import os
        tf = Path.home() / "AppData" / "Local" / "Temp" / f"sticker_print_{int(datetime.now().timestamp())}.png"
        self.preview_image.save(tf, 'PNG')
        os.startfile(str(tf), "print")
        self._save_last_preset()
        self.destroy()
    
    def _search_article(self):
        art = self.article_var.get().strip()
        if not art:
            return
        prod = self.nomenclature.find_by_article_or_barcode(art)
        if prod:
            self.name_var.set(prod.name)
            addr = self.addresses.get_address(prod.article)
            if addr:
                self.address_var.set(addr)
        else:
            messagebox.showwarning("Не найдено", f"Артикул '{art}' не найден")
    
    def _search_name(self):
        name = self.name_var.get().strip()
        if not name or len(name) < 3:
            return
        for prod in self.nomenclature.products.values():
            if name.lower() in prod.name.lower():
                self.article_var.set(prod.article)
                self.name_var.set(prod.name)
                addr = self.addresses.get_address(prod.article)
                if addr:
                    self.address_var.set(addr)
                return
        messagebox.showwarning("Не найдено", f"Название '{name[:30]}...' не найдено")
    
    def _search_address(self):
        addr = self.address_var.get().strip()
        if not addr:
            return
        for art, a in self.addresses.addresses.items():
            if addr.lower() in a.lower():
                self.article_var.set(art)
                self.address_var.set(a)
                prod = self.nomenclature.find_by_article_or_barcode(art)
                if prod:
                    self.name_var.set(prod.name)
                return