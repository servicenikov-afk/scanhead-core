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
        self.geometry("900x550+50+50")
        self.resizable(True, True)
        
        # Привязка к изменению размера окна для динамического переноса текста
        # (используется только для таба "Дополнительно")
        self.bind("<Configure>", self._on_window_resize)
        
        # Флаг, указывающий, что окно закрывается
        self._is_destroying = False
        
        # Отслеживание несохранённых изменений адресов
        self._unsaved_changes = {}  # {index: original_value}
        self._location_entries = []  # Список entry виджетов для адресов
        self._location_frames = []   # Список фреймов для адресов
        
        self._create_ui()
        self._load_details()
        
        # Модальность (после создания UI)
        self.transient(master)
        self.grab_set()
        
        logger.info(f"[ProductInfoDialog] Открыто окно для {product.get('article')}")
    
    def destroy(self):
        """Переопределение метода destroy для предотвращения ошибок при закрытии."""
        self._is_destroying = True
        try:
            # Отвязываем обработчик изменения размера, чтобы избежать вызова после уничтожения
            try:
                self.unbind("<Configure>")
            except Exception:
                pass
            
            super().destroy()
        except Exception as e:
            logger.warning(f"[ProductInfoDialog] Ошибка при уничтожении окна: {e}")
    
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
        
        # Наименование - с простым переносом на 45 символе
        ctk.CTkLabel(parent, text="Наименование:", font=ctk.CTkFont(weight="bold", size=self._font_size)).grid(
            row=2, column=0, sticky="nw", pady=5, padx=5
        )
        self._lbl_name = ctk.CTkLabel(parent, text="", anchor="nw", font=ctk.CTkFont(size=self._font_size))
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
        
        # Модель (бывшая Категория) - теперь отображает product_model из css_export
        ctk.CTkLabel(parent, text="Модель:", font=ctk.CTkFont(weight="bold", size=self._font_size)).grid(
            row=5, column=0, sticky="w", pady=5, padx=5
        )
        self._lbl_model = ctk.CTkLabel(parent, text="", anchor="nw", font=ctk.CTkFont(size=self._font_size))
        self._lbl_model.grid(row=5, column=1, sticky="ew", pady=5, padx=5)
    
    def _wrap_text_at_word(self, text: str, max_length: int = 45) -> str:
        """Перенести текст на границе слова после max_length символов."""
        if not text or len(text) <= max_length:
            return text
        
        # Ищем последнюю границу слова (пробел, дефис, слэш) после max_length
        # Начинаем поиск с max_length и идём вперёд до ближайшей границы слова
        for i in range(max_length, len(text)):
            if text[i] in ' \t-/\n':
                return text[:i] + '\n' + self._wrap_text_at_word(text[i+1:].lstrip(), max_length)
        
        # Если границ не найдено, просто разрываем на max_length
        return text[:max_length] + '\n' + self._wrap_text_at_word(text[max_length:], max_length)
    
    def _create_store_tab(self, parent: ctk.CTkFrame) -> None:
        """Создать вкладку адреса хранения."""
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Прокручиваемый контейнер для адресов
        self._store_scroll_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self._store_scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self._store_scroll_frame.grid_columnconfigure(0, weight=1)
        
        # Контейнер для динамических строк адресов
        self._addresses_container = ctk.CTkFrame(self._store_scroll_frame, fg_color="transparent")
        self._addresses_container.grid(row=0, column=0, sticky="ew", pady=5)
        self._addresses_container.grid_columnconfigure(1, weight=1)
        
        # Кнопка "Добавить адрес"
        self._btn_add_address = ctk.CTkButton(
            self._store_scroll_frame,
            text="➕ Добавить адрес",
            height=self._font_size + 14,
            font=ctk.CTkFont(size=self._font_size),
            command=self._add_address_row
        )
        self._btn_add_address.grid(row=1, column=0, sticky="w", pady=(5, 10))
        
        # Кнопки управления (Сохранить все)
        self._btn_save_all = ctk.CTkButton(
            self._store_scroll_frame,
            text="💾 Сохранить все",
            height=self._font_size + 14,
            font=ctk.CTkFont(size=self._font_size),
            fg_color="#28a745",
            hover_color="#218838",
            command=self._save_all_locations
        )
        self._btn_save_all.grid(row=1, column=0, sticky="e", pady=(5, 10), padx=(0, 5))
    
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
        # Применяем перенос строк на 45 символе для наименования
        name_text = self._product.get('name', '')
        self._lbl_name.configure(text=self._wrap_text_at_word(name_text))
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
        
        # Обновляем адреса хранения - создаём строки для каждого адреса
        self._clear_address_rows()
        if product.storage_locations:
            for i, location in enumerate(product.storage_locations):
                self._add_address_row(location, is_original=True)
        else:
            # Если адресов нет, добавляем одну пустую строку
            self._add_address_row("", is_original=False)
        
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
            models_text = ", ".join(unique_models)
            # Применяем перенос строк на 45 символе
            self._lbl_model.configure(text=self._wrap_text_at_word(models_text))
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
        # Игнорируем события во время уничтожения окна
        if getattr(self, '_is_destroying', False):
            return
        
        # Защита от рекурсивных вызовов и бесконечного цикла
        if getattr(self, '_resize_lock', False):
            return
        
        # Проверяем минимальное изменение ширины (15px) чтобы избежать частых обновлений
        last_width = getattr(self, '_last_width', 0)
        width_change = abs(event.width - last_width)
        if width_change < 15:
            return
        
        self._resize_lock = True
        try:
            self._last_width = event.width
            
            # Вычисляем доступную ширину: ширина окна минус отступы (примерно 120px)
            new_wraplength = max(200, event.width - 120)
            
            # Обновляем wraplength для лейбла с моделями
            if hasattr(self, '_models_label') and self._models_label:
                try:
                    self._models_label.configure(wraplength=new_wraplength)
                except Exception:
                    # Виджет может быть уничтожен во время изменения размера
                    pass
            
            # Обновляем wraplength для всех лейблов с деталями
            if hasattr(self, '_detail_labels') and self._detail_labels:
                for label, frame in self._detail_labels:
                    try:
                        label.configure(wraplength=new_wraplength)
                    except Exception:
                        # Виджет может быть уничтожен во время изменения размера
                        pass
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
        # Загрузить адреса из БД
        self._clear_address_rows()
        if self._store_adapter:
            locations = self._store_adapter.get_all_locations(self._product.get('article', ''))
            if locations:
                for location in locations:
                    self._add_address_row(location, is_original=True)
            else:
                self._add_address_row("", is_original=False)
        else:
            self._add_address_row("", is_original=False)
        
        self._lbl_css_loading.configure(text="ℹ️ Дополнительная информация\n\nДанные из css_export.db\n(подключите ProductDetailsService для полной функциональности)")
    
    def _clear_address_rows(self) -> None:
        """Очистить все строки адресов."""
        for widget in self._addresses_container.winfo_children():
            widget.destroy()
        self._location_entries = []
        self._location_frames = []
        self._unsaved_changes = {}
    
    def _add_address_row(self, initial_value: str = "", is_original: bool = False) -> None:
        """Добавить новую строку с адресом."""
        row_index = len(self._location_frames)
        
        # Фрейм для строки
        row_frame = ctk.CTkFrame(self._addresses_container, fg_color="transparent")
        row_frame.grid(row=row_index, column=0, columnspan=4, sticky="ew", pady=2)
        row_frame.grid_columnconfigure(1, weight=1)
        self._location_frames.append(row_frame)
        
        # Label с номером
        lbl_num = ctk.CTkLabel(
            row_frame,
            text=f"#{row_index + 1}",
            width=30,
            font=ctk.CTkFont(size=self._font_size)
        )
        lbl_num.grid(row=0, column=0, padx=(0, 5))
        
        # Entry для адреса
        entry = ctk.CTkEntry(
            row_frame,
            placeholder_text="Введите адрес",
            height=self._font_size + 16,
            font=ctk.CTkFont(size=self._font_size, family="Arial")
        )
        entry.insert(0, initial_value)
        entry.grid(row=0, column=1, sticky="ew", padx=5)
        self._location_entries.append(entry)
        
        # Кнопка "Удалить" (корзина)
        btn_delete = ctk.CTkButton(
            row_frame,
            text="🗑️",
            width=40,
            height=self._font_size + 14,
            font=ctk.CTkFont(size=self._font_size),
            fg_color="#dc3545",
            hover_color="#c82333",
            command=lambda idx=row_index: self._delete_address_row(idx)
        )
        btn_delete.grid(row=0, column=2, padx=5)
        
        # Кнопка "Сохранить" (дискета) - для индивидуального сохранения
        btn_save = ctk.CTkButton(
            row_frame,
            text="💾",
            width=40,
            height=self._font_size + 14,
            font=ctk.CTkFont(size=self._font_size),
            fg_color="#007bff",
            hover_color="#0056b3",
            command=lambda idx=row_index: self._save_address_row(idx)
        )
        btn_save.grid(row=0, column=3, padx=5)
        
        # Отслеживаем оригинальное значение
        if is_original:
            self._unsaved_changes[row_index] = initial_value
    
    def _delete_address_row(self, index: int) -> None:
        """Удалить строку адреса с подтверждением."""
        if index < 0 or index >= len(self._location_frames):
            return
        
        # Проверка на несохранённые изменения
        if index in self._unsaved_changes:
            # Создаём кастомный диалог подтверждения
            confirm_dialog = ctk.CTkToplevel(self)
            confirm_dialog.title("Подтверждение")
            confirm_dialog.geometry("300x150")
            confirm_dialog.transient(self)
            confirm_dialog.grab_set()
            
            ctk.CTkLabel(
                confirm_dialog,
                text="В этой строке есть несохранённые изменения. Удалить?",
                font=ctk.CTkFont(size=self._font_size)
            ).pack(pady=20)
            
            btn_frame = ctk.CTkFrame(confirm_dialog, fg_color="transparent")
            btn_frame.pack(pady=10)
            
            def on_confirm():
                self._do_delete_address_row(index)
                confirm_dialog.destroy()
            
            def on_cancel():
                confirm_dialog.destroy()
            
            ctk.CTkButton(
                btn_frame,
                text="Отмена",
                command=on_cancel,
                fg_color="#6c757d",
                hover_color="#5a6268"
            ).pack(side="left", padx=5)
            
            ctk.CTkButton(
                btn_frame,
                text="Удалить",
                command=on_confirm,
                fg_color="#dc3545",
                hover_color="#c82333"
            ).pack(side="left", padx=5)
            
            return
        
        # Если нет несохранённых изменений, удаляем сразу
        self._do_delete_address_row(index)
    
    def _do_delete_address_row(self, index: int) -> None:
        """Выполнить удаление строки адреса."""
        # Удаляем виджеты
        self._location_frames[index].destroy()
        self._location_frames.pop(index)
        self._location_entries.pop(index)
        
        # Пересоздаём строки с правильными номерами
        self._rebuild_address_rows()
    
    def _rebuild_address_rows(self) -> None:
        """Перестроить строки адресов после удаления."""
        # Сохраняем текущие значения
        current_values = [entry.get() for entry in self._location_entries]
        
        # Очищаем и пересоздаём
        self._clear_address_rows()
        
        for value in current_values:
            self._add_address_row(value, is_original=False)
    
    def _save_address_row(self, index: int) -> None:
        """Сохранить конкретную строку адреса."""
        if index < 0 or index >= len(self._location_entries):
            return
        
        new_value = self._location_entries[index].get().strip()
        if not new_value:
            return
        
        # Диалог подтверждения
        dialog = ctk.CTkToplevel(self)
        dialog.title("Подтверждение")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(
            dialog,
            text="Сохранить изменения?",
            font=ctk.CTkFont(size=self._font_size)
        ).pack(pady=20)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        def on_confirm():
            self._do_save_address_row(index, new_value)
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        ctk.CTkButton(
            btn_frame,
            text="Отмена",
            command=on_cancel,
            fg_color="#6c757d",
            hover_color="#5a6268"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Сохранить",
            command=on_confirm,
            fg_color="#28a745",
            hover_color="#218838"
        ).pack(side="left", padx=5)
    
    def _do_save_address_row(self, index: int, new_value: str) -> None:
        """Выполнить сохранение адреса."""
        article = self._product.get('article', '')
        
        # Получаем все текущие адреса
        all_locations = [entry.get().strip() for entry in self._location_entries if entry.get().strip()]
        
        if self._store_adapter:
            success = self._store_adapter.set_locations(article, all_locations)
            if success:
                # Обновляем статус
                self._location_entries[index].configure(border_color="green")
                if index in self._unsaved_changes:
                    del self._unsaved_changes[index]
                logger.info(f"[ProductInfoDialog] Адреса сохранены для {article}: {all_locations}")
            else:
                logger.error(f"[ProductInfoDialog] Ошибка сохранения адресов для {article}")
    
    def _save_all_locations(self) -> None:
        """Сохранить все адреса."""
        article = self._product.get('article', '')
        all_locations = [entry.get().strip() for entry in self._location_entries if entry.get().strip()]
        
        if not all_locations:
            return
        
        # Диалог подтверждения
        dialog = ctk.CTkToplevel(self)
        dialog.title("Подтверждение")
        dialog.geometry("350x180")
        dialog.transient(self)
        dialog.grab_set()
        
        ctk.CTkLabel(
            dialog,
            text=f"Сохранить {len(all_locations)} адрес(ов)?",
            font=ctk.CTkFont(size=self._font_size),
            wraplength=300
        ).pack(pady=20)
        
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        def on_confirm():
            self._do_save_all_locations(all_locations)
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        ctk.CTkButton(
            btn_frame,
            text="Отмена",
            command=on_cancel,
            fg_color="#6c757d",
            hover_color="#5a6268"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Сохранить",
            command=on_confirm,
            fg_color="#28a745",
            hover_color="#218838"
        ).pack(side="left", padx=5)
    
    def _do_save_all_locations(self, locations: list) -> None:
        """Выполнить сохранение всех адресов."""
        article = self._product.get('article', '')
        
        if self._store_adapter:
            success = self._store_adapter.set_locations(article, locations)
            if success:
                # Сбрасываем все несохранённые изменения
                self._unsaved_changes = {}
                for entry in self._location_entries:
                    entry.configure(border_color="")
                logger.info(f"[ProductInfoDialog] Все адреса сохранены для {article}: {locations}")
            else:
                logger.error(f"[ProductInfoDialog] Ошибка сохранения адресов для {article}")
