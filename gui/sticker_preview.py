"""
Превью стикера: визуальное отображение макета этикетки.
Кнопка для открытия редактора пресетов.
"""

import logging
import os
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
        self._no_image: Optional[ctk.CTkImage] = None
        
        logger.debug("[StickerPreview] Инициализация")
        
        # Загрузка заглушки
        self._load_no_image()
        
        self._create_ui()

    def _load_no_image(self) -> None:
        """Загрузить изображение-заглушку."""
        try:
            # Путь к изображению относительно корня проекта
            script_dir = os.path.dirname(os.path.dirname(__file__))
            img_path = os.path.join(script_dir, "data", "images", "noimage.png")
            
            if os.path.exists(img_path):
                pil_image = Image.open(img_path)
                self._no_image = ctk.CTkImage(
                    light_image=pil_image,
                    dark_image=pil_image,
                    size=(200, 150)
                )
            else:
                logger.warning(f"[StickerPreview] Файл {img_path} не найден")
                self._no_image = None
        except Exception as e:
            logger.error(f"[StickerPreview] Ошибка загрузки noimage.png: {e}")
            self._no_image = None

    def _create_ui(self) -> None:
        """Создание интерфейса превью."""
        self.configure(fg_color="transparent")
        
        # Заголовок удален по ТЗ
        
        # Фрейм для превью
        self._preview_frame = ctk.CTkFrame(self)
        self._preview_frame.pack(fill="both", expand=True, padx=3, pady=3)
        
        # Метка для изображения/текста
        self._image_label = ctk.CTkLabel(
            self._preview_frame,
            text="Нет данных",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        self._image_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Показываем заглушку сразу
        self._show_placeholder()

    def _show_placeholder(self, text: str = "") -> None:
        """Показать заглушку вместо стикера."""
        # Очищаем фрейм
        for widget in self._preview_frame.winfo_children():
            widget.destroy()
        
        # Если есть загруженная картинка-заглушка - показываем только её
        if self._no_image:
            img_label = ctk.CTkLabel(
                self._preview_frame,
                image=self._no_image,
                text=""
            )
            img_label.place(relx=0.5, rely=0.5, anchor="center")

    def update_product(self, product: Optional[Product]) -> None:
        """Обновить превью данными товара."""
        self._current_product = product
        if product:
            logger.debug(f"[StickerPreview] Обновление превью для {product.article}")
            # Здесь будет логика генерации реального превью
            # Пока просто убираем заглушку или рисуем текст
            self._show_placeholder(f"Товар: {product.article}")
        else:
            self._show_placeholder("Нет данных")