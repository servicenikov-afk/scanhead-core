# --- gui/search_bar.py ---
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
import logging
from typing import Callable, Any, Optional, List, Dict
import threading
import customtkinter as ctk
from services.interfaces import ISearchService
from libs.domain_models import Product
from gui.widgets.suggestion_list import SuggestionList
logger = logging.getLogger(__name__)
class SearchBar(ctk.CTkFrame):
	def __init__(
		self,
		master: Any,
		search_service: ISearchService,
		on_search_result: Callable[[list], None],
		debounce_ms: int = 600,
		font_size: int = 18,
		auto_focus: bool = True,
		config: Optional[Dict[str, Any]] = None
	):
		super().__init__(master)
		self._search_service = search_service
		self._on_search_result = on_search_result
		self._debounce_ms = debounce_ms
		self._config = config or {}
		self._font_size = self._config.get("search_font_size", font_size)
		self._auto_focus = self._config.get("search_autofocus", auto_focus)
		self._focus_delay = self._config.get("search_autofocus_delay", 1.0)
		self._autoclear_enabled = self._config.get("search_autoclear_enabled", True)
		self._autoclear_delay = self._config.get("search_autoclear_delay", 3.0)
		self._timer: Optional[threading.Timer] = None
		self._last_query = ""
		self._suggestion_window: Optional[SuggestionList] = None
		self._update_geometry_after_id: Optional[str] = None
		self._pending_update_id: Optional[str] = None
		self._autoclear_after_id: Optional[str] = None
		entry_height = self._font_size + 8
		self._entry = ctk.CTkEntry(
			self,
			placeholder_text="🔍 Поиск по артикулу, названию или штрих-коду...",
			height=entry_height,
			font=ctk.CTkFont(size=self._font_size, family="Arial")
		)
		self._entry.pack(fill="both", expand=True, padx=5, pady=5)
		self._entry.bind("<KeyRelease>", self._on_key_release)
		self._entry.bind("<Button-1>", self._on_entry_click)
		self._entry.bind("<FocusOut>", lambda e: self._hide_suggestions())
		self._entry.bind("<Configure>", self._on_entry_configure)
		self._entry.bind("<Return>", self._on_enter_press)
		if self._auto_focus:
			delay_ms = int(self._focus_delay * 1000)
			self.after(delay_ms, self._set_initial_focus)
	def _set_initial_focus(self) -> None:
		if self._entry.winfo_exists():
			self._entry.focus_set()
	def _on_key_release(self, event) -> None:
		query = self._entry.get().strip()
		if not query:
			if self._timer:
				self._timer.cancel()
				self._timer = None
			self._hide_suggestions()
			self._on_search_result([])
			self._last_query = ""
			if self._autoclear_after_id:
				try:
					self.after_cancel(self._autoclear_after_id)
				except Exception:
					pass
				self._autoclear_after_id = None
			return
		if query == self._last_query:
			return
		self._last_query = query
		if self._timer:
			self._timer.cancel()
		self._timer = threading.Timer(
			self._debounce_ms / 1000.0,
			self._do_search,
			args=[query]
		)
		self._timer.start()
	def _on_enter_press(self, event) -> None:
		query = self._entry.get().strip()
		if not query:
			return "break"
		logger.info(f"[SearchBar] Enter нажат, отправка запроса: '{query}'")
		if self._timer:
			self._timer.cancel()
			self._timer = None
		self._do_search(query)
		self._hide_suggestions()
		if self._autoclear_enabled:
			self._clear_field_immediately()
		return "break"
	def _clear_field_immediately(self) -> None:
		if not self._entry.winfo_exists():
			return
		logger.debug("[SearchBar] Немедленная очистка поля поиска (Enter)")
		self._entry.delete(0, "end")
		self._last_query = ""
		if self._autoclear_after_id:
			try:
				self.after_cancel(self._autoclear_after_id)
			except Exception:
				pass
			self._autoclear_after_id = None
		if self._auto_focus:
			self._entry.focus_set()
	def _schedule_autoclear(self) -> None:
		if self._autoclear_after_id:
			try:
				self.after_cancel(self._autoclear_after_id)
			except Exception:
				pass
		delay_ms = int(self._autoclear_delay * 1000)
		self._autoclear_after_id = self.after(delay_ms, self._autoclear_field)
	def _autoclear_field(self) -> None:
		self._autoclear_after_id = None
		if not self._entry.winfo_exists():
			return
		logger.debug("[SearchBar] Автоочистка поля поиска (после задержки)")
		self._entry.delete(0, "end")
		self._last_query = ""
		if self._auto_focus:
			self._entry.focus_set()
	def _do_search(self, query: str) -> None:
		logger.info(f"[SearchBar] Поиск: '{query}'")
		self._search_service.search_async(query, self._on_search_complete)
	def _on_search_complete(self, products: list) -> None:
		logger.info(f"[SearchBar] Найдено: {len(products)}")
		if not products:
			self._hide_suggestions()
			self._on_search_result([])
			return
		if len(self._last_query) >= 3:
			self._show_suggestions(products)
		else:
			self._hide_suggestions()
		self.after(0, lambda: self._on_search_result(products))
		if self._autoclear_enabled:
			self._schedule_autoclear()
	def _show_suggestions(self, products: List[Product]) -> None:
		suggestions = []
		for p in products:
			text = f"{p.article} | {p.name[:80]}..." if len(p.name) > 80 else f"{p.article} | {p.name}"
			suggestions.append((text, p.article))
		suggestion_texts = [s[0] for s in suggestions]
		self._pending_update_id = self.after(1, lambda: self._do_show_suggestions(suggestion_texts))
	def _do_show_suggestions(self, suggestion_texts: List[str]) -> None:
		self._pending_update_id = None
		if not suggestion_texts:
			self._hide_suggestions()
			return
		try:
			if not self._entry.winfo_exists():
				return
			x = self._entry.winfo_rootx()
			y = self._entry.winfo_rooty() + self._entry.winfo_height() + 2
			entry_width = self._entry.winfo_width()
		except Exception as e:
			logger.warning(f"[SearchBar] Координаты entry: {e}")
			return
		if self._suggestion_window is None or not self._suggestion_window.winfo_exists():
			self._suggestion_window = SuggestionList(
				self._entry,
				on_select=self._on_suggestion_select,
				width=entry_width + 30,
				max_height=200,
				font_size=self._font_size
			)
		self._suggestion_window.show_suggestions(suggestion_texts, x, y)
	def _update_dropdown_geometry(self, x: int = None, y: int = None) -> None:
		if self._suggestion_window is None or not self._suggestion_window.winfo_exists():
			return
		if x is None:
			x = self._entry.winfo_rootx()
		if y is None:
			y = self._entry.winfo_rooty() + self._entry.winfo_height() + 2
		entry_width = self._entry.winfo_width()
		self._suggestion_window.frame.configure(width=entry_width)
		self._suggestion_window.geometry(f"+{x}+{y}")
	def _on_entry_configure(self, event=None) -> None:
		if self._update_geometry_after_id:
			try:
				self.after_cancel(self._update_geometry_after_id)
			except Exception:
				pass
		self._update_geometry_after_id = self.after(50, self._delayed_update_dropdown)
	def _delayed_update_dropdown(self) -> None:
		self._update_geometry_after_id = None
		if self._suggestion_window and self._suggestion_window.winfo_exists():
			self._update_dropdown_geometry()
	def _hide_suggestions(self) -> None:
		if self._suggestion_window:
			self._suggestion_window.hide()
	def _on_suggestion_select(self, display_text: str) -> None:
		logger.info(f"[SearchBar] Выбор: {display_text}")
		article = display_text.split(" | ")[0].strip()
		self._last_query = ""
		if self._timer:
			self._timer.cancel()
			self._timer = None
		self._entry.delete(0, "end")
		self._hide_suggestions()
		self._do_search(article)
		if self._auto_focus:
			delay_ms = int(self._focus_delay * 1000)
			self.after(delay_ms, self._restore_focus_after_select)
	def _restore_focus_after_select(self) -> None:
		if self._entry.winfo_exists():
			self._entry.focus_set()
	def apply_settings(self, config: dict) -> None:
		if "search_font_size" in config:
			self._font_size = config["search_font_size"]
			new_font = ctk.CTkFont(size=self._font_size, family="Arial")
			self._entry.configure(font=new_font)
			if self._suggestion_window and hasattr(self._suggestion_window, 'update_font_size'):
				self._suggestion_window.update_font_size(self._font_size)
		if "search_autofocus" in config:
			self._auto_focus = config["search_autofocus"]
		if "search_autofocus_delay" in config:
			self._focus_delay = config["search_autofocus_delay"]
		if "search_autoclear_enabled" in config:
			self._autoclear_enabled = config["search_autoclear_enabled"]
		if "search_autoclear_delay" in config:
			self._autoclear_delay = config["search_autoclear_delay"]
	def _on_entry_click(self, event) -> None:
		pass
	def get_query(self) -> str:
		return self._entry.get().strip()
	def clear(self) -> None:
		self._entry.delete(0, "end")
		self._last_query = ""
		self._hide_suggestions()
		if self._timer:
			self._timer.cancel()
			self._timer = None
		if self._update_geometry_after_id:
			try:
				self.after_cancel(self._update_geometry_after_id)
			except Exception:
				pass
			self._update_geometry_after_id = None
		if self._pending_update_id:
			try:
				self.after_cancel(self._pending_update_id)
			except Exception:
				pass
			self._pending_update_id = None
		if self._autoclear_after_id:
			try:
				self.after_cancel(self._autoclear_after_id)
			except Exception:
				pass
			self._autoclear_after_id = None