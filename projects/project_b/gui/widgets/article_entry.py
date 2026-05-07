import tkinter as tk
from tkinter import ttk
import logging
import inspect
from utils.article_normalizer import ArticleNormalizer
from commands import CommandHandler

logger = logging.getLogger(__name__)

class ArticleEntry(ttk.Frame):
    def __init__(self, parent, on_submit_callback, action_logger=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_submit = on_submit_callback
        self.action_logger = action_logger
        self.buffer = ""
        self.timeout_id = None
        self.timeout_ms = 50
        self._create_widgets()
    
    def _create_widgets(self):
        self.label = ttk.Label(self, text="Артикул / Штрих-код:")
        self.label.pack(anchor=tk.W, padx=5, pady=(5,0))
        entry_frame = ttk.Frame(self)
        entry_frame.pack(fill=tk.X, padx=5, pady=2)
        vcmd = (self.register(self._validate_length), '%P')
        self.entry = ttk.Entry(entry_frame, font=('TkFixedFont',12), validate='key', validatecommand=vcmd, width=35)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.clear_btn = ttk.Button(entry_frame, text="✗", width=3, command=self.clear)
        self.clear_btn.pack(side=tk.RIGHT, padx=(2,0))
        self.paste_btn = ttk.Button(entry_frame, text="📋", width=3, command=self._paste_from_clipboard)
        self.paste_btn.pack(side=tk.RIGHT, padx=(2,0))
        self.entry.bind('<Return>', self._on_enter)
        self.entry.bind('<Key>', self._on_key)
        self.entry.focus_set()
        self.info_label = ttk.Label(self, text="Готов к сканированию", foreground="gray")
        self.info_label.pack(anchor=tk.W, padx=5, pady=(0,5))
        fix_frame = ttk.Frame(self)
        fix_frame.pack(fill=tk.X, padx=5, pady=(0,5))
        self.fix_btn = ttk.Button(fix_frame, text="🔧 Исправить раскладку", width=18, command=self._fix_layout)
        self.fix_btn.pack(side=tk.LEFT)
        self.fix_info = ttk.Label(fix_frame, text="", foreground="blue")
        self.fix_info.pack(side=tk.LEFT, padx=(10,0))
    
    def _validate_length(self, new_value):
        return len(new_value) <= 35
    
    def _fix_layout(self):
        current = self.entry.get()
        if current:
            fixed = ArticleNormalizer.fix_keyboard_layout(current)
            if fixed != current:
                self.entry.delete(0, tk.END)
                self.entry.insert(0, fixed)
                self.fix_info.config(text=f"✓ Раскладка исправлена: '{current[:15]}' → '{fixed[:15]}'", foreground="green")
                if CommandHandler.is_command(fixed):
                    self.after(100, lambda: self._on_enter(None))
            else:
                self.fix_info.config(text="✗ Текст уже в правильной раскладке", foreground="orange")
            self.after(2000, lambda: self.fix_info.config(text=""))
    
    def _paste_from_clipboard(self):
        try:
            text = self.clipboard_get()
            if text:
                self.entry.delete(0, tk.END)
                self.entry.insert(0, text.strip()[:35])
                self.fix_info.config(text="✓ Вставлено из буфера", foreground="green")
                self.after(1500, lambda: self.fix_info.config(text=""))
                self._on_enter(None)
        except Exception:
            self.fix_info.config(text="Ошибка вставки", foreground="red")
            self.after(1500, lambda: self.fix_info.config(text=""))
    
    def _on_key(self, event):
        if self.timeout_id:
            self.after_cancel(self.timeout_id)
            self.timeout_id = None
        if event.keysym != 'Return':
            self.timeout_id = self.after(self.timeout_ms, self._reset_buffer)
    
    def _on_enter(self, event):
        self.timeout_id = None
        raw = self.entry.get().strip()
        if raw:
            if len(raw) > 35:
                raw = raw[:35]
                self.entry.delete(0, tk.END)
                self.entry.insert(0, raw)
            is_cmd = False
            normalized = raw
            if 'CMD' in raw.upper() or 'хСЬВ' in raw or 'ХСЬВ' in raw:
                normalized = ArticleNormalizer.normalize_command(raw)
                is_cmd = True
            if not is_cmd:
                normalized = ArticleNormalizer.normalize(raw)
            if normalized != raw:
                self.fix_info.config(text=f"Раскладка исправлена: '{raw[:20]}' → '{normalized[:20]}'", foreground="blue")
                self.after(2000, lambda: self.fix_info.config(text=""))
            if CommandHandler.is_command(normalized):
                cmd = CommandHandler.parse(normalized)
                if cmd:
                    if self.action_logger:
                        self.action_logger.add_command(raw, cmd)
                    self.info_label.config(text=f"⚡ Команда: {cmd}", foreground="purple")
                    sig = inspect.signature(self.on_submit)
                    if 'is_command' in sig.parameters:
                        self.on_submit(normalized, is_command=True)
                    else:
                        self.on_submit(normalized)
                else:
                    if self.action_logger:
                        self.action_logger.add_command(raw, 'UNKNOWN', success=False, message="Неизвестная команда")
                    self.info_label.config(text=f"⚠ Неизвестная команда: {normalized}", foreground="red")
                self.after(1500, lambda: self.info_label.config(text="Готов к сканированию", foreground="gray"))
                self.entry.delete(0, tk.END)
                return 'break'
            if self.action_logger:
                self.action_logger.add_scan(raw, normalized, "", success=None)
            self.on_submit(normalized)
            self.entry.delete(0, tk.END)
            self.info_label.config(text=f"✓ Отсканировано: {normalized[:30]}", foreground="green")
            self.after(2000, lambda: self.info_label.config(text="Готов к сканированию", foreground="gray"))
        else:
            self.info_label.config(text="Введите артикул", foreground="orange")
            self.after(1500, lambda: self.info_label.config(text="Готов к сканированию", foreground="gray"))
        return 'break'
    
    def _reset_buffer(self):
        self.buffer = ""
        self.timeout_id = None
    
    def clear(self):
        self.entry.delete(0, tk.END)
        self.fix_info.config(text="")
    
    def focus(self):
        self.entry.focus_set()
    
    def set_value(self, value: str):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value[:35])