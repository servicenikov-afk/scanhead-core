# --- gui/dialogs/settings_dialog.py ---
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
import logging
from typing import Any, Callable, Optional
import customtkinter as ctk
from services.interfaces import ISettingsService
logger=logging.getLogger(__name__)
class SettingsDialog(ctk.CTkToplevel):
	def __init__(self,master:Any,settings_service:ISettingsService,on_settings_changed:Optional[Callable[[str,Any],None]]=None):
		super().__init__(master)
		self._settings_service=settings_service
		self._on_settings_changed=on_settings_changed
		logger.debug("[SettingsDialog] Открытие диалога настроек")
		self.title("⚙ Настройки приложения")
		self.geometry("800x650+50+50")
		self.minsize(600,550)
		self.transient(master)
		self._create_content()
	def _create_content(self)->None:
		self.grid_rowconfigure(1,weight=1)
		self.grid_columnconfigure(0,weight=1)
		title_label=ctk.CTkLabel(self,text="Настройки приложения",font=ctk.CTkFont(size=16,weight="bold"))
		title_label.grid(row=0,column=0,padx=20,pady=(20,10),sticky="w")
		tabview=ctk.CTkTabview(self,corner_radius=8)
		tabview.grid(row=1,column=0,padx=20,pady=10,sticky="nsew")
		tab_view=tabview.add("Вид")
		tab_address=tabview.add("Адрес")
		tab_data=tabview.add("Данные")
		tab_hotkeys=tabview.add("Клавиши")
		self._create_view_tab(tab_view)
		self._create_address_tab(tab_address)
		self._create_data_tab(tab_data)
		self._create_hotkeys_tab(tab_hotkeys)
		buttons_frame=ctk.CTkFrame(self,fg_color="transparent")
		buttons_frame.grid(row=2,column=0,padx=20,pady=(10,20),sticky="e")
		btn_cancel=ctk.CTkButton(buttons_frame,text="Отмена",width=100,command=self.destroy)
		btn_cancel.pack(side="right",padx=5)
		btn_save=ctk.CTkButton(buttons_frame,text="Сохранить",width=100,command=self._on_click_save)
		btn_save.pack(side="right",padx=5)
	def _create_view_tab(self,parent:Any)->None:
		parent.grid_columnconfigure(1,weight=1)
		row=0
		lbl_theme=ctk.CTkLabel(parent,text="Тема оформления:",width=150,anchor="w")
		lbl_theme.grid(row=row,column=0,padx=10,pady=10,sticky="w")
		current_theme=self._settings_service.get_setting('theme','Dark')
		self._theme_combo=ctk.CTkComboBox(parent,values=["System","Light","Dark"],width=200)
		self._theme_combo.grid(row=row,column=1,padx=10,pady=10,sticky="w")
		self._theme_combo.set(current_theme)
		row+=1
		lbl_lang=ctk.CTkLabel(parent,text="Язык интерфейса:",width=150,anchor="w")
		lbl_lang.grid(row=row,column=0,padx=10,pady=10,sticky="w")
		current_lang=self._settings_service.get_setting('language','ru')
		self._lang_combo=ctk.CTkComboBox(parent,values=["ru","en"],width=200)
		self._lang_combo.grid(row=row,column=1,padx=10,pady=10,sticky="w")
		self._lang_combo.set(current_lang)
		row+=1
		ctk.CTkLabel(parent,text="Шрифт поиска",font=ctk.CTkFont(size=14,weight="bold")).grid(row=row,column=0,columnspan=2,padx=10,pady=(15,5),sticky="w")
		self._font_slider=ctk.CTkSlider(parent,from_=12,to=24,number_of_steps=12,command=lambda v:self._font_val_label.configure(text=f"{int(v)} pt"))
		self._font_slider.grid(row=row+1,column=0,columnspan=2,padx=10,pady=5,sticky="ew")
		self._font_val_label=ctk.CTkLabel(parent,text="18 pt")
		self._font_val_label.grid(row=row+2,column=1,padx=10,pady=5,sticky="e")
		row+=3
		ctk.CTkLabel(parent,text="Фокус",font=ctk.CTkFont(size=14,weight="bold")).grid(row=row,column=0,columnspan=2,padx=10,pady=(15,5),sticky="w")
		self._autofocus_var=ctk.BooleanVar(value=True)
		self._autofocus_checkbox=ctk.CTkCheckBox(parent,text="Авто фокус в поле «Поиск»",variable=self._autofocus_var,command=self._toggle_focus_delay)
		self._autofocus_checkbox.grid(row=row+1,column=0,columnspan=2,padx=10,pady=5,sticky="w")
		row+=2
		focus_delay_frame=ctk.CTkFrame(parent,fg_color="transparent")
		focus_delay_frame.grid(row=row,column=0,columnspan=2,padx=10,pady=5,sticky="w")
		ctk.CTkLabel(focus_delay_frame,text="Задержка автофокуса").pack(side="left")
		self._focus_delay_slider=ctk.CTkSlider(focus_delay_frame,from_=0.0,to=3.0,number_of_steps=30,width=150,command=lambda v:self._focus_delay_val_label.configure(text=f"{v:.1f} сек"))
		self._focus_delay_slider.pack(side="left",padx=10)
		self._focus_delay_val_label=ctk.CTkLabel(focus_delay_frame,text="1.0 сек")
		self._focus_delay_val_label.pack(side="left")
		row+=1
		ctk.CTkLabel(parent,text="Автоочистка поиска",font=ctk.CTkFont(size=14,weight="bold")).grid(row=row,column=0,columnspan=2,padx=10,pady=(15,5),sticky="w")
		self._autoclear_var=ctk.BooleanVar(value=True)
		self._autoclear_checkbox=ctk.CTkCheckBox(parent,text="Автоочистка поля «Поиск» после поиска",variable=self._autoclear_var,command=self._toggle_autoclear_delay)
		self._autoclear_checkbox.grid(row=row+1,column=0,columnspan=2,padx=10,pady=5,sticky="w")
		row+=2
		autoclear_delay_frame=ctk.CTkFrame(parent,fg_color="transparent")
		autoclear_delay_frame.grid(row=row,column=0,columnspan=2,padx=10,pady=5,sticky="w")
		ctk.CTkLabel(autoclear_delay_frame,text="Задержка автоочистки").pack(side="left")
		self._autoclear_delay_slider=ctk.CTkSlider(autoclear_delay_frame,from_=0.0,to=10.0,number_of_steps=20,width=150,command=lambda v:self._autoclear_delay_val_label.configure(text=f"{v:.1f} сек"))
		self._autoclear_delay_slider.pack(side="left",padx=10)
		self._autoclear_delay_val_label=ctk.CTkLabel(autoclear_delay_frame,text="3.0 сек")
		self._autoclear_delay_val_label.pack(side="left")
		self._load_search_settings()
	def _load_search_settings(self)->None:
		font_size=self._settings_service.get_setting("search_font_size",18)
		autofocus=self._settings_service.get_setting("search_autofocus",True)
		focus_delay=self._settings_service.get_setting("search_autofocus_delay",1.0)
		autoclear=self._settings_service.get_setting("search_autoclear_enabled",True)
		autoclear_delay=self._settings_service.get_setting("search_autoclear_delay",3.0)
		self._font_slider.set(font_size)
		self._autofocus_var.set(autofocus)
		self._focus_delay_slider.set(focus_delay)
		self._autoclear_var.set(autoclear)
		self._autoclear_delay_slider.set(autoclear_delay)
		self._font_val_label.configure(text=f"{int(font_size)} pt")
		self._focus_delay_val_label.configure(text=f"{focus_delay:.1f} сек")
		self._autoclear_delay_val_label.configure(text=f"{autoclear_delay:.1f} сек")
		self._toggle_focus_delay()
		self._toggle_autoclear_delay()
	def _toggle_focus_delay(self)->None:
		state="normal" if self._autofocus_var.get() else "disabled"
		self._focus_delay_slider.configure(state=state)
	def _toggle_autoclear_delay(self)->None:
		state="normal" if self._autoclear_var.get() else "disabled"
		self._autoclear_delay_slider.configure(state=state)
	def _create_address_tab(self,parent:Any)->None:
		scrollable_frame=ctk.CTkScrollableFrame(parent,fg_color="transparent")
		scrollable_frame.grid(row=0,column=0,sticky="nsew",padx=0,pady=0)
		parent.grid_columnconfigure(0,weight=1)
		parent.grid_rowconfigure(0,weight=1)
		content_frame=scrollable_frame
		content_frame.grid_columnconfigure(1,weight=1)
		row=0
		self._address_enabled_var=ctk.BooleanVar(value=False)
		self._address_enabled_checkbox=ctk.CTkCheckBox(content_frame,text="Использовать форматированный адрес",variable=self._address_enabled_var,command=self._toggle_address_format_controls)
		self._address_enabled_checkbox.grid(row=row,column=0,columnspan=2,padx=10,pady=10,sticky="w")
		self._format_controls_frame=ctk.CTkFrame(content_frame,fg_color="transparent")
		self._format_controls_frame.grid(row=row+1,column=0,columnspan=2,padx=10,pady=10,sticky="ew")
		self._format_controls_frame.grid_columnconfigure(1,weight=1)
		r=0
		lbl_separator=ctk.CTkLabel(self._format_controls_frame,text="Разделитель:",width=150,anchor="w")
		lbl_separator.grid(row=r,column=0,padx=10,pady=5,sticky="w")
		self._separator_var=ctk.StringVar(value="-")
		self._separator_combo=ctk.CTkComboBox(self._format_controls_frame,values=["-","/","_",".","custom"],width=100,variable=self._separator_var,command=self._on_separator_changed)
		self._separator_combo.grid(row=r,column=1,padx=10,pady=5,sticky="w")
		self._custom_separator_entry=ctk.CTkEntry(self._format_controls_frame,width=50,placeholder_text="Свой")
		self._custom_separator_entry.grid(row=r,column=2,padx=10,pady=5,sticky="w")
		self._custom_separator_entry.grid_remove()
		r+=1
		lbl_levels=ctk.CTkLabel(self._format_controls_frame,text="Уровни адреса:",font=ctk.CTkFont(size=14,weight="bold"))
		lbl_levels.grid(row=r,column=0,columnspan=2,padx=10,pady=(15,5),sticky="w")
		self._levels_container=ctk.CTkScrollableFrame(self._format_controls_frame,height=250,fg_color=("gray85","gray25"))
		self._levels_container.grid(row=r+1,column=0,columnspan=3,padx=10,pady=5,sticky="nsew")
		self._format_controls_frame.grid_rowconfigure(r+1,weight=1)
		self._add_level_button=ctk.CTkButton(self._format_controls_frame,text="+ Добавить уровень",width=150,command=self._add_level)
		self._add_level_button.grid(row=r+2,column=0,columnspan=2,padx=10,pady=10,sticky="w")
		self._level_widgets=[]
		r+=3
		lbl_display=ctk.CTkLabel(self._format_controls_frame,text="Режим отображения:",font=ctk.CTkFont(size=14,weight="bold"))
		lbl_display.grid(row=r,column=0,columnspan=2,padx=10,pady=(15,5),sticky="w")
		self._display_mode_var=ctk.StringVar(value="compact")
		radio_compact=ctk.CTkRadioButton(self._format_controls_frame,text="Компактный (только значения)",variable=self._display_mode_var,value="compact")
		radio_compact.grid(row=r+1,column=0,columnspan=2,padx=20,pady=5,sticky="w")
		radio_labels=ctk.CTkRadioButton(self._format_controls_frame,text="С подписями (Блок A, Стеллаж 01)",variable=self._display_mode_var,value="with_labels")
		radio_labels.grid(row=r+2,column=0,columnspan=2,padx=20,pady=5,sticky="w")
		self._load_address_settings()
	def _load_address_settings(self)->None:
		config=self._settings_service.get_setting("address_format",{})
		if config:
			self._address_enabled_var.set(config.get("enabled",False))
			self._separator_var.set(config.get("separator","-"))
			self._custom_separator_entry.insert(0,config.get("custom_separator",""))
			self._display_mode_var.set(config.get("display_mode","compact"))
			levels=config.get("levels",["Блок","Стеллаж","Секция"])
			for level_name in levels:self._add_level(level_name)
		self._toggle_address_format_controls()
		self._on_separator_changed(self._separator_var.get())
	def _toggle_address_format_controls(self)->None:
		if self._address_enabled_var.get():self._format_controls_frame.grid()
		else:self._format_controls_frame.grid_remove()
	def _on_separator_changed(self,value:str)->None:
		if value=="custom":self._custom_separator_entry.grid()
		else:self._custom_separator_entry.grid_remove()
	def _add_level(self,name:str="")->None:
		if len(self._level_widgets)>=10:return
		row=len(self._level_widgets)
		frame=ctk.CTkFrame(self._levels_container,fg_color="transparent")
		frame.pack(fill="x",pady=2)
		entry=ctk.CTkEntry(frame,width=200,placeholder_text=f"Уровень {row+1}")
		entry.pack(side="left",padx=(0,10))
		if name:entry.insert(0,name)
		btn_delete=ctk.CTkButton(frame,text="🗑️",width=40,command=lambda:self._remove_level(frame))
		btn_delete.pack(side="left")
		self._level_widgets.append((frame,entry))
	def _remove_level(self,frame:ctk.CTkFrame)->None:
		for i,(f,_) in enumerate(self._level_widgets):
			if f==frame:
				frame.destroy()
				self._level_widgets.pop(i)
				break
	def _get_address_config_from_ui(self)->dict:
		levels=[entry.get().strip() or f"Уровень {i+1}" for i,(_,entry) in enumerate(self._level_widgets)]
		separator=self._separator_var.get()
		custom_sep=self._custom_separator_entry.get().strip()
		return{"enabled":self._address_enabled_var.get(),"separator":separator,"custom_separator":custom_sep if separator=="custom" else "","levels":levels,"display_mode":self._display_mode_var.get()}
	def _create_data_tab(self,parent:Any)->None:
		lbl=ctk.CTkLabel(parent,text="Настройки данных и БД\n(в разработке)",font=ctk.CTkFont(size=14))
		lbl.place(relx=0.5,rely=0.5,anchor="center")
	def _create_hotkeys_tab(self,parent:Any)->None:
		parent.grid_columnconfigure(0,weight=1)
		parent.grid_rowconfigure(0,weight=1)
		scroll_frame=ctk.CTkScrollableFrame(parent,fg_color="transparent")
		scroll_frame.grid(row=0,column=0,sticky="nsew",padx=10,pady=10)
		scroll_frame.grid_columnconfigure(1,weight=1)
		ctk.CTkLabel(scroll_frame,text="⌨️ Горячие клавиши",font=ctk.CTkFont(size=16,weight="bold")).grid(row=0,column=0,columnspan=2,padx=10,pady=(0,15),sticky="w")
		actions={'open_settings':'Настройки программы','show_product_info':'Детальная информация о товаре','add_to_queue':'Добавить в очередь печати','next_preset':'Следующий пресет','open_preset_editor':'Настройки пресетов','print_queue':'Печать очереди'}
		current_hotkeys=self._settings_service.get_setting('hotkeys',{})
		self._hotkey_entries={}
		row=1
		for action,description in actions.items():
			lbl=ctk.CTkLabel(scroll_frame,text=description,font=ctk.CTkFont(size=13),anchor="w")
			lbl.grid(row=row,column=0,padx=10,pady=5,sticky="w")
			entry=ctk.CTkEntry(scroll_frame,width=150,font=ctk.CTkFont(size=13),placeholder_text="Нажмите клавишу...")
			current_value=current_hotkeys.get(action,'')
			if current_value:
				entry.insert(0,current_value)
			entry.grid(row=row,column=1,padx=10,pady=5,sticky="w")
			entry.bind("<Key>",lambda e,ent=entry:self._capture_hotkey(e,ent))
			self._hotkey_entries[action]=entry
			row+=1
		btn_reset=ctk.CTkButton(scroll_frame,text="🔄 Сбросить к умолчанию",command=self._reset_hotkeys_to_default,fg_color="#6c757d",hover_color="#5a6268",width=200)
		btn_reset.grid(row=row,column=0,columnspan=2,padx=10,pady=(20,10),sticky="w")
	def _capture_hotkey(self,event,entry)->str:
		logger.debug(f"[SettingsDialog] Захвачена клавиша: keysym={event.keysym}, state={event.state}, char={event.char}")
		if event.keysym in ('Control_L','Control_R','Shift_L','Shift_R','Alt_L','Alt_R','Super_L','Super_R'):
			return "break"
		if event.keysym in ('Alt_L','Alt_R') and (event.state & 0x8):
			return "break"
		modifiers=[]
		if event.state & 0x4:modifiers.append("Control")
		if event.state & 0x1:modifiers.append("Shift")
		if event.state & 0x8:modifiers.append("Alt")
		keysym=event.keysym
		keysym_map={'Return':'Return','Escape':'Escape','space':'space','plus':'equal','minus':'minus','equal':'equal'}
		keysym=keysym_map.get(keysym,keysym)
		if modifiers:hotkey='-'.join(modifiers+[keysym])
		else:hotkey=keysym
		entry.delete(0,"end")
		entry.insert(0,hotkey)
		logger.info(f"[SettingsDialog] Установлена горячая клавиша: {hotkey}")
		return "break"
	def _reset_hotkeys_to_default(self)->None:
		from services.hotkey_service import DEFAULT_HOTKEYS
		for action,entry in self._hotkey_entries.items():
			default_value=DEFAULT_HOTKEYS.get(action,'')
			entry.delete(0,"end")
			entry.insert(0,default_value)
	def _on_click_save(self)->None:
		logger.info("[SettingsDialog] Сохранение настроек")
		theme=self._theme_combo.get()
		self._settings_service.set_setting('theme',theme)
		import customtkinter as ctk
		ctk.set_appearance_mode(theme)
		lang=self._lang_combo.get()
		self._settings_service.set_setting('language',lang)
		font_size=int(self._font_slider.get())
		autofocus=self._autofocus_var.get()
		focus_delay=float(self._focus_delay_slider.get())
		autoclear=self._autoclear_var.get()
		autoclear_delay=float(self._autoclear_delay_slider.get())
		self._settings_service.set_setting("search_font_size",font_size)
		self._settings_service.set_setting("search_autofocus",autofocus)
		self._settings_service.set_setting("search_autofocus_delay",focus_delay)
		self._settings_service.set_setting("search_autoclear_enabled",autoclear)
		self._settings_service.set_setting("search_autoclear_delay",autoclear_delay)
		if hasattr(self,'_hotkey_entries'):
			hotkeys={}
			for action,entry in self._hotkey_entries.items():
				hotkey=entry.get().strip()
				if hotkey:hotkeys[action]=hotkey
			self._settings_service.set_setting('hotkeys',hotkeys)
			logger.info(f"[SettingsDialog] Сохранены горячие клавиши: {hotkeys}")
			if self._on_settings_changed:
				self._on_settings_changed('hotkeys',hotkeys)
		address_config=self._get_address_config_from_ui()
		self._settings_service.set_setting("address_format",address_config)
		logger.info(f"[SettingsDialog] Настройки сохранены: theme={theme}, language={lang}, search_font_size={font_size}, search_autofocus={autofocus}, search_autofocus_delay={focus_delay}, search_autoclear_enabled={autoclear}, search_autoclear_delay={autoclear_delay}, address_format={address_config}")
		if self._on_settings_changed:
			self._on_settings_changed("search_font_size",font_size)
			self._on_settings_changed("search_autofocus",autofocus)
			self._on_settings_changed("search_autofocus_delay",focus_delay)
			self._on_settings_changed("search_autoclear_enabled",autoclear)
			self._on_settings_changed("search_autoclear_delay",autoclear_delay)
			self._on_settings_changed("address_format",address_config)
		if hasattr(self._settings_service,'save'):
			self._settings_service.save()
		self.destroy()