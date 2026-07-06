# --- gui/services/adapters/store_adapter.py ---
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
import sqlite3, threading, json
from pathlib import Path
from typing import Optional, List
import logging
logger=logging.getLogger(__name__)
class StoreAdapter:
	def __init__(self,db_path:str="data/databases/store/store.db"):
		project_root=Path(__file__).parent.parent.parent.parent
		self.db_path=project_root/db_path
		if not self.db_path.exists():
			logger.error(f"[StoreAdapter] БД НЕ НАЙДЕНА: {self.db_path}")
			logger.error(f"[StoreAdapter] Текущая директория: {Path.cwd()}")
			logger.error(f"[StoreAdapter] project_root: {project_root}")
			alt_path=Path(db_path)
			if alt_path.exists():
				self.db_path=alt_path
				logger.warning(f"[StoreAdapter] Используется альтернативный путь: {self.db_path}")
			else:logger.error(f"[StoreAdapter] Альтернативный путь тоже не найден: {alt_path}")
		logger.info(f"[StoreAdapter] Инициализация, путь к БД: {self.db_path}")
	def _get_connection(self)->sqlite3.Connection:
		if not self.db_path.exists():
			logger.warning(f"[StoreAdapter] БД не найдена: {self.db_path}")
			raise FileNotFoundError(f"Database not found: {self.db_path}")
		conn=sqlite3.connect(str(self.db_path))
		conn.row_factory=sqlite3.Row
		logger.debug(f"[StoreAdapter] Создано новое соединение в потоке {threading.current_thread().ident}")
		return conn
	def _ensure_schema(self):
		conn=self._get_connection()
		cursor=conn.cursor()
		cursor.execute("""CREATE TABLE IF NOT EXISTS storage_locations (article TEXT PRIMARY KEY,locations TEXT NOT NULL,alternative_names TEXT,notes TEXT,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
		conn.commit()
		logger.info("[StoreAdapter] Схема БД проверена")
	def get_location(self,article:str)->Optional[str]:
		conn=self._get_connection()
		cursor=conn.cursor()
		sql="SELECT locations FROM storage_locations WHERE article=?"
		try:
			cursor.execute(sql,(article,))
			row=cursor.fetchone()
			if row:
				locations_json=row['locations']
				locations=json.loads(locations_json) if locations_json else []
				location=locations[0] if locations else None
				logger.debug(f"[StoreAdapter] Адрес для {article}: {location}")
				return location
			return None
		except Exception as e:
			logger.error(f"[StoreAdapter] Ошибка получения адреса: {e}")
			return None
	def get_all_locations(self,article:str)->List[str]:
		conn=self._get_connection()
		cursor=conn.cursor()
		sql="SELECT locations FROM storage_locations WHERE article=?"
		try:
			cursor.execute(sql,(article,))
			row=cursor.fetchone()
			if row:
				locations_json=row['locations']
				return json.loads(locations_json) if locations_json else []
			return []
		except Exception as e:
			logger.error(f"[StoreAdapter] Ошибка получения адресов: {e}")
			return []
	def update_location(self,article:str,location:str)->bool:
		conn=self._get_connection()
		cursor=conn.cursor()
		current_locations=self.get_all_locations(article)
		if location not in current_locations:current_locations.append(location)
		locations_json=json.dumps(current_locations,ensure_ascii=False)
		sql="INSERT OR REPLACE INTO storage_locations (article,locations,updated_at) VALUES (?,?,CURRENT_TIMESTAMP)"
		try:
			cursor.execute(sql,(article,locations_json))
			conn.commit()
			logger.info(f"[StoreAdapter] Обновлён адрес для {article}: {location}")
			return True
		except Exception as e:
			logger.error(f"[StoreAdapter] Ошибка обновления адреса: {e}")
			conn.rollback()
			return False
	def set_locations(self,article:str,locations:List[str],notes:str=None)->bool:
		conn=self._get_connection()
		cursor=conn.cursor()
		locations_json=json.dumps(locations,ensure_ascii=False)
		sql="INSERT OR REPLACE INTO storage_locations (article,locations,notes,updated_at) VALUES (?,?,?,CURRENT_TIMESTAMP)"
		try:
			cursor.execute(sql,(article,locations_json,notes))
			conn.commit()
			logger.info(f"[StoreAdapter] Установлены адреса для {article}: {locations}")
			return True
		except Exception as e:
			logger.error(f"[StoreAdapter] Ошибка установки адресов: {e}")
			conn.rollback()
			return False
	def close(self):
		logger.debug("[StoreAdapter] Метод close() вызван, но соединения теперь управляются автоматически")