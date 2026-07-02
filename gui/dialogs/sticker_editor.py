# --- sticker_editor.py ---
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
import logging,customtkinter as ctk,tkinter as tk
from typing import Any,Optional
from services.interfaces import ISettingsService
from libs.domain_models import Product
from libs.printing.sticker_generator import StickerGenerator
from PIL import Image,ImageTk
logger=logging.getLogger(__name__)
class MiniSpinbox(ctk.CTkFrame):
	def __init__(self,master,from_=0,to=100,width=60,command=None,**kwargs):
		super().__init__(master,**kwargs)
		self._min,self._max,self._command=from_,to,command
		self.grid_columnconfigure(1,weight=1)
		ctk.CTkButton(self,text="−",width=24,command=self._dec).grid(row=0,column=0,padx=1)
		self._entry=ctk.CTkEntry(self,width=width,justify="center")
		self._entry.grid(row=0,column=1,padx=1)
		self._entry.bind("<KeyRelease>",lambda e:self._fire())
		ctk.CTkButton(self,text="+",width=24,command=self._inc).grid(row=0,column=2,padx=1)
		self.set(from_)
	def _inc(self):
		try:v=int(self._entry.get())+1
		except ValueError:v=self._min
		self.set(min(v,self._max));self._fire()
	def _dec(self):
		try:v=int(self._entry.get())-1
		except ValueError:v=self._max
		self.set(max(v,self._min));self._fire()
	def _fire(self):
		if self._command:self._command()
	def get(self):
		try:return int(self._entry.get())
		except ValueError:return 0
	def set(self,v):
		self._entry.delete(0,"end");self._entry.insert(0,str(v))
