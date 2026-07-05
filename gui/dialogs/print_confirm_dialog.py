# --- gui/dialogs/print_confirm_dialog.py ---
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
import logging
import customtkinter as ctk
import tkinter as tk
from typing import Callable, Optional
logger = logging.getLogger(__name__)
class PrintConfirmDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        total_count: int,
        preset_name: str,
        on_confirm: Callable[[], None],
        on_cancel: Optional[Callable[[], None]] = None,
    ):
        super().__init__(master)
        self._on_confirm = on_confirm
        self._on_cancel = on_cancel
        self._total_count = total_count
        self._preset_name = preset_name
        self._confirmed = False
        self._closed = False
        self.title("Подтверждение печати")
        self.geometry("420x240")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._handle_cancel)
        self._create_ui()
        self.after(100, self.focus_force)
    def _create_ui(self) -> None:
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=(20, 10))
        info_label = ctk.CTkLabel(
            content,
            text=f"Будет напечатано стикеров: {self._total_count}",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        info_label.pack(pady=(0, 5))
        preset_label = ctk.CTkLabel(
            content,
            text=f"Пресет: {self._preset_name}",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray60"),
        )
        preset_label.pack(pady=(0, 15))
        self._status_label = ctk.CTkLabel(
            content,
            text="Готов к печати",
            font=ctk.CTkFont(size=12),
        )
        self._status_label.pack(pady=(0, 5))
        self._progress = ctk.CTkProgressBar(content, mode="determinate")
        self._progress.pack(fill="x", pady=(0, 10))
        self._progress.set(0)
        self._progress.pack_forget()
        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=20, pady=(0, 15))
        self._btn_cancel = ctk.CTkButton(
            buttons,
            text="Отмена",
            width=120,
            fg_color="#808080",
            hover_color="#606060",
            command=self._handle_cancel,
        )
        self._btn_cancel.pack(side="left", padx=(0, 10))
        self._btn_confirm = ctk.CTkButton(
            buttons,
            text="Печать",
            width=120,
            command=self._handle_confirm,
        )
        self._btn_confirm.pack(side="right")
    def _handle_confirm(self) -> None:
        if self._confirmed:
            return
        self._confirmed = True
        self._btn_confirm.configure(state="disabled", text="Печать...")
        self._btn_cancel.configure(state="disabled")
        self._status_label.configure(text="Подготовка...", text_color=("gray40", "gray60"))
        logger.info(f"[PrintConfirmDialog] Подтверждена печать {self._total_count} стикеров")
        try:
            self._on_confirm()
        except Exception as e:
            logger.error(f"[PrintConfirmDialog] Ошибка в on_confirm: {e}", exc_info=True)
            self.show_error(f"Ошибка запуска печати: {e}")
    def _handle_cancel(self) -> None:
        if self._closed:
            return
        self._closed = True
        logger.info("[PrintConfirmDialog] Печать отменена пользователем")
        if self._on_cancel:
            try:
                self._on_cancel()
            except Exception as e:
                logger.error(f"[PrintConfirmDialog] Ошибка в on_cancel: {e}", exc_info=True)
        self._safe_destroy()
    def show_progress(self, current: int, total: int, status: str = "") -> None:
        if self._closed:
            return
        try:
            if not self._progress.winfo_ismapped():
                self._progress.pack(fill="x", pady=(0, 10), before=self._status_label.master)
            progress = current / total if total > 0 else 0
            self._progress.set(progress)
            text = status or f"Рендеринг: {current}/{total}"
            self._status_label.configure(text=text)
        except tk.TclError:
            pass
        except Exception as e:
            logger.error(f"[PrintConfirmDialog] Ошибка обновления прогресса: {e}")
    def show_error(self, message: str) -> None:
        if self._closed:
            return
        try:
            self._status_label.configure(text=f"Ошибка: {message}", text_color="#C0392B")
            self._btn_confirm.configure(state="disabled", text="Ошибка")
            self._btn_cancel.configure(state="normal", text="Закрыть")
            self._closed = True
            logger.error(f"[PrintConfirmDialog] Ошибка печати: {message}")
        except tk.TclError:
            pass
        except Exception as e:
            logger.error(f"[PrintConfirmDialog] Ошибка показа ошибки: {e}")
    def show_success(self) -> None:
        if self._closed:
            return
        try:
            self._status_label.configure(text="Отправлено на печать ✓", text_color="#27AE60")
            self._progress.set(1.0)
            self._closed = True
            self.after(1200, self._safe_destroy)
        except tk.TclError:
            pass
        except Exception as e:
            logger.error(f"[PrintConfirmDialog] Ошибка показа успеха: {e}")
    def _safe_destroy(self) -> None:
        try:
            if self.winfo_exists():
                self.grab_release()
                self.destroy()
        except tk.TclError:
            pass
        except Exception as e:
            logger.error(f"[PrintConfirmDialog] Ошибка закрытия: {e}")