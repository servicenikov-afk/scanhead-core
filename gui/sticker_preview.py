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
        
