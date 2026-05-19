"""Загрузка тестовых данных из JSON-файлов."""

import json
from pathlib import Path
from typing import List, Optional

from libs.domain_models import Product, Address


class JsonMockLoader:
    """Загрузка тестовых данных из JSON-файлов."""

    def __init__(self, data_dir: Path | str = "data/mocks"):
        self.data_dir = Path(data_dir)
        self._products_cache: List[Product] = []
        self._addresses_cache: List[Address] = []
        self._load_cache()

    def _load_cache(self) -> None:
        """Ленивая загрузка данных в кэш."""
        products_file = self.data_dir / "products.json"
        addresses_file = self.data_dir / "addresses.json"

        if products_file.exists():
            self._products_cache = self._parse_products(products_file)

        if addresses_file.exists():
            self._addresses_cache = self._parse_addresses(addresses_file)

    def _parse_products(self, file_path: Path) -> List[Product]:
        """Парсинг JSON в объекты Product."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        products = []
        for item in data:
            product = Product(
                article=item.get("article", ""),
                name=item.get("name", ""),
                barcodes=item.get("barcodes", []),
                address=item.get("address"),
            )
            products.append(product)

        return products

    def _parse_addresses(self, file_path: Path) -> List[Address]:
        """Парсинг JSON в объекты Address."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return [
            Address(
                code=item.get("code", ""),
                description=item.get("description", ""),
            )
            for item in data
        ]

    def load_products(self) -> List[Product]:
        """Загрузить список тестовых товаров."""
        return self._products_cache.copy()

    def load_addresses(self) -> List[Address]:
        """Загрузить список тестовых адресов."""
        return self._addresses_cache.copy()

    def get_product_by_article(self, article: str) -> Optional[Product]:
        """Найти товар по артикулу в моках."""
        if not article:
            return None

        article_lower = article.lower()
        for product in self._products_cache:
            if (
                (product.article and article_lower in product.article.lower())
                or (product.name and article_lower in product.name.lower())
            ):
                return product
        return None
