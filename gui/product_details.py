"""
Детали товара: поля для отображения информации о товаре.
Все поля readonly, кнопка "Изменить" открывает диалог редактирования.
"""

import logging
from typing import Any, Optional

import customtkinter as ctk

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
        on_add_to_queue: callable = None,
        font_size: int = 14,
        details_service: Optional[Any] = None
    ):
        super().__init__(master)
        self._product_repo = product_repo
        self._on_add_to_queue = on_add_to_queue
        self._current_product: Optional[Product] = None
        self._font_size = font_size
        self._details_service = details_service
        self._address_entries: list = []  # Список виджетов адресов
        
        logger.debug(f"[ProductDetails] Инициализация (font_size={self._font_size})")
        
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
        
        # Метка для адреса (будет в row=3, column=0)
        self._address_label = ctk.CTkLabel(
            fields_frame,
            text="Адрес:",
            width=100,
            anchor="e",
            font=ctk.CTkFont(size=self._font_size)
        )
        self._address_label.grid(row=3, column=0, padx=(5, 10), pady=2, sticky="ne")
        
        # Контейнер для полей адресов (grid внутри grid)
        self._address_container = ctk.CTkFrame(fields_frame, fg_color="transparent")
        self._address_container.grid(row=3, column=1, padx=2, pady=2, sticky="ew")
        
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
            font=ctk.CTkFont(size=self._font_size)
        )
        lbl.grid(row=row, column=0, padx=(5, 10), pady=2, sticky="e")
        
        # Поле ввода (readonly) - используем CTkEntry вместо ttk для консистентности
        entry = ctk.CTkEntry(
            parent,
            state="disabled",  # readonly эквивалент в CTk
            height=self._font_size + 16,  # Высота = шрифт + отступы
            font=ctk.CTkFont(size=self._font_size, family="Arial"),
            fg_color="#FFFFFF",      # Белый фон
            text_color="#000000",    # Черный текст
            border_color="#AAAAAA",
            corner_radius=6
        )
        entry.grid(row=row, column=1, padx=2, pady=2, sticky="ew")
        
        # Кнопка "Изменить" (только если show_edit_btn=True)
        if show_edit_btn:
            btn_edit = ctk.CTkButton(
                parent,
                text="✏️",
                width=40,
                height=self._font_size + 14,  # Высота кнопки = шрифт + отступы
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
        
        # Фильтруем штрихкоды, исключая основной артикул для article2
        other_barcodes = [b for b in self._current_product.barcodes if b != self._current_product.article]
        article2 = other_barcodes[0] if other_barcodes else ''
        
        # Формируем словарь данных для диалога
        product_data = {
            'article': self._current_product.article,
            'article2': article2,
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
            css_adapter=None,
            font_size=self._font_size,
            details_service=self._details_service
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
                # Возвращаем второй штрих-код, если он отличается от основного
                # Фильтруем баркоды, исключая основной артикул
                other_barcodes = [b for b in self._current_product.barcodes if b != self._current_product.article]
                if other_barcodes:
                    return other_barcodes[0]
                return ""
            case "name":
                return self._current_product.name
            case "address":
                # Больше не используется для textbox, адреса отображаются отдельно
                return ""
            case _:
                return ""
    
    def _render_addresses(self) -> None:
        """Отрисовка адресов в виде отдельных полей с переносом после каждого 3-го."""
        # DEBUG_TEMP: Логирование входных данных
        logger.debug(f"[DEBUG_TEMP] _render_addresses вызван")
        if not self._current_product:
            logger.debug(f"[DEBUG_TEMP] _current_product = None")
        else:
            logger.debug(f"[DEBUG_TEMP] _current_product.article = {self._current_product.article}")
            logger.debug(f"[DEBUG_TEMP] storage_locations = {self._current_product.storage_locations}")
            logger.debug(f"[DEBUG_TEMP] len(storage_locations) = {len(self._current_product.storage_locations) if self._current_product.storage_locations else 0}")
        
        # Очищаем контейнер
        for widget in self._address_container.winfo_children():
            widget.destroy()
        self._address_entries.clear()
        
        if not self._current_product or not self._current_product.storage_locations:
            logger.debug(f"[DEBUG_TEMP] Прерываем отрисовку: нет товара или адресов")
            return
        
        addresses = self._current_product.storage_locations
        row, col = 0, 0
        
        for i, addr in enumerate(addresses):
            # Создаём поле с длиной по содержимому (минимум 15 символов)
            width = max(len(addr) + 2, 15)
            logger.debug(f"[DEBUG_TEMP] Отрисовка адреса[{i}]: '{addr}' (ширина={width})")
            
            entry = ctk.CTkEntry(
                self._address_container,
                state="disabled",
                height=self._font_size + 16,
                font=ctk.CTkFont(size=self._font_size, family="Arial"),
                fg_color="#FFFFFF",
                text_color="#000000",
                border_color="#AAAAAA",
                corner_radius=6,
                width=width * (self._font_size + 4)  # Примерная ширина в пикселях
            )
            entry.insert(0, addr)
            entry.grid(row=row, column=col, padx=2, pady=2, sticky="w")
            
            self._address_entries.append(entry)
            
            col += 1
            # Перенос после каждого 3-го адреса
            if col >= 3:
                col = 0
                row += 1
        
        # Настройка grid контейнера
        for c in range(3):
            self._address_container.grid_columnconfigure(c, weight=1)
        
        # Принудительное обновление геометрии для немедленного отображения
        self._address_container.update_idletasks()
        
        # Диагностика видимости
        logger.debug(f"[DEBUG_TEMP] Контейнер адресов: width={self._address_container.winfo_width()}, height={self._address_container.winfo_height()}")
        logger.debug(f"[DEBUG_TEMP] Контейнер адресов видим: {self._address_container.winfo_ismapped()}")
        for i, entry in enumerate(self._address_entries):
            logger.debug(f"[DEBUG_TEMP] Адрес[{i}] виджет: width={entry.winfo_width()}, visible={entry.winfo_ismapped()}")
        
        logger.debug(f"[DEBUG_TEMP] Отрисовано {len(self._address_entries)} адресов")
    
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
        
        # Обновляем обычные поля
        for field_name in ["article", "article2", "name"]:
            entry = getattr(self, f"_{field_name}_entry")
            value = self._get_field_value(field_name)
            
            # CTkEntry: state="normal" для редактирования, state="disabled" для readonly
            entry.configure(state="normal")
            entry.delete(0, "end")
            if value:  # Вставляем только непустые значения
                entry.insert(0, value)
            entry.configure(state="disabled")
        
        # Отрисовываем адреса отдельными полями
        self._render_addresses()
    
    def clear(self) -> None:
        """Очистка всех полей."""
        self._current_product = None
        logger.debug("[ProductDetails] Очистка полей")
        
        # Очищаем обычные поля
        for field_name in ["article", "article2", "name"]:
            entry = getattr(self, f"_{field_name}_entry")
            entry.configure(state="normal")
            entry.delete(0, "end")
            entry.configure(state="disabled")
        
        # Очищаем контейнер адресов
        for widget in self._address_container.winfo_children():
            widget.destroy()
        self._address_entries.clear()
    
    def get_current_product(self) -> Optional[Product]:
        """Получение текущего товара."""
        return self._current_product
