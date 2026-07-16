# --- gui/print_queue.py ---
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
import logging
from typing import Any, List, Dict, Optional
import customtkinter as ctk
from tkinter import ttk
import tkinter as tk
from services.interfaces import IPrinterService, ISettingsService
from libs.domain_models import Product
logger = logging.getLogger(__name__)
class PrintQueue(ctk.CTkFrame):
	def __init__(self, master: Any, printer_service: IPrinterService, settings_service: ISettingsService):
		super().__init__(master)
		self._printer_service = printer_service
		self._settings_service = settings_service
		self._products: List[Product] = []
		self._copy_counts: Dict[str, int] = {}
		self._next_item_id = 1
		self._column_config = {'visible': ['article', 'article2', 'name', 'address'], 'order': ['article', 'article2', 'name', 'address']}
		self._create_header()
		self._create_table()
		self._load_column_settings()
	def _create_header(self) -> None:
		header_frame = ctk.CTkFrame(self, fg_color="transparent")
		header_frame.pack(fill="x", padx=3, pady=3)
		ctk.CTkButton(header_frame, text="⋮ Столбцы", width=80, command=self._toggle_column_menu).pack(side="right", padx=5)
		ctk.CTkButton(header_frame, text="📥 Импорт", width=90, command=self._import_from_file).pack(side="right", padx=5)
		ctk.CTkButton(header_frame, text="🖨️ Печать", width=80, command=self._print_all).pack(side="right", padx=5)
		btn_clear = ctk.CTkButton(header_frame, text="❌", width=40, height=28, fg_color="#d32f2f", hover_color="#b71c1c", command=self._clear_all)
		btn_clear.pack(side="right", padx=5)
		self._column_menu = ctk.CTkFrame(header_frame, fg_color="#2b2b2b")
	def _apply_treeview_theme(self) -> None:
		try:
			style = ttk.Style()
			if 'clam' in style.theme_names():
				style.theme_use('clam')
			style.configure("Treeview",
				background="white", foreground="black", fieldbackground="white",
				borderwidth=1, relief="solid", rowheight=32, font=("Arial", 12))
			style.configure("Treeview.Heading",
				borderwidth=1, relief="solid", background="#E0E0E0", font=("Arial", 11, "bold"))
			style.map("Treeview",
				background=[('selected', 'grey')],
				foreground=[('selected', 'white')])
			logger.debug("[PrintQueue] Тема clam применена для Treeview")
		except Exception as e:
			logger.warning(f"[PrintQueue] Не удалось применить тему clam: {e}")
	def _create_table(self) -> None:
		table_frame = ctk.CTkFrame(self)
		table_frame.pack(fill="both", expand=True, padx=3, pady=3)
		columns = ("delete", "num", "decrease", "copies", "article", "article2", "name", "address")
		self._tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
		self._apply_treeview_theme()
		self._tree.tag_configure('oddrow', background='#FFFFFF')
		self._tree.tag_configure('evenrow', background='#F5F5F5')
		self._tree.heading("delete", text="")
		self._tree.heading("num", text="№")
		self._tree.heading("decrease", text=" ")
		self._tree.heading("copies", text="Копии")
		self._tree.heading("article", text="Артикул")
		self._tree.heading("article2", text="Артикул 2")
		self._tree.heading("name", text="Наименование")
		self._tree.heading("address", text="Адрес")
		self._tree.column("delete", width=35, minwidth=30, anchor="center", stretch=False)
		self._tree.column("num", width=40, minwidth=40, anchor="center", stretch=False)
		self._tree.column("decrease", width=20, minwidth=20, anchor="center", stretch=False)
		self._tree.column("copies", width=35, minwidth=35, anchor="center", stretch=False)
		self._tree.column("article", width=200, minwidth=150, stretch=False)
		self._tree.column("article2", width=200, minwidth=150, stretch=False)
		self._tree.column("name", width=550, minwidth=400, stretch=True)
		self._tree.column("address", width=200, minwidth=150, stretch=False)
		v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self._tree.yview)
		h_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self._tree.xview)
		self._tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
		self._tree.grid(row=0, column=0, sticky="nsew")
		v_scroll.grid(row=0, column=1, sticky="ns")
		h_scroll.grid(row=1, column=0, sticky="ew")
		table_frame.grid_rowconfigure(0, weight=1)
		table_frame.grid_columnconfigure(0, weight=1)
		self._tree.bind("<Double-1>", self._on_double_click)
		self._tree.bind("<Button-1>", self._on_tree_click)
	def _load_column_settings(self) -> None:
		config = self._settings_service.get_column_config()
		if config:
			self._column_config = config
			self._apply_column_visibility()
	def _toggle_column_menu(self) -> None:
		logger.info("[PrintQueue] Переключение меню колонок")
	def _apply_column_visibility(self) -> None:
		visible = self._column_config.get('visible', [])
		self._tree.column("delete", width=35, minwidth=30, anchor="center")
		self._tree.column("num", width=40, minwidth=40, anchor="center")
		self._tree.column("decrease", width=20, minwidth=20, anchor="center")
		self._tree.column("copies", width=35, minwidth=35, anchor="center")
		for col in ["article", "article2", "address"]:
			if col in visible:
				self._tree.column(col, width=150, minwidth=90)
			else:
				self._tree.column(col, width=0, minwidth=0, stretch=False)
	def _on_tree_click(self, event) -> None:
		rel_x = event.x
		rel_y = event.y
		selection = self._tree.selection()
		if not selection:
			return
		item_id = selection[0]
		if not self._is_item_valid(item_id):
			return
		column_id = self._tree.identify("column", rel_x, rel_y)
		column = self._column_id_to_name(column_id)
		if column == "delete":
			self._delete_item(item_id)
		elif column == "decrease":
			self._decrease_copy_count(item_id)
		elif column == "copies":
			self._increase_copy_count(item_id)
	def _on_double_click(self, event) -> None:
		abs_x = event.widget.winfo_rootx() + event.x
		abs_y = event.widget.winfo_rooty() + event.y
		rel_x = abs_x - self._tree.winfo_rootx()
		rel_y = abs_y - self._tree.winfo_rooty()
		selection = self._tree.selection()
		if not selection: return
		item_id = selection[0]
		region = self._tree.identify("region", rel_x, rel_y)
		if region != "cell": return
		column_id = self._tree.identify("column", rel_x, rel_y)
		column = self._column_id_to_name(column_id)
		if column in ("#0", "delete", "num", "decrease", "copies", ""): return
		values = self._tree.item(item_id, "values")
		column_index = self._get_column_index(column)
		if column_index == -1: return
		try:
			value = values[column_index] if column_index < len(values) else ""
		except (IndexError, TypeError):
			value = ""
		self._start_inline_edit(item_id, column, value)
	def _column_id_to_name(self, column_id: str) -> str:
		if not column_id or column_id == "#0": return "#0"
		try:
			idx = int(column_id[1:]) - 1
			columns = self._tree["columns"]
			if 0 <= idx < len(columns): return columns[idx]
		except (ValueError, IndexError): pass
		return column_id
	def _get_column_index(self, column: str) -> int:
		columns = ["delete", "num", "decrease", "copies", "article", "article2", "name", "address"]
		return columns.index(column) if column in columns else -1
	def _start_inline_edit(self, item_id: str, column: str, value: str) -> None:
		bbox = self._tree.bbox(item_id, column)
		if not bbox: return
		x, y, width, height = bbox
		edit_entry = ttk.Entry(self._tree, font=("Arial", 11))
		edit_entry.place(x=x, y=y, width=width, height=height)
		edit_entry.insert(0, value)
		edit_entry.focus_set()
		edit_entry.select_range(0, "end")
		def save(event=None):
			new_value = edit_entry.get().strip()
			if new_value and new_value != value:
				values = list(self._tree.item(item_id, "values"))
				column_idx = self._get_column_index(column)
				if 0 <= column_idx < len(values):
					values[column_idx] = new_value
					self._tree.item(item_id, values=values)
					self._update_product_field(item_id, column, new_value)
			edit_entry.destroy()
		def cancel(event=None):
			edit_entry.destroy()
		edit_entry.bind("<Return>", save)
		edit_entry.bind("<FocusOut>", save)
		edit_entry.bind("<Escape>", cancel)
	def _update_product_field(self, item_id: str, column: str, new_value: str) -> None:
		items = self._tree.get_children()
		try:
			item_position = list(items).index(item_id)
		except ValueError:
			logger.warning(f"[PrintQueue] Не найден item_id {item_id} в дереве")
			return
		if not (0 <= item_position < len(self._products)):
			logger.warning(f"[PrintQueue] Индекс {item_position} вне диапазона products")
			return
		product = self._products[item_position]
		if column == "article":
			old_article = product.article
			product.article = new_value
			if product.barcodes and old_article in product.barcodes:
				idx = product.barcodes.index(old_article)
				product.barcodes[idx] = new_value
			logger.debug(f"[PrintQueue] Обновлён article: {old_article} → {new_value}")
		elif column == "article2":
			other_barcodes = [b for b in product.barcodes if b != product.article]
			if other_barcodes:
				idx = product.barcodes.index(other_barcodes[0])
				product.barcodes[idx] = new_value
			else:
				product.barcodes.append(new_value)
			logger.debug(f"[PrintQueue] Обновлён article2: {new_value}")
		elif column == "name":
			product.name = new_value
			logger.debug(f"[PrintQueue] Обновлён name: {new_value}")
		elif column == "address":
			if new_value:
				addresses = [a.strip() for a in new_value.split(",") if a.strip()]
				product.storage_locations = addresses
				product.address = addresses[0] if addresses else None
			else:
				product.storage_locations = []
				product.address = None
			logger.debug(f"[PrintQueue] Обновлён address: {new_value}")
	def _is_item_valid(self, item_id: str) -> bool:
		try:
			return item_id in self._tree.get_children()
		except Exception:
			return False
	def _increase_copy_count(self, item_id: str) -> None:
		if not self._is_item_valid(item_id):
			return
		current = self._copy_counts.get(item_id, 1)
		new_count = current + 1
		self._copy_counts[item_id] = new_count
		values = list(self._tree.item(item_id, "values"))
		if len(values) > 3:
			values[3] = str(new_count)
			self._tree.item(item_id, values=values)
	def _decrease_copy_count(self, item_id: str) -> None:
		if not self._is_item_valid(item_id):
			return
		current = self._copy_counts.get(item_id, 1)
		if current > 1:
			new_count = current - 1
			self._copy_counts[item_id] = new_count
			values = list(self._tree.item(item_id, "values"))
			if len(values) > 3:
				values[3] = str(new_count)
				self._tree.item(item_id, values=values)
	def _delete_item(self, item_id: str) -> None:
		if not self._is_item_valid(item_id):
			return
		logger.info(f"[PrintQueue] Удаление позиции {item_id}")
		items_before = self._tree.get_children()
		item_position = -1
		for idx, iid in enumerate(items_before):
			if iid == item_id:
				item_position = idx
				break
		self._tree.delete(item_id)
		if 0 <= item_position < len(self._products):
			del self._products[item_position]
		if item_id in self._copy_counts:
			del self._copy_counts[item_id]
		self.after(50, self._rebuild_queue)
	def _rebuild_queue(self) -> None:
		items = self._tree.get_children()
		for new_num, item_id in enumerate(items, start=1):
			if not self._is_item_valid(item_id):
				continue
			values = list(self._tree.item(item_id, "values"))
			if len(values) > 1:
				values[1] = str(new_num)
				values[2] = "⟨"
				count = self._copy_counts.get(item_id, 1)
				values[3] = str(count)
				values[0] = "❌"
				tag = 'oddrow' if new_num % 2 else 'evenrow'
				self._tree.item(item_id, values=values, tags=(tag,))
	def add_item(self, product: Product) -> None:
		logger.info(f"[PrintQueue] Добавление товара {product.article} в очередь")
		item_id = str(self._next_item_id)
		self._next_item_id += 1
		article2_val = ""
		other_barcodes = [b for b in product.barcodes if b != product.article]
		if other_barcodes:
			article2_val = other_barcodes[0]
		address_val = ""
		if product.storage_locations:
			address_val = ", ".join(product.storage_locations)
		current_num = len(self._products) + 1
		tag = 'oddrow' if current_num % 2 else 'evenrow'
		values = ("❌", str(current_num), "⟨", "1", product.article, article2_val, product.name, address_val)
		self._tree.insert("", "end", iid=item_id, values=values, tags=(tag,))
		self._products.append(product)
		self._copy_counts[item_id] = 1
	def set_products(self, products: List[Product]) -> None:
		self._products = products
		self._copy_counts.clear()
		self._next_item_id = 1
		logger.info(f"[PrintQueue] Установка {len(products)} товаров в очередь")
		for item in self._tree.get_children():
			self._tree.delete(item)
		for i, product in enumerate(products, start=1):
			article2_val = ""
			other_barcodes = [b for b in product.barcodes if b != product.article]
			if other_barcodes:
				article2_val = other_barcodes[0]
			address_val = ""
			if product.storage_locations:
				address_val = ", ".join(product.storage_locations)
			item_id = str(self._next_item_id)
			self._next_item_id += 1
			tag = 'oddrow' if i % 2 else 'evenrow'
			values = ("❌", str(i), "⟨", "1", product.article, article2_val, product.name, address_val)
			self._tree.insert("", "end", iid=item_id, values=values, tags=(tag,))
			self._copy_counts[item_id] = 1
	def clear(self) -> None:
		self._products = []
		self._copy_counts.clear()
		self._next_item_id = 1
		for item in self._tree.get_children():
			self._tree.delete(item)
		logger.debug("[PrintQueue] Очередь очищена")
	def _clear_all(self) -> None:
		if self._products:
			self.clear()
			logger.info("[PrintQueue] Вся очередь очищена пользователем")
	def _print_all(self) -> None:
		logger.info("[PrintQueue] Печать всех товаров")
		products_to_print = []
		items = self._tree.get_children()
		for idx, item_id in enumerate(items):
			if 0 <= idx < len(self._products):
				product = self._products[idx]
				count = self._copy_counts.get(item_id, 1)
				for _ in range(count):
					products_to_print.append(product)
		if products_to_print:
			self._printer_service.print_queue(products_to_print, one_by_one=False)
	def _import_from_file(self) -> None:
		logger.info("[PrintQueue] Импорт из файла (заглушка)")