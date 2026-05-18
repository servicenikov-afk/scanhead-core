"""
Диалог настроек приложения.
Позволяет настроить тему, язык, параметры таблицы и другие опции.
"""

import logging
from typing import Any, Callable, Optional

import customtkinter as ctk

from services.interfaces import ISettingsService

logger = logging.getLogger(__name__)


class SettingsDialog(ctk.CTkToplevel):
    """
    Диалог настроек приложения.
    
    Настройки: тема, язык, конфигурация колонок таблицы.
    """
    
    def __init__(
        self,
        master: Any,
        settings_service: ISettingsService,
        on_settings_changed: Optional[Callable[[str, Any], None]] = None
    ):
        super().__init__(master)
        self._settings_service = settings_service
        self._on_settings_changed = on_settings_changed
        
        logger.debug("[SettingsDialog] Открытие диалога настроек")
        
        # Настройки окна (увеличенный размер 800x600)
        self.title("⚙ Настройки приложения")
        self.geometry("800x600")
        self.minsize(600, 450)
        
        self.transient(master)
        
        # Создаём контент с табами
        self._create_content()
    
    def _create_content(self) -> None:
        """Создание контента диалога с табами."""
        # Отступы
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Заголовок
        title_label = ctk.CTkLabel(
            self,
            text="Настройки приложения",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # CTkTabview с вкладками: "Вид", "Адрес", "Данные"
        tabview = ctk.CTkTabview(self, corner_radius=8)
        tabview.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        tab_view = tabview.add("Вид")
        tab_address = tabview.add("Адрес")
        tab_data = tabview.add("Данные")
        
        # Вкладка "Вид"
        self._create_view_tab(tab_view)
        
        # Вкладка "Адрес"
        self._create_address_tab(tab_address)
        
        # Вкладка "Данные"
        self._create_data_tab(tab_data)
        
        # Кнопки
        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="e")
        
        btn_cancel = ctk.CTkButton(
            buttons_frame,
            text="Отмена",
            width=100,
            command=self.destroy
        )
        btn_cancel.pack(side="right", padx=5)
        
        btn_save = ctk.CTkButton(
            buttons_frame,
            text="Сохранить",
            width=100,
            command=self._on_click_save
        )
        btn_save.pack(side="right", padx=5)
    
    def _create_view_tab(self, parent: Any) -> None:
        """Создание вкладки 'Вид'."""
        parent.grid_columnconfigure(1, weight=1)
        
        # Тема оформления
        row = 0
        lbl_theme = ctk.CTkLabel(
            parent,
            text="Тема оформления:",
            width=150,
            anchor="w"
        )
        lbl_theme.grid(row=row, column=0, padx=10, pady=10, sticky="w")
        
        current_theme = self._settings_service.get_setting('theme', 'Dark')
        self._theme_combo = ctk.CTkComboBox(
            parent,
            values=["System", "Light", "Dark"],
            width=200
        )
        self._theme_combo.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        self._theme_combo.set(current_theme)
        
        # Язык интерфейса
        row += 1
        lbl_lang = ctk.CTkLabel(
            parent,
            text="Язык интерфейса:",
            width=150,
            anchor="w"
        )
        lbl_lang.grid(row=row, column=0, padx=10, pady=10, sticky="w")
        
        current_lang = self._settings_service.get_setting('language', 'ru')
        self._lang_combo = ctk.CTkComboBox(
            parent,
            values=["ru", "en"],
            width=200
        )
        self._lang_combo.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        self._lang_combo.set(current_lang)
        
        # === СЕКЦИЯ: Шрифт поиска ===
        row += 1
        ctk.CTkLabel(
            parent,
            text="Шрифт поиска",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=row, column=0, columnspan=2, padx=10, pady=(15, 5), sticky="w")
        
        self._font_slider = ctk.CTkSlider(
            parent,
            from_=12, to=24, number_of_steps=12,
            command=lambda v: self._font_val_label.configure(text=f"{int(v)} pt")
        )
        self._font_slider.grid(row=row + 1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        self._font_val_label = ctk.CTkLabel(parent, text="18 pt")
        self._font_val_label.grid(row=row + 2, column=1, padx=10, pady=5, sticky="e")
        
        # === СЕКЦИЯ: Автофокус ===
        row += 3
        ctk.CTkLabel(
            parent,
            text="Фокус",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=row, column=0, columnspan=2, padx=10, pady=(15, 5), sticky="w")
        
        self._autofocus_var = ctk.BooleanVar(value=True)
        self._autofocus_checkbox = ctk.CTkCheckBox(
            parent,
            text="Авто фокус в поле «Поиск»",
            variable=self._autofocus_var,
            command=self._toggle_focus_delay
        )
        self._autofocus_checkbox.grid(row=row + 1, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        # === СЕКЦИЯ: Задержка автофокуса ===
        row += 2
        focus_delay_frame = ctk.CTkFrame(parent, fg_color="transparent")
        focus_delay_frame.grid(row=row, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        ctk.CTkLabel(focus_delay_frame, text="Задержка автофокуса").pack(side="left")
        
        self._focus_delay_slider = ctk.CTkSlider(
            focus_delay_frame,
            from_=0.0, to=3.0, number_of_steps=30,  # Шаг 0.1 сек
            width=150,
            command=lambda v: self._focus_delay_val_label.configure(text=f"{v:.1f} сек")
        )
        self._focus_delay_slider.pack(side="left", padx=10)
        
        self._focus_delay_val_label = ctk.CTkLabel(focus_delay_frame, text="1.0 сек")
        self._focus_delay_val_label.pack(side="left")
        
        # Загрузка текущих значений настроек
        self._load_search_settings()
    
    def _load_search_settings(self) -> None:
        """Загрузка настроек поиска из сервиса настроек."""
        font_size = self._settings_service.get_setting("search_font_size", 18)
        autofocus = self._settings_service.get_setting("search_autofocus", True)
        focus_delay = self._settings_service.get_setting("search_autofocus_delay", 1.0)
        
        self._font_slider.set(font_size)
        self._autofocus_var.set(autofocus)
        self._focus_delay_slider.set(focus_delay)
        
        # Обновить текстовые метки
        self._font_val_label.configure(text=f"{int(font_size)} pt")
        self._focus_delay_val_label.configure(text=f"{focus_delay:.1f} сек")
        
        # Обновить состояние слайдера задержки
        self._toggle_focus_delay()
    
    def _toggle_focus_delay(self) -> None:
        """Блокировка слайдера задержки, если автофокус выключен."""
        state = "normal" if self._autofocus_var.get() else "disabled"
        self._focus_delay_slider.configure(state=state)
    
    def _create_address_tab(self, parent: Any) -> None:
        """Создание вкладки 'Адрес' (заглушка)."""
        lbl = ctk.CTkLabel(
            parent,
            text="Настройки адресов хранения\n(в разработке)",
            font=ctk.CTkFont(size=14)
        )
        lbl.place(relx=0.5, rely=0.5, anchor="center")
    
    def _create_data_tab(self, parent: Any) -> None:
        """Создание вкладки 'Данные' (заглушка)."""
        lbl = ctk.CTkLabel(
            parent,
            text="Настройки данных и БД\n(в разработке)",
            font=ctk.CTkFont(size=14)
        )
        lbl.place(relx=0.5, rely=0.5, anchor="center")
    
    def _on_click_save(self) -> None:
        """Обработчик клика по кнопке 'Сохранить'."""
        logger.info("[SettingsDialog] Сохранение настроек")
        
        # Сохраняем тему
        theme = self._theme_combo.get()
        self._settings_service.set_setting('theme', theme)
        
        # Применяем тему немедленно
        import customtkinter as ctk
        ctk.set_appearance_mode(theme)
        
        # Сохраняем язык
        lang = self._lang_combo.get()
        self._settings_service.set_setting('language', lang)
        
        # Сохраняем настройки поиска
        font_size = int(self._font_slider.get())
        autofocus = self._autofocus_var.get()
        focus_delay = float(self._focus_delay_slider.get())
        
        self._settings_service.set_setting("search_font_size", font_size)
        self._settings_service.set_setting("search_autofocus", autofocus)
        self._settings_service.set_setting("search_autofocus_delay", focus_delay)
        
        logger.info(f"[SettingsDialog] Настройки сохранены: theme={theme}, language={lang}, search_font_size={font_size}, search_autofocus={autofocus}, search_autofocus_delay={focus_delay}")
        
        # Уведомляем об изменениях через колбэк
        if self._on_settings_changed:
            self._on_settings_changed("search_font_size", font_size)
            self._on_settings_changed("search_autofocus", autofocus)
            self._on_settings_changed("search_autofocus_delay", focus_delay)
        
        self.destroy()
