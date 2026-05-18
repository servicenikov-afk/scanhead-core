"""
Детали товара: поля для отображения информации о товаре.
Все поля readonly, кнопка "Изменить" открывает диалог редактирования.
"""

import logging
from typing import Any, Optional

import customtkinter as ctk
from tkinter import ttk

from services.interfaces import IProductRepository
from libs.domain_models import Product, Address
from gui.dialogs.field_editor import FieldEditor

logger = logging.getLogger(__name__)


class ProductDetails(ctk.CTkFrame):
    """
    Панель деталей товара.
    
    Отображает: артикул, название, адрес хранения.
    Все поля только для чтения, изменение через диалог.
    """
    
    def __init__(
        self, 
        master: Any, 
        product_repo: IProductRepository,
        on_add_to_queue: callable = None
    ):
        super().__init__(master)
        self._product_repo = product_repo
        self._on_add_to_queue = on_add_to_queue
        self._current_product: Optional[Product] = None
        
        logger.debug("[ProductDetails] Инициализация")
        
        # Контейнер для полей и кнопки
        fields_frame = ctk.CTkFrame(self, fg_color="transparent")
        fields_frame.pack(fill="both", expand=True, padx=2, pady=2)
        fields_frame.grid_columnconfigure(1, weight=1)
        
        # Поле: Артикул
        self._create_field_row(
            fields_frame, 
            row=0, 
            label="Артикул:", 
            field_name="article"
        )
        
        # Поле: Артикул 2 (дополнительный)
        self._create_field_row(
            fields_frame, 
            row=1, 
            label="Артикул 2:", 
            field_name="article2"
        )
        
        # Поле: Наименование
        self._create_field_row(
            fields_frame, 
            row=2, 
            label="Наименование:", 
            field_name="name"
        )
        
        # Поле: Адрес хранения (с кнопкой редактирования)
        self._create_field_row(
            fields_frame, 
            row=3, 
            label="Адрес:", 
            field_name="address",
            show_edit_btn=True
        )
        
        # Кнопки под полями: [ℹ️] и [⤵️]
        buttons_row = ctk.CTkFrame(fields_frame, fg_color="transparent")
        buttons_row.grid(row=4, column=1, padx=2, pady=2, sticky="w")
        
        btn_info = ctk.CTkButton(
            buttons_row,
            text="ℹ️",
            width=28,
            height=28,
            command=self._on_info_click
        )
        btn_info.pack(side="left", padx=2)
        
        btn_add = ctk.CTkButton(
            buttons_row,
            text="⤵️",
            width=28,
            height=28,
            command=self._on_add_to_queue_click
        )
        btn_add.pack(side="left", padx=2)
        
        logger.debug("[ProductDetails] Поля и кнопки созданы")
    
    def _create_field_row(
        self, 
        parent: Any, 
        row: int, 
        label: str, 
        field_name: str,
        show_edit_btn: bool = False
    ) -> None:
        """Создание строки с полем и кнопкой редактирования."""
        # Метка
        lbl = ctk.CTkLabel(
            parent,
            text=label,
            width=100,
            anchor="e",
            font=ctk.CTkFont(size=13)
        )
        lbl.grid(row=row, column=0, padx=(5, 10), pady=2, sticky="e")
        
        # Поле ввода (readonly)
        entry = ttk.Entry(
            parent,
            state="readonly",
            font=("Arial", 12)
        )
        entry.grid(row=row, column=1, padx=2, pady=2, sticky="ew")
        
        # Кнопка "Изменить" (только если show_edit_btn=True)
        if show_edit_btn:
            btn_edit = ctk.CTkButton(
                parent,
                text="✏️",
                width=40,
                height=28,
                command=lambda: self._open_editor(field_name)
            )
            btn_edit.grid(row=row, column=2, padx=2, pady=2)
        
        # Сохраняем ссылки на виджеты
        setattr(self, f"_{field_name}_label", lbl)
        setattr(self, f"_{field_name}_entry", entry)
    
    def _on_info_click(self) -> None:
        """Обработчик нажатия кнопки 'ℹ️' (детальная информация)."""
        if not self._current_product:
            logger.warning("[ProductDetails] Нет товара для отображения детальной информации")
            return
        
        logger.info(f"[ProductDetails] Запрос детальной информации по {self._current_product.article}")
        
        # Открываем диалог с подробной информацией
        from gui.dialogs.product_info_dialog import ProductInfoDialog
        
        # Формируем словарь данных для диалога
        product_data = {
            'article': self._current_product.article,
            'article2': self._current_product.barcodes[1] if len(self._current_product.barcodes) > 1 else '',
            'name': self._current_product.name,
            'barcodes': ', '.join(self._current_product.barcodes),
            'description': getattr(self._current_product, 'description', 'Нет описания'),
            'category': getattr(self._current_product, 'category', 'Нет категории')
        }
        
        dialog = ProductInfoDialog(
            self,
            product=product_data,
            nomenclature_adapter=self._product_repo,
            store_adapter=self._product_repo,
            css_adapter=None
        )
    
    def _on_add_to_queue_click(self) -> None:
        """Обработчик нажатия кнопки '⤵️' (добавить в очередь)."""
        if not self._current_product:
            logger.warning("[ProductDetails] Нет товара для добавления в очередь")
            return
        
        if self._on_add_to_queue:
            logger.info(f"[ProductDetails] Добавление товара {self._current_product.article} в очередь")
            self._on_add_to_queue(self._current_product)
        else:
            logger.warning("[ProductDetails] Callback on_add_to_queue не установлен")
    
    def _open_editor(self, field_name: str) -> None:
        """Открытие диалога редактирования поля."""
        if not self._current_product:
            logger.warning("[ProductDetails] Нет текущего товара для редактирования")
            return
        
        logger.info(f"[ProductDetails] Открытие редактора для поля {field_name}")
        
        # Получаем текущее значение
        value = self._get_field_value(field_name)
        
        # Открываем диалог
        # Используем article как идентификатор, т.к. в Product нет поля id
        dialog = FieldEditor(
            self,
            field_name=field_name,
            current_value=value,
            product_id=self._current_product.article,
            product_repo=self._product_repo,
            on_save=self._on_field_saved
        )
        dialog.grab_set()
    
    def _get_field_value(self, field_name: str) -> str:
        """Получение значения поля из текущего товара."""
        if not self._current_product:
            return ""
        
        match field_name:
            case "article":
                return self._current_product.article
            case "article2":
                # Возвращаем второй штрих-код если есть
                if len(self._current_product.barcodes) > 1:
                    return self._current_product.barcodes[1]
                return ""
            case "name":
                return self._current_product.name
            case "address":
                if self._current_product.address:
                    return self._current_product.address
                return "Не указан"
            case _:
                return ""
    
    def _on_field_saved(self, field_name: str, new_value: str) -> None:
        """Обработчик сохранения поля из диалога."""
        if not self._current_product:
            return
        
        logger.info(f"[ProductDetails] Поле {field_name} обновлено: {new_value}")
        
        # Вызываем репозиторий для обновления (используем article как id)
        success = self._product_repo.update_field(
            self._current_product.article,
            field_name,
            new_value
        )
        
        if success:
            # Обновляем UI
            self.set_product(self._current_product)
    
    def set_product(self, product: Product) -> None:
        """
        Установка текущего товара и обновление полей.
        
        :param product: Товар для отображения
        """
        self._current_product = product
        logger.debug(f"[ProductDetails] Установка товара: {product.article}")
        
        # Обновляем все поля
        for field_name in ["article", "article2", "name", "address"]:
            entry = getattr(self, f"_{field_name}_entry")
            value = self._get_field_value(field_name)
            
            entry.config(state="normal")
            entry.delete(0, "end")
            entry.insert(0, value)
            entry.config(state="readonly")
    
    def clear(self) -> None:
        """Очистка всех полей."""
        self._current_product = None
        logger.debug("[ProductDetails] Очистка полей")
        
        for field_name in ["article", "article2", "name", "address"]:
            entry = getattr(self, f"_{field_name}_entry")
            entry.config(state="normal")
            entry.delete(0, "end")
            entry.config(state="readonly")
    
    def get_current_product(self) -> Optional[Product]:
        """Получение текущего товара."""
        return self._current_product