FIELDS={
	"📏 Размеры":[
		{"label":"Ширина (мм)","key":"width_mm","type":"spin","min":10,"max":200,"default":60},
		{"label":"Высота (мм)","key":"height_mm","type":"spin","min":10,"max":200,"default":40},
		{"label":"Ориентация","key":"orientation","type":"combo","values":["portrait","landscape"],"default":"portrait"},
		{"label":"Рамка","key":"border","type":"check","default":False}
	],
	"🔤 Артикул":[
		{"label":"Включить","key":"article_enabled","type":"check","default":True},
		{"label":"Размер шрифта","key":"article_size","type":"spin","min":2,"max":72,"default":8},
		{"label":"Выравнивание","key":"article_align","type":"combo","values":["left","center","right"],"default":"left"},
		{"label":"Жирный","key":"article_bold","type":"check","default":True},
		{"label":"Смещение ","key":"article_offset_x","type":"pair_spin_wrap","key2":"article_offset_y","min":-500,"max":500,"default":0,"default2":0}
	],
	"📝 Название":[
		{"label":"Включить","key":"name_enabled","type":"check","default":True},
		{"label":"Размер шрифта","key":"name_size","type":"spin","min":2,"max":72,"default":6},
		{"label":"Выравнивание","key":"name_align","type":"combo","values":["left","center","right"],"default":"left"},
		{"label":"Макс. строк","key":"name_max_lines","type":"spin","min":0,"max":20,"default":5},
		{"label":"Жирный","key":"name_bold","type":"check","default":False},
		{"label":"Курсив","key":"name_italic","type":"check","default":False},
		{"label":"Смещение ","key":"name_offset_x","type":"pair_spin_wrap","key2":"name_offset_y","min":-500,"max":500,"default":0,"default2":0}
	],
	"🏢 Адрес":[
		{"label":"Включить","key":"address_enabled","type":"check","default":False},
		{"label":"Размер шрифта","key":"address_size","type":"spin","min":2,"max":72,"default":6},
		{"label":"Выравнивание","key":"address_align","type":"combo","values":["left","center","right"],"default":"right"},
		{"label":"Жирный","key":"address_bold","type":"check","default":False},
		{"label":"Курсив","key":"address_italic","type":"check","default":False},
		{"label":"Смещение ","key":"address_offset_x","type":"pair_spin_wrap","key2":"address_offset_y","min":-500,"max":500,"default":0,"default2":0}
	],
	"Коды":[
		{"label":"Включить","key":"barcode_enabled","type":"check","default":True},
		{"label":"Тип","key":"barcode_type","type":"combo","values":["auto","code128","qr"],"default":"auto"},
		{"label":"Позиция","key":"barcode_position","type":"combo","values":["top_right","top_left","bottom_right","bottom_left","right","left","top","bottom"],"default":"top_right"},
		{"label":"Размер QR (мм)","key":"barcode_qr_size_mm","type":"spin","min":4,"max":100,"default":16},
		{"label":"Code128 Ширина (мм)","key":"code128_width_mm","type":"spin","min":2,"max":128,"default":36},
		{"label":"Code128 Высота (мм)","key":"code128_height_mm","type":"spin","min":2,"max":64,"default":6},
		{"label":"Текст под кодом","key":"barcode_show_text","type":"check","default":False},
		{"label":"Размер текста","key":"barcode_text_size","type":"spin","min":2,"max":72,"default":4},
		{"label":"Смещение кода ","key":"barcode_offset_x","type":"pair_spin_wrap","key2":"barcode_offset_y","min":-500,"max":500,"default":0,"default2":0},
		{"label":"Смещение текста ","key":"barcode_text_offset_x","type":"pair_spin_wrap","key2":"barcode_text_offset_y","min":-500,"max":500,"default":0,"default2":0},
		{"label":"Масштаб текста X (×0.1)","key":"barcode_text_scale_x","type":"spin","min":1,"max":30,"default":10},
		{"label":"Масштаб текста Y (×0.1)","key":"barcode_text_scale_y","type":"spin","min":1,"max":30,"default":10}
	]
}
class StickerEditor(ctk.CTkToplevel):
	def __init__(self,master:Any,settings_service:ISettingsService,product:Optional[Product]=None,search_service=None):
		super().__init__(master)
		self._settings_service=settings_service
		self._search_service=search_service
		self._product=product
		self._sample_product_cache=None
		self._sample_address_cache=None
		self.title("⚙ Редактор пресетов")
		self.geometry("1100x585")
		self.resizable(True,True)
		self.transient(master)
		self._presets=self._settings_service.get_setting('sticker_presets',{})
		self._current_name=self._settings_service.get_setting('current_preset_name','default')
		self._current_preset=self._presets.get(self._current_name,{})
		self._widgets={}
		self._photo_image=None
		self._last_preview_size=(0,0)
		self._preview_after_id=None
		self.protocol("WM_DELETE_WINDOW",self._on_close)
		self._create_ui()
		if self._current_name not in self._presets:self._presets[self._current_name]={}
		self._show_group(list(FIELDS.keys())[0])
		self._update_preview()
	def _on_close(self):
		if self._preview_after_id:
			try:self.after_cancel(self._preview_after_id)
			except:pass
			self._preview_after_id=None
		self.destroy()
	def destroy(self):
		if self._preview_after_id:
			try:self.after_cancel(self._preview_after_id)
			except:pass
			self._preview_after_id=None
		super().destroy()
	def _create_ui(self):
		self.grid_columnconfigure(0,weight=1,minsize=180)
		self.grid_columnconfigure(1,weight=4)
		self.grid_columnconfigure(2,weight=2)
		self.grid_rowconfigure(0,weight=1)
		left=ctk.CTkFrame(self)
		left.grid(row=0,column=0,rowspan=2,sticky="nsew",padx=5,pady=5)
		ctk.CTkLabel(left,text="Пресеты",font=ctk.CTkFont(weight="bold")).pack(pady=(5,2))
		self._preset_list=ctk.CTkComboBox(left,values=list(self._presets.keys()),command=self._on_select)
		self._preset_list.pack(fill="x",padx=5,pady=2)
		self._preset_list.set(self._current_name)
		btn_frame=ctk.CTkFrame(left,fg_color="transparent")
		btn_frame.pack(fill="x",padx=5,pady=2)
		ctk.CTkButton(btn_frame,text="+",width=30,command=self._add).pack(side="left",padx=2)
		ctk.CTkButton(btn_frame,text="−",width=30,fg_color="#808080",command=self._del).pack(side="left",padx=2)
		ctk.CTkFrame(left,height=2,fg_color=("gray50","gray50")).pack(fill="x",padx=10,pady=10)
		ctk.CTkLabel(left,text="Группы",font=ctk.CTkFont(weight="bold")).pack(pady=(0,2))
		self._nav_btns={}
		for group in FIELDS.keys():
			btn=ctk.CTkButton(left,text=group,fg_color=("gray60","gray40"),hover_color=("gray50","gray30"),text_color=("black","white"),anchor="w",command=lambda g=group:self._show_group(g))
			btn.pack(fill="x",padx=5,pady=1)
			self._nav_btns[group]=btn
		self._right_frame=ctk.CTkFrame(self)
		self._right_frame.grid(row=0,column=1,rowspan=2,sticky="nsew",padx=5,pady=5)
		self._right_frame.grid_propagate(False)
		self._right_frame.configure(width=320)
		preview_container=ctk.CTkFrame(self)
		preview_container.grid(row=0,column=2,rowspan=2,sticky="nsew",padx=5,pady=5)
		preview_container.grid_rowconfigure(0,weight=1)
		preview_container.grid_columnconfigure(0,weight=1)
		self._preview_frame=ctk.CTkFrame(preview_container,fg_color=("gray70","gray35"))
		self._preview_frame.grid(row=0,column=0,sticky="nsew",padx=3,pady=3)
		self._preview_frame.grid_rowconfigure(0,weight=1)
		self._preview_frame.grid_columnconfigure(0,weight=1)
		self._preview_frame.grid_propagate(False)
		self._preview_frame.configure(width=420,height=320)
		self._preview_frame.bind("<Configure>",self._on_preview_frame_resize)
		self._preview_canvas=tk.Canvas(self._preview_frame,bg="white",highlightthickness=0)
		self._preview_canvas.grid(row=0,column=0,sticky="nsew",padx=5,pady=5)
		bottom=ctk.CTkFrame(self,fg_color="transparent")
		bottom.grid(row=2,column=0,columnspan=3,sticky="e",padx=10,pady=10)
		ctk.CTkButton(bottom,text="Сброс",fg_color="#808080",command=self._reset).pack(side="right",padx=5)
		ctk.CTkButton(bottom,text="Отмена",fg_color="#808080",command=self._on_close).pack(side="right",padx=5)
		ctk.CTkButton(bottom,text="Сохранить",command=self._save).pack(side="right",padx=5)
	def _on_preview_frame_resize(self,event=None):
		fw=self._preview_frame.winfo_width()
		fh=self._preview_frame.winfo_height()
		if abs(fw-self._last_preview_size[0])>10 or abs(fh-self._last_preview_size[1])>10:
			self._last_preview_size=(fw,fh)
			self._schedule_preview_update()
	def _show_group(self,group:str):
		for btn in self._nav_btns.values():btn.configure(fg_color=("gray60","gray40"))
		self._nav_btns[group].configure(fg_color=("gray40","gray60"))
		self._right_frame.update_idletasks()
		for w in self._right_frame.winfo_children():
			w.grid_remove()
			try:w.destroy()
			except tk.TclError:pass
		self._widgets.clear()
		for r,item in enumerate(FIELDS[group]):
			ctk.CTkLabel(self._right_frame,text=item["label"]).grid(row=r,column=0,padx=5,pady=3,sticky="w")
			self._render_widget(self._right_frame,r,item)
	def _schedule_preview_update(self):
		try:
			if self._preview_after_id:self.after_cancel(self._preview_after_id)
		except Exception:pass
		self._preview_after_id=self.after(150,self._update_preview)
	def _to_nested(self,flat:dict)->dict:
		return {
			'sticker':{'width_mm':flat.get('width_mm',60),'height_mm':flat.get('height_mm',40),'orientation':flat.get('orientation','portrait'),'border':flat.get('border',False),'background_color':'#FFFFFF','dpi':300},
			'fonts':{'name_size':flat.get('name_size',6),'article_size':flat.get('article_size',8),'address_size':flat.get('address_size',6)},
			'layout':{'show_barcode':flat.get('barcode_enabled',True),'show_qr':flat.get('barcode_type')=='qr','article_position':'top' if flat.get('article_enabled',True) else 'hidden','show_address':flat.get('address_enabled',False),'address_position':'bottom'},
			'article':{'enabled':flat.get('article_enabled',True),'size':flat.get('article_size',8),'align':flat.get('article_align','left'),'bold':flat.get('article_bold',True),'offset_x':flat.get('article_offset_x',0),'offset_y':flat.get('article_offset_y',0)},
			'name':{'enabled':flat.get('name_enabled',True),'size':flat.get('name_size',6),'align':flat.get('name_align','left'),'max_lines':flat.get('name_max_lines',5),'bold':flat.get('name_bold',False),'italic':flat.get('name_italic',False),'offset_x':flat.get('name_offset_x',0),'offset_y':flat.get('name_offset_y',0)},
			'address':{'enabled':flat.get('address_enabled',False),'size':flat.get('address_size',6),'align':flat.get('address_align','right'),'bold':flat.get('address_bold',False),'italic':flat.get('address_italic',False),'offset_x':flat.get('address_offset_x',0),'offset_y':flat.get('address_offset_y',0)},
			'barcode':{'enabled':flat.get('barcode_enabled',True),'type':flat.get('barcode_type','auto'),'position':flat.get('barcode_position','top_right'),'qr_size_mm':flat.get('barcode_qr_size_mm',16),'code128_width_mm':flat.get('code128_width_mm',36),'code128_height_mm':flat.get('code128_height_mm',6),'show_text':flat.get('barcode_show_text',False),'text_size':flat.get('barcode_text_size',4),'offset_x':flat.get('barcode_offset_x',0),'offset_y':flat.get('barcode_offset_y',0),'text_offset_x':flat.get('barcode_text_offset_x',0),'text_offset_y':flat.get('barcode_text_offset_y',0),'text_scale_x':flat.get('barcode_text_scale_x',10)/10.0,'text_scale_y':flat.get('barcode_text_scale_y',10)/10.0}
		}
	def _update_preview(self):
		self._preview_after_id=None
		try:
			if not self._preview_canvas.winfo_exists():return
			self._do_update_preview()
		except Exception as e:logger.warning(f"Preview update failed: {e}")
	def _do_update_preview(self):
		try:
			if not self._preview_canvas.winfo_exists():return
			self.update_idletasks()
			cw=self._preview_canvas.winfo_width()
			ch=self._preview_canvas.winfo_height()
			if cw<=1 or ch<=1:cw,ch=400,300
			max_w,max_h=cw-10,ch-10
			preset=self._to_nested(self._collect_current_preset())
			product=self._product
			address_text=""
			if product:
				if hasattr(product,'storage_locations') and product.storage_locations:
					address_text=product.storage_locations[0] if isinstance(product.storage_locations,list) else str(product.storage_locations)
				elif hasattr(product,'address') and product.address:address_text=product.address
			else:
				if self._sample_product_cache is None:
					if self._search_service:
						try:
							results=self._search_service.search("")
							product_with_address=None
							first_valid_ascii=None
							for i,p in enumerate(results):
								if i>=50:break
								article=p.article or ""
								if any(ord(c)>127 for c in article):continue
								if first_valid_ascii is None:first_valid_ascii=p
								if hasattr(p,'storage_locations') and p.storage_locations:
									product_with_address=p;break
							if product_with_address:
								self._sample_product_cache=product_with_address
								self._sample_address_cache=product_with_address.storage_locations[0] if isinstance(product_with_address.storage_locations,list) else str(product_with_address.storage_locations)
							elif first_valid_ascii:
								self._sample_product_cache=first_valid_ascii
								self._sample_address_cache="00-00-00-00-00"
							else:
								self._sample_product_cache=None
								self._sample_address_cache=""
						except Exception as e:logger.warning(f"Failed to get sample product: {e}")
				product=self._sample_product_cache
				address_text=self._sample_address_cache or ""
			article_text=product.article if product else "TEST-001"
			name_text=product.name if product else "Тестовый товар"
			pil_img=StickerGenerator(preset).generate(article=article_text,name=name_text,address=address_text)
			iw,ih=pil_img.size
			ratio=min(max_w/iw,max_h/ih,1.0)
			pil_img=pil_img.resize((max(1,int(iw*ratio)),max(1,int(ih*ratio))),Image.Resampling.LANCZOS)
			self._photo_image=ImageTk.PhotoImage(pil_img)
			self._preview_canvas.delete("all")
			self._preview_canvas.create_image(cw//2,ch//2,image=self._photo_image,anchor="center")
		except Exception as e:logger.warning(f"Preview update failed: {e}")
	def _collect_current_preset(self):
		preset=dict(self._current_preset)
		for group in FIELDS.values():
			for item in group:
				key,dtype=item["key"],item["type"]
				w=self._widgets.get(key)
				if w:
					if isinstance(w,MiniSpinbox):preset[key]=w.get()
					elif isinstance(w,ctk.CTkComboBox):preset[key]=w.get()
					elif isinstance(w,ctk.CTkCheckBox):preset[key]=bool(w.get())
					elif isinstance(w,ctk.CTkEntry):preset[key]=w.get()
				k2=item.get("key2")
				if k2:
					w2=self._widgets.get(k2)
					if w2:
						if isinstance(w2,MiniSpinbox):preset[k2]=w2.get()
						elif isinstance(w2,ctk.CTkComboBox):preset[k2]=w2.get()
						elif isinstance(w2,ctk.CTkCheckBox):preset[k2]=bool(w2.get())
						elif isinstance(w2,ctk.CTkEntry):preset[k2]=w2.get()
		return preset
	def _update_preset_value(self,key:str,value:Any):
		self._current_preset[key]=value
		self._schedule_preview_update()
	def _render_widget(self,parent,row,item):
		key,dtype,default=item["key"],item["type"],item.get("default",False)
		val=self._current_preset.get(key,default)
		def make_callback(k):
			def cb(v=None):
				w=self._widgets.get(k)
				if not w:return
				if isinstance(w,MiniSpinbox):v=w.get()
				elif isinstance(w,ctk.CTkComboBox):v=w.get()
				elif isinstance(w,ctk.CTkCheckBox):v=bool(w.get())
				elif isinstance(w,ctk.CTkEntry):v=w.get()
				self._update_preset_value(k,v)
			return cb
		if dtype=="spin":
			w=MiniSpinbox(parent,from_=item["min"],to=item["max"],width=70,command=make_callback(key))
			w.grid(row=row,column=1,padx=5,pady=3,sticky="w");w.set(val);self._widgets[key]=w
		elif dtype=="combo":
			w=ctk.CTkComboBox(parent,values=item["values"],width=120,command=make_callback(key))
			w.grid(row=row,column=1,padx=5,pady=3,sticky="w");w.set(str(val));self._widgets[key]=w
		elif dtype=="check":
			w=ctk.CTkCheckBox(parent,text="",command=make_callback(key))
			w.grid(row=row,column=1,padx=5,pady=3,sticky="w")
			if val:w.select()
			self._widgets[key]=w
		elif dtype=="entry":
			w=ctk.CTkEntry(parent,width=100)
			w.grid(row=row,column=1,padx=5,pady=3,sticky="w");w.insert(0,str(val));self._widgets[key]=w
			w.bind("<KeyRelease>",lambda e,k=key:self._update_preset_value(k,self._widgets[k].get()))
		elif dtype=="pair_spin_wrap":
			f=ctk.CTkFrame(parent,fg_color="transparent")
			f.grid(row=row,column=1,columnspan=2,padx=5,pady=3,sticky="w")
			w1=MiniSpinbox(f,from_=item["min"],to=item["max"],width=60,command=make_callback(key))
			w1.grid(row=0,column=0,sticky="w",padx=(0,5));w1.set(val);self._widgets[key]=w1
			k2,v2=item["key2"],self._current_preset.get(item["key2"],item.get("default2",0))
			w2=MiniSpinbox(f,from_=item.get("min2",item["min"]),to=item.get("max2",item["max"]),width=60,command=make_callback(k2))
			w2.grid(row=1,column=0,sticky="w",padx=(0,5));w2.set(v2);self._widgets[k2]=w2
	def _on_select(self,choice:str):self._load_preset(choice)
	def _load_preset(self,name:str):
		self._current_name=name
		saved=self._presets.get(name,{})
		self._current_preset={}
		for group in FIELDS.values():
			for item in group:
				self._current_preset[item["key"]]=item.get("default",False)
				if "key2" in item:self._current_preset[item["key2"]]=item.get("default2",0)
		self._current_preset.update(saved)
		self._preset_list.configure(values=list(self._presets.keys()))
		self._preset_list.set(name)
		self._show_group(list(FIELDS.keys())[0])
		self._update_preview()
	def _add(self):
		name=f"preset_{len(self._presets)+1}"
		preset={}
		for group in FIELDS.values():
			for item in group:
				preset[item["key"]]=item.get("default",False)
				if "key2" in item:preset[item["key2"]]=item.get("default2",0)
		self._presets[name]=preset
		self._preset_list.configure(values=list(self._presets.keys()))
		self._load_preset(name)
	def _del(self):
		if len(self._presets)<=1:return
		del self._presets[self._current_name]
		self._load_preset(next(iter(self._presets)))
	def _save(self):
		preset=self._collect_current_preset()
		self._presets[self._current_name]=preset
		self._settings_service.set_setting('sticker_presets',self._presets)
		self._settings_service.set_setting('current_preset_name',self._current_name)
		self._on_close()
	def _reset(self):self._load_preset(self._current_name)