"""
DB Manager Models
Модели данных для работы с базой данных.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class DataRecord:
    """
    Модель записи данных с расширенным набором полей.
    
    Атрибуты:
        id: Уникальный идентификатор записи
        article: Канонический артикул товара
        barcode: Штрих-код (EAN-13, UPC-A и т.д.)
        name_original: Наименование на оригинальном языке
        name_sticker: Наименование для стикеров (сокращенное/адаптированное)
        article_old: Старый артикул (если был изменен)
        articles_alternative: Список альтернативных артикулов
        tags: Теги (модели оборудования, категории и т.д.)
        created_at: Дата создания записи
        updated_at: Дата последнего обновления
        metadata: Дополнительные метаданные (произвольный dict)
    """
    
    id: Optional[int] = None
    article: str = ""
    barcode: Optional[str] = None
    name_original: Optional[str] = None
    name_sticker: Optional[str] = None
    article_old: Optional[str] = None
    articles_alternative: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Инициализация дат при создании новой записи."""
        if self.id is None and self.created_at is None:
            self.created_at = datetime.now()
        
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def add_alternative_article(self, article: str):
        """Добавить альтернативный артикул."""
        if article and article not in self.articles_alternative:
            self.articles_alternative.append(article)
            self.updated_at = datetime.now()

    def add_tag(self, tag: str):
        """Добавить тег."""
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать запись в словарь."""
        return {
            'id': self.id,
            'article': self.article,
            'barcode': self.barcode,
            'name_original': self.name_original,
            'name_sticker': self.name_sticker,
            'article_old': self.article_old,
            'articles_alternative': self.articles_alternative,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'metadata': self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataRecord':
        """Создать запись из словаря."""
        # Обработка дат
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        updated_at = data.get('updated_at')
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        return cls(
            id=data.get('id'),
            article=data.get('article', ''),
            barcode=data.get('barcode'),
            name_original=data.get('name_original'),
            name_sticker=data.get('name_sticker'),
            article_old=data.get('article_old'),
            articles_alternative=data.get('articles_alternative', []),
            tags=data.get('tags', []),
            created_at=created_at,
            updated_at=updated_at,
            metadata=data.get('metadata', {}),
        )
