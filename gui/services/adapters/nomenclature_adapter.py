# --- gui/services/adapters/nomenclature_adapter.py ---
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
import sqlite3, json, threading
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable
import logging
from libs.domain_models import Product
logger=logging.getLogger(__name__)
class NomenclatureAdapter:
	def __init__(self,db_path:str="data/databases/nomenclature/nomenclature.db"):
		project_root=Path(__file__).parent.parent.parent.parent
		self.db_path=project_root/db_path
		if not self.db_path.exists():
			logger.error(f"[NomenclatureAdapter] БД НЕ НАЙДЕНА: {self.db_path}")
			logger.error(f"[NomenclatureAdapter] Текущая директория: {Path.cwd()}")
			logger.error(f"[NomenclatureAdapter] project_root: {project_root}")
			alt_path=Path(db_path)
			if alt_path.exists():
				self.db_path=alt_path
				logger.warning(f"[NomenclatureAdapter] Используется альтернативный путь: {self.db_path}")
			else:logger.error(f"[NomenclatureAdapter] Альтернативный путь тоже не найден: {alt_path}")
		self._connection:Optional[sqlite3.Connection]=None
		logger.info(f"[NomenclatureAdapter] Инициализация, путь к БД: {self.db_path}")
	def _get_connection(self)->sqlite3.Connection:
		if self._connection is None:
			if not self.db_path.exists():
				logger.warning(f"[NomenclatureAdapter] БД не найдена: {self.db_path}")
				raise FileNotFoundError(f"Database not found: {self.db_path}")
			self._connection=sqlite3.connect(f"file:{self.db_path}?mode=ro",uri=True)
			self._connection.row_factory=sqlite3.Row
			logger.info(f"[NomenclatureAdapter] Подключено к {self.db_path} (read-only)")
		return self._connection
	def search_async(self,query:str,callback:Callable[[List['Product']],None])->None:
		def _search_thread():
			results=self.search(query)
			callback(results)
		thread=threading.Thread(target=_search_thread,daemon=True)
		thread.start()
	def search(self,query:str)->List[Product]:
		if not self.db_path.exists():
			logger.warning(f"[NomenclatureAdapter] БД не найдена: {self.db_path}")
			return []
		conn=sqlite3.connect(f"file:{self.db_path}?mode=ro",uri=True)
		conn.row_factory=sqlite3.Row
		try:
			cursor=conn.cursor()
			cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
			table_row=cursor.fetchone()
			if not table_row:
				logger.error("[NomenclatureAdapter] Таблицы в БД не найдены")
				return []
			table_name=table_row['name']
			logger.debug(f"[NomenclatureAdapter] Используется таблица: {table_name}")
			query_pattern=f"%{query}%"
			sql=f"""
				SELECT DISTINCT article, name, barcodes, unit
				FROM {table_name}
				WHERE LOWER(article) LIKE LOWER(?)
				   OR LOWER(name) LIKE LOWER(?)
				   OR LOWER(barcodes) LIKE LOWER(?)
				LIMIT 50
			"""
			cursor.execute(sql,(query_pattern,query_pattern,query_pattern))
			rows=cursor.fetchall()
			products=[]
			for row in rows:
				article=row['article'] or ''
				name=row['name'] or ''
				barcodes_raw=row['barcodes'] or ''
				unit=row['unit'] or ''
				if barcodes_raw:
					try:barcodes=json.loads(barcodes_raw) if isinstance(barcodes_raw,str) else barcodes_raw
					except (json.JSONDecodeError,TypeError):barcodes=barcodes_raw if isinstance(barcodes_raw,list) else []
				else:barcodes=[]
				products.append(Product(article=article,name=name,barcodes=barcodes,unit=unit,storage_locations=[]))
			logger.info(f"[NomenclatureAdapter] Найдено {len(products)} товаров по запросу '{query}'")
			return products
		except Exception as e:
			logger.error(f"[NomenclatureAdapter] Ошибка поиска: {e}")
			return []
		finally:conn.close()
	def get_by_article(self,article:str)->Optional[Product]:
		if not self.db_path.exists():
			logger.warning(f"[NomenclatureAdapter] БД не найдена: {self.db_path}")
			return None
		conn=sqlite3.connect(f"file:{self.db_path}?mode=ro",uri=True)
		conn.row_factory=sqlite3.Row
		cursor=conn.cursor()
		cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
		table_row=cursor.fetchone()
		if not table_row:
			logger.error("[NomenclatureAdapter] Таблицы в БД не найдены")
			conn.close()
			return None
		table_name=table_row['name']
		sql=f"SELECT article,name,barcodes,unit FROM {table_name} WHERE article=?"
		try:
			cursor.execute(sql,(article,))
			row=cursor.fetchone()
			if row:
				barcodes_raw=row['barcodes']
				if barcodes_raw:
					try:barcodes=json.loads(barcodes_raw) if isinstance(barcodes_raw,str) else barcodes_raw
					except (json.JSONDecodeError,TypeError):barcodes=barcodes_raw if isinstance(barcodes_raw,list) else []
				else:barcodes=[]
				return Product(article=row['article'],name=row['name'],barcodes=barcodes,unit=row['unit'])
			return None
		except Exception as e:
			logger.error(f"[NomenclatureAdapter] Ошибка получения товара: {e}")
			return None
		finally:conn.close()
	def close(self):
		if self._connection:
			self._connection.close()
			self._connection=None
			logger.info("[NomenclatureAdapter] Соединение закрыто")