"""
Превью стикера: визуальное отображение макета этикетки.
Кнопка для открытия редактора пресетов.
"""

import logging
from typing import Any, Optional

import customtkinter as ctk
from PIL import Image, ImageTk

from services.interfaces import IPrinterService, ISettingsService
from libs.domain_models import Product
from gui.dialogs.sticker_editor import StickerEditor

logger = logging.getLogger(__name__)


class StickerPreview(ctk.CTkFrame):
    """
    Панель превью стикера.
    
    Отображает макет этикетки и кнопку редактирования пресета.
    """
    
    def __init__(
        self,
        master: Any,
        printer_service: IPrinterService,
        settings_service: ISettingsService
    ):
        super().__init__(master)
        self._printer_service = printer_service
        self._settings_service = settings_service
        self._current_product: Optional[Product] = None
        self._current_image: Optional[ImageTk.PhotoImage] = None
        
        logger.debug("[StickerPreview] Инициализация")
        
        # Заголовок с кнопкой редактора
        self._create_header()
        
        # Область превью
        self._create_preview_area()
        
        logger.debug("[StickerPreview] Превью создано")
    
    def _create_header(self) -> None:
        """Создание заголовка с кнопкой редактора."""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=5, pady=5)
        
        # Заголовок
        title_label = ctk.CTkLabel(
            header_frame,
            text="🏷️ Превью стикера",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(side="left", padx=5)
        
        # Кнопка редактора пресетов
        btn_editor = ctk.CTkButton(
            header_frame,
            text="⚙ Редактор",
            width=90,
            command=self._open_sticker_editor
        )
        btn_editor.pack(side="right", padx=5)
    
    def _create_preview_area(self) -> None:
        """Создание области для отображения превью."""
        preview_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        preview_frame.pack(fill="both", expand=True, padx=5, pady=5)
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)
        
        # Label для изображения
        self._image_label = ctk.CTkLabel(
            preview_frame,
            text="Нет данных для превью",
            font=ctk.CTkFont(size=12),
            text_color="#808080"
        )
        self._image_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    
    def _open_sticker_editor(self) -> None:
        """Открытие редактора пресетов стикеров."""
        logger.info("[StickerPreview] Открытие редактора пресетов")
        
        dialog = StickerEditor(
            self,
            settings_service=self._settings_service
        )
        dialog.grab_set()
    
    def set_product(self, product: Product) -> None:
        """
        Установка товара для генерации превью.
        
        :param product: Товар для отображения в превью
        """
        self._current_product = product
        logger.debug(f"[StickerPreview] Генерация превью для {product.article}")
        
        # Получаем пресет из настроек
        preset = self._settings_service.get_setting('current_preset', {})
        
        # Генерируем стикер через сервис
        try:
            sticker_image = self._printer_service.generate_sticker(product, preset)
            self._display_image(sticker_image)
        except Exception as e:
            logger.error(f"[StickerPreview] Ошибка генерации: {e}")
            self._show_placeholder("Ошибка генерации")
    
    def _display_image(self, image: Image.Image | None) -> None:
        """Отображение изображения в превью."""
        if image is None:
            self._show_placeholder("Нет изображения")
            return
            
        try:
            # Масштабируем под размер label
            label_width = self._image_label.winfo_reqwidth() or 300
            label_height = self._image_label.winfo_reqheight() or 200
            
            # Сохраняем пропорции
            image.thumbnail((label_width, label_height), Image.Resampling.LANCZOS)
            
            # Конвертируем в PhotoImage для tkinter
            self._current_image = ImageTk.PhotoImage(image)
            
            # Обновляем label
            self._image_label.configure(
                image=self._current_image,
                text=""
            )
        except Exception as e:
            logger.error(f"[StickerPreview] Ошибка отображения: {e}")
            self._show_placeholder("Ошибка отображения")
    
    def _show_placeholder(self, message: str) -> None:
        """Показ заглушки вместо изображения."""
        self._current_image = None
        self._image_label.configure(
            image="",
            text=message,
            text_color="#808080"
        )
    
    def clear(self) -> None:
        """Очистка превью."""
        self._current_product = None
        self._show_placeholder("Нет данных для превью")
        logger.debug("[StickerPreview] Превью очищено")
