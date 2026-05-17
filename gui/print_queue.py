"""
Очередь печати на базе ttk.Treeview.
Функционал: отображение товаров, inline-редактирование, удаление, кнопки управления.
"""

import logging
from typing import Any, List, Dict, Optional

import customtkinter as ctk
from tkinter import ttk

from services.interfaces import IProductRepository, IPrinterService, ISettingsService
from libs.domain_models import Product

logger = logging.getLogger(__name__)


class PrintQueue(ctk.CTkFrame):
    """
    Таблица очереди печати.
    
    Колонки: № п/п, Артикул, Артикул 2, Наименование, Адрес, [Действия]
    Функции: inline-редактирование, drag&drop колонок, управление видимостью.
    """
    
    def __init__(
        self,
        master: Any,
        product_repo: IProductRepository,
        printer_service: IPrinterService,
        settings_service: ISettingsService
    ):
        super().__init__(master)
        self._product_repo = product_repo
        self._printer_service = printer_service
        self._settings_service = settings_service
        
        self._products: List[Product] = []
        self._column_config = {
            'visible': ['article', 'article2', 'name', 'address'],
            'order': ['article', 'article2', 'name', 'address']
        }
        
        logger.debug("[PrintQueue] Инициализация")
        
        # Заголовок с кнопками
        self._create_header()
        
        # Таблица
        self._create_table()
        
        # Загружаем настройки колонок
        self._load_column_settings()
        
        logger.debug("[PrintQueue] Таблица создана")
    
    def _create_header(self) -> None:
        """Создание заголовка с кнопками управления."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=3, pady=3)
        
        # Кнопка выбора колонок
        btn_columns = ctk.CTkButton(
            header_frame,
            text="⋮ Столбцы",
            width=80,
            command=self._toggle_column_menu
        )
        btn_columns.pack(side="right", padx=5)
        
        # Кнопка "Импорт из файла"
        btn_import = ctk.CTkButton(
            header_frame,
            text="📥 Импорт",
            width=90,
            command=self._import_from_file
        )
        btn_import.pack(side="right", padx=5)
        
        # Кнопка "Печатать все"
        btn_print_all = ctk.CTkButton(
            header_frame,
            text="🖨️ Все",
            width=80,
            command=self._print_all
        )
        btn_print_all.pack(side="right", padx=5)
        
        # Кнопка "По одному"
        btn_print_one = ctk.CTkButton(
            header_frame,
            text="📄 По одному",
            width=90,
            command=self._print_one_by_one
        )
        btn_print_one.pack(side="right", padx=5)
        
        # Меню выбора колонок (скрыто по умолчанию)
        self._column_menu = ctk.CTkFrame(header_frame, fg_color="#2b2b2b")
        # Будет показано при клике
    
    def _create_table(self) -> None:
        """Создание таблицы Treeview."""
        # Контейнер для таблицы с прокруткой
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=3, pady=3)
        
        # Создаём Treeview
        columns = ("article", "article2", "name", "address")
        self._tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Настройка колонок
        self._tree.heading("article", text="Артикул")
        self._tree.heading("article2", text="Артикул 2")
        self._tree.heading("name", text="Наименование")
        self._tree.heading("address", text="Адрес")
        
        self._tree.column("article", width=100, minwidth=80)
        self._tree.column("article2", width=100, minwidth=80)
        self._tree.column("name", width=200, minwidth=150)
        self._tree.column("address", width=150, minwidth=100)
        
        # Скроллбары
        v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self._tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Размещение
        self._tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Привязка двойного клика для редактирования
        self._tree.bind("<Double-1>", self._on_double_click)
        
        logger.debug("[PrintQueue] Treeview создан")
    
    def _load_column_settings(self) -> None:
        """Загрузка настроек колонок из сервиса настроек."""
        config = self._settings_service.get_column_config()
        if config:
            self._column_config = config
            self._apply_column_visibility()
    
    def _toggle_column_menu(self) -> None:
        """Показать/скрыть меню выбора колонок."""
        logger.info("[PrintQueue] Переключение меню колонок")
        # TODO: Реализовать выпадающее меню с чекбоксами
    
    def _apply_column_visibility(self) -> None:
        """Применение видимости колонок."""
        visible = self._column_config.get('visible', [])
        
        for col in ["article", "article2", "name", "address"]:
            if col in visible:
                self._tree.column(col, width=100, minwidth=80)
            else:
                self._tree.column(col, width=0, minwidth=0, stretch=False)
    
    def _on_double_click(self, event) -> None:
        """Обработчик двойного клика для inline-редактирования."""
        item_id = self._tree.selection()[0] if self._tree.selection() else None
        if not item_id:
            return
        
        # Определяем колонку
        region = self._tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        
        column = self._tree.identify("column", event.x, event.y)
        if column in ("#0", "actions"):
            return  # Не редактируем номер и действия
        
        # Получаем текущее значение
        value = self._tree.item(item_id, "values")[self._get_column_index(column)]
        
        # Создаём Entry для редактирования
        self._start_inline_edit(item_id, column, value)
    
    def _get_column_index(self, column: str) -> int:
        """Получение индекса колонки."""
        columns = ["article", "article2", "name", "address"]
        return columns.index(column) if column in columns else -1
    
    def _start_inline_edit(self, item_id: str, column: str, value: str) -> None:
        """Начало inline-редактирования ячейки."""
        logger.debug(f"[PrintQueue] Inline-редактирование: {column} = {value}")
        
        # Получаем координаты ячейки
        bbox = self._tree.bbox(item_id, column)
        if not bbox:
            return
        
        x, y, width, height = bbox
        
        # Создаём Entry поверх ячейки
        edit_entry = ttk.Entry(self._tree, font=("Arial", 11))
        edit_entry.place(x=x, y=y, width=width, height=height)
        edit_entry.insert(0, value)
        edit_entry.focus_set()
        edit_entry.select_range(0, "end")
        
        # Обработчики сохранения/отмены
        def save(event=None):
            new_value = edit_entry.get().strip()
            if new_value and new_value != value:
                self._tree.set(item_id, column, new_value)
                # TODO: Вызвать репозиторий для сохранения
            edit_entry.destroy()
        
        def cancel(event=None):
            edit_entry.destroy()
        
        edit_entry.bind("<Return>", save)
        edit_entry.bind("<FocusOut>", save)
        edit_entry.bind("<Escape>", cancel)
    
    def set_products(self, products: List[Product]) -> None:
        """
        Установка списка товаров в очередь.
        
        :param products: Список товаров для отображения
        """
        self._products = products
        logger.info(f"[PrintQueue] Установка {len(products)} товаров в очередь")
        
        # Очищаем таблицу
        for item in self._tree.get_children():
            self._tree.delete(item)
        
        # Добавляем товары
        for i, product in enumerate(products, start=1):
            # Формируем значения для колонок
            article2_val = ""
            if len(product.barcodes) > 1:
                article2_val = product.barcodes[1]
            
            address_val = ""
            if product.address:
                address_val = product.address
            
            values = (
                i,  # № п/п
                product.article,
                article2_val,
                product.name,
                address_val
            )
            self._tree.insert("", "end", iid=i, values=values)
    
    def clear(self) -> None:
        """Очистка очереди."""
        self._products = []
        for item in self._tree.get_children():
            self._tree.delete(item)
        logger.debug("[PrintQueue] Очередь очищена")
    
    def _print_all(self) -> None:
        """Печать всех товаров одним PDF."""
        logger.info("[PrintQueue] Печать всех товаров (одним PDF)")
        self._printer_service.print_queue(self._products, one_by_one=False)
    
    def _print_one_by_one(self) -> None:
        """Печать каждого товара отдельно."""
        logger.info("[PrintQueue] Печать по одному")
        self._printer_service.print_queue(self._products, one_by_one=True)
    
    def _import_from_file(self) -> None:
        """Импорт списка из файла (заглушка)."""
        logger.info("[PrintQueue] Импорт из файла (заглушка)")
        # TODO: Открыть диалог выбора файла
