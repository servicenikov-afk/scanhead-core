"""Интерфейсы сервисов."""
from .search_service import ISearchService
from .product_repo import IProductRepository
from .image_service import IImageService
from .settings_service import ISettingsService
from .printer_service import IPrinterService

__all__ = [
    "ISearchService",
    "IProductRepository",
    "IImageService",
    "ISettingsService",
    "IPrinterService",
]
