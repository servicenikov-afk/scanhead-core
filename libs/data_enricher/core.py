"""
Data Enricher Core
Обогащение и преобразование сырых данных в полноценные бизнес-объекты.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

from .models import DataRecord


@dataclass
class EnrichmentResult:
    """Результат обогащения данных."""
    
    success: bool
    record: Optional[DataRecord] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    enriched_fields: List[str] = field(default_factory=list)
    
    @classmethod
    def ok(cls, record: DataRecord, enriched_fields: List[str] = None) -> 'EnrichmentResult':
        """Создать успешный результат."""
        return cls(
            success=True,
            record=record,
            enriched_fields=enriched_fields or []
        )
    
    @classmethod
    def fail(cls, errors: List[str], warnings: List[str] = None) -> 'EnrichmentResult':
        """Создать результат с ошибкой."""
        return cls(
            success=False,
            errors=errors,
            warnings=warnings or []
        )


class DataEnricher:
    """
    Обогащение сырых данных до полноценных бизнес-объектов.
    
    Пример использования:
        enricher = DataEnricher()
        
        # Добавление обработчиков
        enricher.add_processor("normalize_article", normalize_article)
        enricher.add_processor("generate_sticker_name", generate_sticker_name)
        
        # Обогащение
        raw_data = {"article": "  abc-123 ", "name_original": "Длинное наименование товара"}
        result = enricher.enrich(raw_data)
        
        if result.success:
            record = result.record
    """

    def __init__(self):
        self.processors: Dict[str, Callable[[Dict[str, Any], DataRecord], DataRecord]] = {}
        self.validators: Dict[str, Callable[[Dict[str, Any]], bool]] = {}

    def add_processor(self, name: str, processor: Callable[[Dict[str, Any], DataRecord], DataRecord]):
        """
        Добавить процессор обогащения.
        
        Args:
            name: Имя процессора
            processor: Функция, принимающая (raw_data, record) и возвращающая обновленный record
        """
        self.processors[name] = processor

    def remove_processor(self, name: str):
        """Удалить процессор по имени."""
        if name in self.processors:
            del self.processors[name]

    def add_validator(self, name: str, validator: Callable[[Dict[str, Any]], bool]):
        """
        Добавить валидатор сырых данных.
        
        Args:
            name: Имя валидатора
            validator: Функция, принимающая raw_data и возвращающая bool
        """
        self.validators[name] = validator

    def enrich(self, raw_data: Dict[str, Any]) -> EnrichmentResult:
        """
        Обогатить сырые данные до DataRecord.
        
        Args:
            raw_data: Словарь с сырыми данными
            
        Returns:
            EnrichmentResult с результатом обогащения
        """
        errors = []
        warnings = []
        enriched_fields = []

        # Валидация входных данных
        for name, validator in self.validators.items():
            try:
                if not validator(raw_data):
                    errors.append(f"Валидатор '{name}' не прошел")
            except Exception as e:
                errors.append(f"Ошибка валидатора '{name}': {str(e)}")

        if errors:
            return EnrichmentResult.fail(errors, warnings)

        # Создание базовой записи
        try:
            record = DataRecord.from_dict(raw_data)
        except Exception as e:
            return EnrichmentResult.fail([f"Ошибка создания записи: {str(e)}"], warnings)

        # Применение процессоров
        for name, processor in self.processors.items():
            try:
                old_record = record
                record = processor(raw_data, record)
                
                # Определение измененных полей
                if record != old_record:
                    enriched_fields.append(name)
                    
            except Exception as e:
                warnings.append(f"Процессор '{name}' вернул ошибку: {str(e)}")

        return EnrichmentResult.ok(record, enriched_fields)

    def enrich_batch(self, raw_data_list: List[Dict[str, Any]]) -> List[EnrichmentResult]:
        """
        Обогатить пакет данных.
        
        Args:
            raw_data_list: Список словарей с сырыми данными
            
        Returns:
            Список EnrichmentResult
        """
        return [self.enrich(data) for data in raw_data_list]


# Стандартные процессоры обогащения

def normalize_article_processor(raw_data: Dict[str, Any], record: DataRecord) -> DataRecord:
    """
    Процессор нормализации артикула.
    Использует article_normalizer если доступен.
    """
    if record.article:
        try:
            from libs.article_normalizer import ArticleNormalizer
            normalizer = ArticleNormalizer()
            record.article = normalizer.normalize(record.article)
        except ImportError:
            # Fallback: простая нормализация
            record.article = record.article.strip().upper()
    
    return record


def generate_sticker_name_processor(raw_data: Dict[str, Any], record: DataRecord) -> DataRecord:
    """
    Процессор генерации наименования для стикеров.
    Если name_sticker не задан, создается сокращенная версия name_original.
    """
    if record.name_original and not record.name_sticker:
        # Простая логика сокращения
        name = record.name_original
        if len(name) > 30:
            # Берем первые слова до 30 символов
            words = name.split()
            short_name = ""
            for word in words:
                if len(short_name) + len(word) + 1 <= 30:
                    short_name = short_name + " " + word if short_name else word
                else:
                    break
            record.name_sticker = short_name.strip()
        else:
            record.name_sticker = name
    
    return record


def extract_tags_from_metadata_processor(raw_data: Dict[str, Any], record: DataRecord) -> DataRecord:
    """
    Процессор извлечения тегов из метаданных.
    """
    metadata = raw_data.get("metadata", {})
    
    if isinstance(metadata, dict):
        # Извлечение тегов из metadata['tags'] если есть
        meta_tags = metadata.get("tags", [])
        if isinstance(meta_tags, list):
            for tag in meta_tags:
                if tag and tag not in record.tags:
                    record.tags.append(tag)
    
    return record


def set_default_values_processor(raw_data: Dict[str, Any], record: DataRecord) -> DataRecord:
    """
    Процессор установки значений по умолчанию.
    """
    if record.created_at is None:
        record.created_at = datetime.now()
    
    if record.updated_at is None:
        record.updated_at = datetime.now()
    
    return record
