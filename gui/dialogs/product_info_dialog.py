"""Окно детальной информации о товаре."""
import customtkinter as ctk
from typing import Any, Optional, Dict
from tkinter import ttk
import logging

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
        font_size: int = 14
    ):
        super().__init__(master)
        
        self._product = product
        self._nomenclature_adapter = nomenclature_adapter
        self._store_adapter = store_adapter
        self._css_adapter = css_adapter
        self._font_size = font_size
        
        self.title(f"📦 {product.get('article', 'Товар')}")
        self.geometry("700x500")
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
        for i in range(6):
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
        
        # Описание (если есть)
        ctk.CTkLabel(parent, text="Описание:", font=ctk.CTkFont(weight="bold", size=self._font_size)).grid(
            row=4, column=0, sticky="nw", pady=5, padx=5
        )
        self._lbl_description = ctk.CTkLabel(parent, text="", anchor="nw", wraplength=400, height=field_height, font=ctk.CTkFont(size=self._font_size))
        self._lbl_description.grid(row=4, column=1, sticky="ew", pady=5, padx=5)
        
        # Категория
        ctk.CTkLabel(parent, text="Категория:", font=ctk.CTkFont(weight="bold", size=self._font_size)).grid(
            row=5, column=0, sticky="w", pady=5, padx=5
        )
        self._lbl_category = ctk.CTkLabel(parent, text="", anchor="w", height=field_height, font=ctk.CTkFont(size=self._font_size))
        self._lbl_category.grid(row=5, column=1, sticky="ew", pady=5, padx=5)
    
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
        
        info_label = ctk.CTkLabel(
            parent,
            text="ℹ️ Дополнительная информация\n\nДанные из css_export.db\n(будет реализовано в следующей версии)",
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        info_label.grid(row=0, column=0, sticky="nsew")
    
    def _load_details(self) -> None:
        """Загрузить данные в форму."""
        # Основные данные
        self._lbl_article.configure(text=self._product.get('article', ''))
        self._lbl_article2.configure(text=self._product.get('article2', ''))
        self._lbl_name.configure(text=self._product.get('name', ''))
        self._lbl_barcodes.configure(text=self._product.get('barcodes', ''))
        self._lbl_description.configure(text=self._product.get('description', 'Нет описания'))
        self._lbl_category.configure(text=self._product.get('category', 'Нет категории'))
        
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
