"""Окно детальной информации о товаре."""
import customtkinter as ctk
from typing import Any, Optional, Dict, List
from tkinter import ttk
import logging

from gui.services.product_details_service import ProductDetailsService
from libs.domain_models import Product

logger = logging.getLogger(__name__)


class ProductInfoDialog(ctk.CTkToplevel):
    """Диалог отображения детальной информации о товаре."""
    
    def __init__(
        self,
        master: Any,
        product: Dict[str, Any],
        nomenclature_adapter: Any = None,
        store_adapter: Any = None,
        css_adapter: Any = None,
        font_size: int = 14,
        details_service: Optional[ProductDetailsService] = None
    ):
        super().__init__(master)
        
        self._product = product
        self._nomenclature_adapter = nomenclature_adapter
        self._store_adapter = store_adapter
        self._css_adapter = css_adapter
        self._font_size = font_size
        self._details_service = details_service
        
        self.title(f"📦 {product.get('article', 'Товар')}")
        self.geometry("800x600")
        self.resizable(True, True)
        
        # Модальность
        self.transient(master)
        self.grab_set()
        
        self._create_ui()
        self._load_details()
        
        logger.info(f"[ProductInfoDialog] Открыто окно для {product.get('article')}")
    
    def _create_ui(self) -> None:
        """Создать интерфейс окна."""
        # Основной контейнер
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Заголовок
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            header_frame,
            text="📋 Детальная информация",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        ctk.CTkButton(
            header_frame,
            text="✕",
            width=30,
            height=30,
            command=self.destroy
        ).pack(side="right")
        
        # Табы с информацией
        self._notebook = ctk.CTkTabview(main_frame)
        self._notebook.pack(fill="both", expand=True)
        
        # Вкладка "Основное" (из nomenclature)
        self._nom_tab = self._notebook.add("📦 Номенклатура")
        self._create_nomenclature_tab(self._nom_tab)
        
        # Вкладка "Адрес" (из store)
        self._store_tab = self._notebook.add("📍 Адрес хранения")
        self._create_store_tab(self._store_tab)
        
        # Вкладка "Дополнительно" (из css_export)
        self._css_tab = self._notebook.add("📎 Дополнительно")
        self._create_css_tab(self._css_tab)
    
    def _create_nomenclature_tab(self, parent: ctk.CTkFrame) -> None:
        """Создать вкладку номенклатуры."""
        # Сетка для полей
        for i in range(7):
            parent.grid_rowconfigure(i, weight=0)
        parent.grid_columnconfigure(0, weight=0)
        parent.grid_columnconfigure(1, weight=1)
        
        # Артикул - высота = шрифт + 20
        field_height = self._font_size + 20
        
        ctk.CTkLabel(parent, text="Артикул:", font=ctk.CTkFont(weight="bold", size=self._font_size)).grid(
            row=0, column=0, sticky="w", pady=5, padx=5
        )
        self._lbl_article = ctk.CTkLabel(parent, text="", anchor="w", height=field_height, font=ctk.CTkFont(size=self._font_size))
        self._lbl_article.grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        
        # Альт. артикул
        ctk.CTkLabel(parent, text="Альт. артикул:", font=ctk.CTkFont(weight="bold", size=self._font_size)).grid(
            row=1, column=0, sticky="w", pady=5, padx=5
        )
        self._lbl_article2 = ctk.CTkLabel(parent, text="", anchor="w", height=field_height, font=ctk.CTkFont(size=self._font_size))
        self._lbl_article2.grid(row=1, column=1, sticky="ew", pady=5, padx=5)
        
        # Наименование
        ctk.CTkLabel(parent, text="Наименование:", font=ctk.CTkFont(weight="bold", size=self._font_size)).grid(
            row=2, column=0, sticky="nw", pady=5, padx=5
        )
        self._lbl_name = ctk.CTkLabel(parent, text="", anchor="nw", wraplength=400, height=field_height, font=ctk.CTkFont(size=self._font_size))
        self._lbl_name.grid(row=2, column=1, sticky="ew", pady=5, padx=5)
        
        # Штрихкоды
        ctk.CTkLabel(parent, text="Штрихкоды:", font=ctk.CTkFont(weight="bold", size=self._font_size)).grid(
            row=3, column=0, sticky="w", pady=5, padx=5
        )
        self._lbl_barcodes = ctk.CTkLabel(parent, text="", anchor="w", height=field_height, font=ctk.CTkFont(size=self._font_size))
        self._lbl_barcodes.grid(row=3, column=1, sticky="ew", pady=5, padx=5)
        
        # Единица измерения
        ctk.CTkLabel(parent, text="Ед. изм.:", font=ctk.CTkFont(weight="bold", size=self._font_size)).grid(
            row=4, column=0, sticky="w", pady=5, padx=5
        )
        self._lbl_unit = ctk.CTkLabel(parent, text="", anchor="w", height=field_height, font=ctk.CTkFont(size=self._font_size))
        self._lbl_unit.grid(row=4, column=1, sticky="ew", pady=5, padx=5)
        
        # Описание (если есть)
        ctk.CTkLabel(parent, text="Описание:", font=ctk.CTkFont(weight="bold", size=self._font_size)).grid(
            row=5, column=0, sticky="nw", pady=5, padx=5
        )
        self._lbl_description = ctk.CTkLabel(parent, text="", anchor="nw", wraplength=400, height=field_height, font=ctk.CTkFont(size=self._font_size))
        self._lbl_description.grid(row=5, column=1, sticky="ew", pady=5, padx=5)
        
        # Категория
        ctk.CTkLabel(parent, text="Категория:", font=ctk.CTkFont(weight="bold", size=self._font_size)).grid(
            row=6, column=0, sticky="w", pady=5, padx=5
        )
        self._lbl_category = ctk.CTkLabel(parent, text="", anchor="w", height=field_height, font=ctk.CTkFont(size=self._font_size))
        self._lbl_category.grid(row=6, column=1, sticky="ew", pady=5, padx=5)
    
    def _create_store_tab(self, parent: ctk.CTkFrame) -> None:
        """Создать вкладку адреса хранения."""
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Текущий адрес
        info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        info_frame.grid(row=0, column=0, sticky="ew", pady=10, padx=10)
        
        ctk.CTkLabel(
            info_frame,
            text="Текущий адрес хранения:",
            font=ctk.CTkFont(weight="bold", size=self._font_size)
        ).pack(anchor="w")
        
        self._lbl_location = ctk.CTkLabel(
            info_frame,
            text="Загрузка...",
            font=ctk.CTkFont(size=self._font_size + 4),
            text_color="green",
            height=self._font_size + 20
        )
        self._lbl_location.pack(anchor="w", pady=10)
        
        # Поле редактирования
        edit_frame = ctk.CTkFrame(parent, fg_color="transparent")
        edit_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(edit_frame, text="Изменить адрес:", font=ctk.CTkFont(size=self._font_size)).pack(anchor="w")
        
        entry_frame = ctk.CTkFrame(edit_frame, fg_color="transparent")
        entry_frame.pack(fill="x", pady=5)
        
        self._entry_location = ctk.CTkEntry(
            entry_frame,
            placeholder_text="Новый адрес",
            height=self._font_size + 16,
            font=ctk.CTkFont(size=self._font_size, family="Arial")
        )
        self._entry_location.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkButton(
            entry_frame,
            text="💾 Сохранить",
            height=self._font_size + 14,
            font=ctk.CTkFont(size=self._font_size),
            command=self._save_location
        ).pack(side="left")
    
    def _create_css_tab(self, parent: ctk.CTkFrame) -> None:
        """Создать вкладку дополнительной информации."""
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Создаём прокручиваемый фрейм для контента
        scroll_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Заголовок
        ctk.CTkLabel(
            scroll_frame,
            text="📎 Информация от производителя",
            font=ctk.CTkFont(size=self._font_size + 2, weight="bold")
        ).pack(anchor="w", pady=(0, 10))
        
        # Контейнер для записей
        self._css_records_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        self._css_records_frame.pack(fill="both", expand=True, anchor="w")
        
        # Поле для загрузки
        self._lbl_css_loading = ctk.CTkLabel(
            scroll_frame,
            text="Загрузка данных...",
            font=ctk.CTkFont(size=self._font_size),
            justify="center"
        )
        self._lbl_css_loading.pack(pady=20)
    
    def _load_details(self) -> None:
        """Загрузить данные в форму."""
        # Основные данные из переданного product
        self._lbl_article.configure(text=self._product.get('article', ''))
        self._lbl_article2.configure(text=self._product.get('article2', ''))
        self._lbl_name.configure(text=self._product.get('name', ''))
        self._lbl_barcodes.configure(text=self._product.get('barcodes', ''))
        self._lbl_description.configure(text=self._product.get('description', 'Нет описания'))
        self._lbl_category.configure(text=self._product.get('category', 'Нет категории'))
        
        # Если есть details_service, загружаем полные данные из всех БД
        if self._details_service:
            article = self._product.get('article', '')
            self._lbl_css_loading.configure(text="Загрузка данных из всех источников...")
            
            # Загружаем данные асинхронно
            def on_details_loaded(product: Optional[Product]):
                if product:
                    self._update_ui_with_full_data(product)
                else:
                    self._lbl_css_loading.configure(text="Не удалось загрузить данные")
            
            self._details_service.get_product_details(article, callback=on_details_loaded)
        else:
            # Старый режим с адаптерами
            self._load_details_legacy()
    
    def _update_ui_with_full_data(self, product: Product) -> None:
        """Обновить UI с полными данными из ProductDetailsService."""
        # Обновляем основные поля если есть новые данные
        if product.unit:
            self._lbl_unit.configure(text=product.unit)
        
        # Обновляем адрес хранения
        if product.storage_locations:
            location_text = " | ".join(product.storage_locations)
            self._lbl_location.configure(text=location_text, text_color="green")
            self._entry_location.delete(0, "end")
            self._entry_location.insert(0, product.storage_locations[0])
        else:
            self._lbl_location.configure(text="Не указан", text_color="gray")
        
        # Обновляем категорию
        if product.category:
            self._lbl_category.configure(text=product.category)
        
        # Заполняем вкладку CSS данными от производителя
        self._populate_css_tab(product.manufacturer_info, product.models)
        
        self._lbl_css_loading.pack_forget()
    
    def _populate_css_tab(self, manufacturer_info: List[Dict[str, Any]], models: List[str]) -> None:
        """Заполнить вкладку CSS данными от производителя."""
        # Очищаем старые записи
        for widget in self._css_records_frame.winfo_children():
            widget.destroy()
        
        if not manufacturer_info:
            ctk.CTkLabel(
                self._css_records_frame,
                text="ℹ️ Данные от производителя не найдены",
                font=ctk.CTkFont(size=self._font_size),
                justify="center"
            ).pack(pady=20)
            return
        
        # Список моделей
        if models:
            models_frame = ctk.CTkFrame(self._css_records_frame, fg_color="#2a2a2a")
            models_frame.pack(fill="x", pady=5, padx=5)
            
            ctk.CTkLabel(
                models_frame,
                text=f"🔧 Модели оборудования ({len(models)}):",
                font=ctk.CTkFont(size=self._font_size, weight="bold")
            ).pack(anchor="w", padx=5, pady=5)
            
            models_text = "\n".join(f"• {m}" for m in models[:10])
            if len(models) > 10:
                models_text += f"\n... и ещё {len(models) - 10}"
            
            ctk.CTkLabel(
                models_frame,
                text=models_text,
                font=ctk.CTkFont(size=self._font_size - 1),
                justify="left",
                wraplength=600
            ).pack(anchor="w", padx=10, pady=5)
        
        # Записи о деталях
        for i, item in enumerate(manufacturer_info[:20]):  # Ограничим 20 записями
            record_frame = ctk.CTkFrame(self._css_records_frame, fg_color="#2a2a2a")
            record_frame.pack(fill="x", pady=3, padx=5)
            
            # Заголовок записи
            header = f"#{i+1} {item.get('product_model', 'N/A')}"
            ctk.CTkLabel(
                record_frame,
                text=header,
                font=ctk.CTkFont(size=self._font_size, weight="bold"),
                text_color="#4CAF50"
            ).pack(anchor="w", padx=5, pady=(5, 0))
            
            # Детали
            details = []
            if item.get('name'):
                details.append(f"Название: {item['name']}")
            if item.get('position'):
                details.append(f"Позиция: {item['position']}")
            if item.get('usage_path'):
                details.append(f"Расположение: {item['usage_path']}")
            if item.get('category1'):
                details.append(f"Категория: {item['category1']}")
            if item.get('category2'):
                details.append(f"Подкатегория: {item['category2']}")
            if item.get('production_date_from'):
                details.append(f"Производство с: {item['production_date_from']}")
            if item.get('serial_from') and item.get('serial_to'):
                details.append(f"Серийные номера: {item['serial_from']} - {item['serial_to']}")
            
            details_text = "\n".join(details)
            ctk.CTkLabel(
                record_frame,
                text=details_text,
                font=ctk.CTkFont(size=self._font_size - 1),
                justify="left",
                wraplength=600
            ).pack(anchor="w", padx=10, pady=(0, 5))
        
        if len(manufacturer_info) > 20:
            ctk.CTkLabel(
                self._css_records_frame,
                text=f"... и ещё {len(manufacturer_info) - 20} записей",
                font=ctk.CTkFont(size=self._font_size - 1),
                text_color="gray"
            ).pack(pady=5)
    
    def _load_details_legacy(self) -> None:
        """Загрузить данные через старые адаптеры (обратная совместимость)."""
        # Загрузить адрес из БД
        if self._store_adapter:
            location = self._store_adapter.get_location(self._product.get('article', ''))
            if location:
                self._lbl_location.configure(text=location, text_color="green")
                self._entry_location.insert(0, location)
            else:
                self._lbl_location.configure(text="Не указан", text_color="gray")
        else:
            self._lbl_location.configure(text="Адаптер не подключён", text_color="red")
        
        self._lbl_css_loading.configure(text="ℹ️ Дополнительная информация\n\nДанные из css_export.db\n(подключите ProductDetailsService для полной функциональности)")
    
    def _save_location(self) -> None:
        """Сохранить новый адрес."""
        new_location = self._entry_location.get().strip()
        if not new_location:
            return
        
        if self._store_adapter:
            article = self._product.get('article', '')
            success = self._store_adapter.update_location(article, new_location)
            if success:
                self._lbl_location.configure(text=new_location, text_color="green")
                logger.info(f"[ProductInfoDialog] Адрес сохранён для {article}: {new_location}")
            else:
                logger.error(f"[ProductInfoDialog] Ошибка сохранения адреса для {article}")
