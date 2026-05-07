# modules/nomenclature.py
"""
Модель работы с номенклатурой из CSV файла.
"""

import requests
import logging
import re
import difflib
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
import tempfile
import csv
import os

logger = logging.getLogger(__name__)


class FuzzySearch:
    """Нечеткий поиск по тексту"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Нормализация текста для поиска"""
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r'[^\w\sа-яА-Яa-zA-Z0-9]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    @staticmethod
    def find_best_match(query: str, choices: List[str], threshold: float = 0.6) -> Optional[int]:
        """Находит лучший матч среди вариантов"""
        if not query or not choices:
            return None
        
        normalized_query = FuzzySearch.normalize_text(query)
        matches = difflib.get_close_matches(
            normalized_query,
            [FuzzySearch.normalize_text(c) for c in choices],
            n=1,
            cutoff=threshold
        )
        
        if matches:
            normalized_choices = [FuzzySearch.normalize_text(c) for c in choices]
            try:
                return normalized_choices.index(matches[0])
            except ValueError:
                return None
        return None


class NomenclatureCSV:
    """Работа с номенклатурой из CSV файла (без SQLite)"""
    
    def __init__(self, csv_path: str = None):
        self.csv_path = Path(csv_path) if csv_path else None
        self.data = []  # Список записей: [(name, article_correct, barcodes), ...]
        self.loaded = False
    
    @staticmethod
    def normalize_article(article: str) -> str:
        """Нормализация артикула согласно инструкции"""
        if not article:
            return ""
        
        # 1. Удалить лишние пробелы и кавычки
        result = str(article).strip().strip('"\'').strip()
        
        # 2. Заменить переносы строк на пробелы
        result = result.replace('\n', ' ').replace('\r', ' ')
        
        # 3. Убрать множественные пробелы
        result = re.sub(r'\s+', ' ', result).strip()
        
        # 4. Если есть '/', взять первую непустую часть
        if '/' in result:
            parts = [part.strip() for part in result.split('/') if part.strip()]
            if parts:
                result = parts[0]
        
        return result
    
    def download_and_load(self, csv_url: str, local_path: str = None) -> bool:
        """Скачивает и загружает CSV файл"""
        try:
            logger.info(f"Скачивание CSV из {csv_url}")
            response = requests.get(csv_url, timeout=30)
            response.raise_for_status()
            
            # Если указан локальный путь, сохраняем
            if local_path:
                self.csv_path = Path(local_path)
                self.csv_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(self.csv_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"CSV сохранен: {self.csv_path}")
                return self.load_from_file(self.csv_path)
            else:
                # Загружаем прямо из памяти
                return self._load_from_bytes(response.content)
                
        except Exception as e:
            logger.error(f"Ошибка загрузки CSV: {e}", exc_info=True)
            return False
    
    def load_from_file(self, csv_path: str) -> bool:
        """Загружает CSV из файла"""
        try:
            self.csv_path = Path(csv_path)
            
            if not self.csv_path.exists():
                logger.error(f"Файл не найден: {csv_path}")
                return False
            
            with open(self.csv_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
            
            return self._load_from_bytes(content.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Ошибка загрузки файла {csv_path}: {e}")
            return False
    
    def _load_from_bytes(self, content: bytes) -> bool:
        """Загружает данные из байтов CSV"""
        try:
            self.data = []
            seen_articles = set()
            
            # Декодируем и читаем CSV
            content_str = content.decode('utf-8-sig')
            lines = content_str.splitlines()
            
            # Определяем разделитель
            first_line = lines[0] if lines else ""
            if ';' in first_line:
                delimiter = ';'
            elif '\t' in first_line:
                delimiter = '\t'
            else:
                delimiter = ','
            
            # Читаем CSV
            csv_reader = csv.DictReader(lines, delimiter=delimiter)
            fieldnames = csv_reader.fieldnames or []
            
            # Приводим к нижнему регистру для поиска
            fieldnames_lower = [f.lower() for f in fieldnames]
            
            # Ищем нужные колонки
            name_col = None
            article_col = None
            barcode_col = None
            
            for col in fieldnames:
                col_lower = col.lower()
                if col_lower in ['наименование', 'название', 'имя', 'name', 'description']:
                    name_col = col
                elif col_lower in ['артикул', 'article', 'код', 'code', 'articul']:
                    article_col = col
                elif col_lower in ['штрих-коды', 'штрихкоды', 'barcodes', 'barcode']:
                    barcode_col = col
            
            if not article_col:
                logger.error("Не найдена колонка с артикулом")
                return False
            
            # Обрабатываем строки
            for row in csv_reader:
                name = row.get(name_col, "").strip() if name_col else ""
                article_correct = row.get(article_col, "").strip()
                barcodes = row.get(barcode_col, "").strip() if barcode_col else ""
                
                if not article_correct:
                    continue
                
                # Проверяем дубликаты
                if article_correct in seen_articles:
                    logger.warning(f"Пропущен дубликат: {article_correct}")
                    continue
                
                seen_articles.add(article_correct)
                self.data.append((name, article_correct, barcodes))
            
            self.loaded = True
            logger.info(f"Загружено записей из CSV: {len(self.data)}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка парсинга CSV: {e}")
            return False
    
    def find_by_source_article(self, source_article: str) -> Optional[Tuple[str, str]]:
        """Поиск по исходному артикулу через штрих-коды"""
        if not source_article or not self.loaded:
            return None
        
        # Нормализуем исходный артикул
        normalized_source = self.normalize_article(source_article)
        if not normalized_source:
            return None
        
        for name, article_correct, barcodes in self.data:
            if not barcodes:
                continue
            
            # Разбиваем штрих-коды и нормализуем каждый
            barcode_list = [self.normalize_article(b.strip()) 
                           for b in str(barcodes).split(',') if b.strip()]
            
            # Ищем совпадение
            for barcode in barcode_list:
                if barcode == normalized_source:
                    logger.debug(f"Найдено совпадение: {normalized_source} -> {article_correct}")
                    return (name, article_correct)
        
        return None
    
    def find_by_name_fuzzy(self, name_query: str, threshold: float = 0.6, limit: int = 10) -> List[Tuple[str, str]]:
        """Нечеткий поиск по наименованию, возвращает список вариантов"""
        if not name_query or not self.loaded:
            return []
        
        results = []
        norm_query = FuzzySearch.normalize_text(name_query)
        
        for name, article, _ in self.data:
            norm_name = FuzzySearch.normalize_text(name)
            score = difflib.SequenceMatcher(None, norm_query, norm_name).ratio()
            if score >= threshold:
                results.append((score, name, article))
        
        # Сортируем по убыванию релевантности
        results.sort(reverse=True)
        return [(name, article) for score, name, article in results][:limit]
    
    def find_article_for_invoice_position(self, source_article: str, source_name: str) -> Tuple[str, str, bool]:
        """
        Основной метод: ищет правильный артикул для позиции накладной
        
        Args:
            source_article: "сырой" артикул из накладной
            source_name: "сырое" наименование из накладной
            
        Returns:
            Tuple[правильный_артикул, правильное_название, найден_ли]
        """
        logger.debug(f"Поиск артикула для: article='{source_article}', name='{source_name}'")
        
        # ШАГ 1: Поиск по артикулу (через штрих-коды)
        if source_article:
            result = self.find_by_source_article(source_article)
            if result:
                correct_name, correct_article = result
                logger.info(f"Найдено по артикулу: '{source_article}' -> '{correct_article}'")
                return correct_article, correct_name, True
        
        # ШАГ 2: Нечеткий поиск по наименованию
        if source_name:
            result = self.find_by_name_fuzzy(source_name, threshold=0.6)
            if result:
                correct_name, correct_article = result
                logger.info(f"Найдено по имени: '{source_name}' -> '{correct_article}'")
                return correct_article, correct_name, True
        
        # ШАГ 3: Артикул не найден
        normalized_article = self.normalize_article(source_article) or ""
        logger.debug(f"Артикул не найден, используем исходные данные")
        return normalized_article, source_name or normalized_article, False
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику"""
        stats = {
            'status': 'loaded' if self.loaded else 'not_loaded',
            'records': len(self.data) if self.loaded else 0,
            'csv_path': str(self.csv_path) if self.csv_path else 'none'
        }
        
        if self.loaded and len(self.data) > 0:
            stats['sample'] = [
                {'article': self.data[0][1], 'name': self.data[0][0][:50] + '...'}
            ]
        
        return stats