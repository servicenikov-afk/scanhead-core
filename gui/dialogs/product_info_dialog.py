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
        self._models_label = None
        self._detail_labels = []
        self._last_width = 800  # Для отслеживания изменений размера
        self._resize_lock = False  # Блокировка рекурсивных вызовов
        
        self.title(f"📦 {product.get('article', 'Товар')}")
        self.geometry("1200x680+50+50")
        self.resizable(True, True)
        
        # Привязка к изменению размера окна для динамического переноса текста
        self.bind("<Configure>", self._on_window_resize)
        
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
        # Сетка для полей (6 строк вместо 7 - убрано Описание)
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
        
        # Наименование - с динамическим wraplength
        ctk.CTkLabel(parent, text="Наименование:", font=ctk.CTkFont(weight="bold", size=self._font_size)).grid(
            row=2, column=0, sticky="nw", pady=5, padx=5
        )
        self._lbl_name = ctk.CTkLabel(parent, text="", anchor="nw", wraplength=550, height=field_height, font=ctk.CTkFont(size=self._font_size))
        self._lbl_name.grid(row=2, column=1, sticky="ew", pady=5, padx=5)
        
        # Привязка для динамического изменения wraplength при изменении размера окна
        parent.bind("<Configure>", lambda e: self._update_nomenclature_wraplength(e.width))
        
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
        
        # Модель (бывшая Категория) - теперь отображает product_model из css_export
        ctk.CTkLabel(parent, text="Модель:", font=ctk.CTkFont(weight="bold", size=self._font_size)).grid(
            row=5, column=0, sticky="w", pady=5, padx=5
        )
        self._lbl_model = ctk.CTkLabel(parent, text="", anchor="nw", wraplength=550, height=field_height, font=ctk.CTkFont(size=self._font_size))
        self._lbl_model.grid(row=5, column=1, sticky="ew", pady=5, padx=5)
    
    def _update_nomenclature_wraplength(self, window_width: int) -> None:
        """Обновить wraplength для полей Наименование и Модель при изменении размера окна."""
        # Вычисляем доступную ширину: ширина окна минус отступы (~150px)
        new_wraplength = max(200, window_width - 150)
        
        if hasattr(self, '_lbl_name'):
            self._lbl_name.configure(wraplength=new_wraplength)
        
        if hasattr(self, '_lbl_model'):
            self._lbl_model.configure(wraplength=new_wraplength)
    
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
        # Поле description удалено, category переименовано в model
        
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
        
        # Обновляем поле "Модель" - обрезаем текст в скобках и объединяем через запятую
        if product.models:
            # Обрезаем значения в скобках: "FM series (FCS4026)" -> "FM series"
            cleaned_models = []
            for model in product.models:
                # Находим первую скобку и обрезаем до неё
                if '(' in model:
                    cleaned = model.split('(')[0].strip()
                else:
                    cleaned = model.strip()
                if cleaned:
                    cleaned_models.append(cleaned)
            
            # Убираем дубликаты и объединяем через запятую
            unique_models = list(dict.fromkeys(cleaned_models))
            self._lbl_model.configure(text=", ".join(unique_models))
        else:
            self._lbl_model.configure(text="Нет модели")
        
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
        
        # Список моделей (уже очищенных в _update_ui_with_full_data)
        if models:
            models_frame = ctk.CTkFrame(self._css_records_frame, fg_color="#f0f0f0", border_width=1, border_color="#cccccc")
            models_frame.pack(fill="x", pady=5, padx=5)
            
            ctk.CTkLabel(
                models_frame,
                text=f"🔧 Модели оборудования ({len(models)}):",
                font=ctk.CTkFont(size=self._font_size, weight="bold"),
                text_color="#000000"
            ).pack(anchor="w", padx=5, pady=5)
            
            # Показываем ВСЕ модели без ограничений
            models_text = "\n".join(f"• {m}" for m in models)
            
            # Динамический wraplength: ширина фрейма минус отступы
            # Начальное значение wraplength
            initial_wraplength = max(200, models_frame.winfo_width() - 40) if models_frame.winfo_width() > 0 else 500
            
            self._models_label = ctk.CTkLabel(
                models_frame,
                text=models_text,
                font=ctk.CTkFont(size=self._font_size - 1),
                justify="left",
                wraplength=initial_wraplength,
                text_color="#000000"
            )
            self._models_label.pack(anchor="w", padx=10, pady=5)
            
            # Привязка к изменению размера для динамического переноса
            models_frame.bind("<Configure>", self._on_models_frame_resize)
        
        # Записи о деталях с форматированием "Модель > Путь" - показываем ВСЕ записи
        self._detail_labels = []  # Сохраняем ссылки для обновления wraplength
        for i, item in enumerate(manufacturer_info):
            record_frame = ctk.CTkFrame(self._css_records_frame, fg_color="#ffffff", border_width=1, border_color="#dddddd")
            record_frame.pack(fill="x", pady=3, padx=5)
            
            # Форматируем "Оригинальное название" и "Расположение"
            original_name = item.get('name', 'N/A')
            
            # Формат: [%Модель] > [%Путь]
            product_model = item.get('product_model', '')
            usage_path = item.get('usage_path', '')
            
            # Обрезаем скобки в модели для отображения
            if '(' in product_model:
                display_model = product_model.split('(')[0].strip()
            else:
                display_model = product_model.strip()
            
            location_display = f"{display_model} > {usage_path}" if display_model and usage_path else (display_model or usage_path or 'N/A')
            
            # Детали
            details = []
            details.append(f"Оригинальное название: {original_name}")
            details.append(f"Расположение: {location_display}")
            if item.get('position'):
                details.append(f"Позиция: {item['position']}")
            if item.get('category1'):
                details.append(f"Категория: {item['category1']}")
            if item.get('category2'):
                details.append(f"Подкатегория: {item['category2']}")
            if item.get('production_date_from'):
                details.append(f"Производство с: {item['production_date_from']}")
            if item.get('serial_from') and item.get('serial_to'):
                details.append(f"Серийные номера: {item['serial_from']} - {item['serial_to']}")
            
            details_text = "\n".join(details)
            
            # Начальное значение wraplength для деталей
            initial_detail_wraplength = max(200, record_frame.winfo_width() - 40) if record_frame.winfo_width() > 0 else 500
            
            label = ctk.CTkLabel(
                record_frame,
                text=details_text,
                font=ctk.CTkFont(size=self._font_size - 1),
                justify="left",
                wraplength=initial_detail_wraplength,
                text_color="#000000"
            )
            label.pack(anchor="w", padx=10, pady=(0, 5))
            self._detail_labels.append((label, record_frame))
        
        # Убрано ограничение на отображение записей - теперь показываются все
    
    def _on_window_resize(self, event):
        """Обработка изменения размера окна для динамического переноса текста."""
        # Защита от рекурсивных вызовов и бесконечного цикла
        if self._resize_lock:
            return
        
        # Проверяем минимальное изменение ширины (15px) чтобы избежать частых обновлений
        width_change = abs(event.width - self._last_width)
        if width_change < 15:
            return
        
        self._resize_lock = True
        try:
            self._last_width = event.width
            
            # Вычисляем доступную ширину: ширина окна минус отступы (примерно 120px)
            new_wraplength = max(200, event.width - 120)
            
            # Обновляем wraplength для лейбла с моделями
            if hasattr(self, '_models_label') and self._models_label:
                self._models_label.configure(wraplength=new_wraplength)
            
            # Обновляем wraplength для всех лейблов с деталями
            if hasattr(self, '_detail_labels') and self._detail_labels:
                for label, frame in self._detail_labels:
                    label.configure(wraplength=new_wraplength)
        finally:
            # Снимаем блокировку через короткую задержку
            self.after(50, lambda: setattr(self, '_resize_lock', False))
    
    def _on_models_frame_resize(self, event):
        """Обработка изменения размера фрейма моделей."""
        if hasattr(self, '_models_label') and self._models_label:
            # Вычисляем wraplength на основе ширины фрейма минус отступы
            new_wraplength = max(150, event.width - 40)
            self._models_label.configure(wraplength=new_wraplength)
    
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
