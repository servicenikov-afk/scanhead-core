"""Минимальный диалог отображения информации о товаре — совместимый с gui-framework-dev."""

import logging
from typing import Optional

import customtkinter as ctk

from gui.framework.dialog_base import DialogHandler
from libs.domain_models import Product

logger = logging.getLogger(__name__)


class ProductInfoDialog(DialogHandler):
    """Простой диалог для отображения базовой информации о товаре."""

    def __init__(
        self,
        master: any,
        product: Product,
        font_size: int = 14,
    ):
        """
        Инициализация диалога.

        Args:
            master: Родительский виджет.
            product: Объект продукта (из libs.domain_models).
            font_size: Размер шрифта.
        """
        super().__init__(master=master)
        self._product = product
        self._font_size = font_size

        # Настройка окна
        self.title(f"{product.name} ({product.model if hasattr(product, 'model') else product.article})")
        self.geometry("600x400")
        self.resizable(True, True)
        
        # Контент
        self._build_widgets()
        
        # Фокус
        self.grab_set()
        self.focus()

    def _build_widgets(self):
        """Сборка виджетов диалога — минимальная версия."""
        # Основной фрейм с отступами
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        content.grid_columnconfigure(1, weight=1)

        row = 0
        
        # Артикул
        ctk.CTkLabel(
            content, text="Артикул:", font=ctk.CTkFont(size=self._font_size, weight="bold")
        ).grid(row=row, column=0, sticky="e", padx=(0, 10), pady=5)
        ctk.CTkLabel(
            content, text=self._product.article, font=ctk.CTkFont(size=self._font_size)
        ).grid(row=row, column=1, sticky="w", pady=5)
        row += 1

        # Название
        ctk.CTkLabel(
            content, text="Наименование:", font=ctk.CTkFont(size=self._font_size, weight="bold")
        ).grid(row=row, column=0, sticky="ne", padx=(0, 10), pady=5)
        name_lbl = ctk.CTkLabel(
            content, text=self._product.name, font=ctk.CTkFont(size=self._font_size),
            wraplength=400, justify="left"
        )
        name_lbl.grid(row=row, column=1, sticky="w", pady=5)
        row += 1

        # Адреса хранения (если есть)
        if hasattr(self._product, 'storage_locations') and self._product.storage_locations:
            ctk.CTkLabel(
                content, text="Адреса:", font=ctk.CTkFont(size=self._font_size, weight="bold")
            ).grid(row=row, column=0, sticky="ne", padx=(0, 10), pady=5)
            addresses_text = "\n".join(self._product.storage_locations)
            ctk.CTkLabel(
                content, text=addresses_text, font=ctk.CTkFont(size=self._font_size),
                justify="left"
            ).grid(row=row, column=1, sticky="w", pady=5)
            row += 1

        # Штрихкоды (если есть)
        if hasattr(self._product, 'barcodes') and self._product.barcodes:
            ctk.CTkLabel(
                content, text="Штрихкоды:", font=ctk.CTkFont(size=self._font_size, weight="bold")
            ).grid(row=row, column=0, sticky="ne", padx=(0, 10), pady=5)
            barcodes_text = ", ".join(self._product.barcodes)
            ctk.CTkLabel(
                content, text=barcodes_text, font=ctk.CTkFont(size=self._font_size),
                wraplength=400, justify="left"
            ).grid(row=row, column=1, sticky="w", pady=5)
            row += 1

        # Кнопка закрытия
        close_btn = ctk.CTkButton(
            content, text="Закрыть", command=self.destroy,
            width=100, height=30
        )
        close_btn.grid(row=row, column=0, columnspan=2, pady=20)

    def destroy(self):
        """Переопределённый destroy для корректного закрытия."""
        self.grab_release()
        super().destroy()

# --- Конец файла gui/dialogs/product_info_dialog.py ---