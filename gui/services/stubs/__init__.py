"""Заглушки сервисов."""
from .search_service_stub import StubSearchService
from .product_repo_stub import StubProductRepository
from .image_service_stub import StubImageService
from .settings_service_stub import StubSettingsService
from .printer_service_stub import StubPrinterService

__all__ = [
    "StubSearchService",
    "StubProductRepository",
    "StubImageService",
    "StubSettingsService",
    "StubPrinterService",
]
