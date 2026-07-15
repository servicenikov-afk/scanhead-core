#--- gui/sticker_preview.py ---
#⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
import logging,os
from typing import Any,Optional
import customtkinter as ctk
from tkinter import ttk
from PIL import Image
from services.interfaces import IPrinterService,ISettingsService
from libs.domain_models import Product
from gui.dialogs.sticker_editor import StickerEditor
from libs.printing.sticker_generator import StickerGenerator
from services.presets_config_utils import normalize_preset
from libs.utils.name_formatter import format_sticker_name
logger=logging.getLogger(__name__)
class StickerPreview(ctk.CTkFrame):
	def __init__(self,master:Any,printer_service:IPrinterService,settings_service:ISettingsService,search_service=None):
		super().__init__(master)
		self._printer_service,self._settings_service=printer_service,settings_service
		self._search_service=search_service
		self._current_product:Optional[Product]=None
		self._sample_product_cache=None
		self._sample_address_cache=None
		self._ctk_image:Optional[ctk.CTkImage]=None
		self._icon_settings=self._load_icon("settings32.png",(20,20))
		self._last_preview_size=(0,0)
		self._preview_after_id:Optional[str]=None
		self._create_ui()
	def _load_icon(self,filename:str,size:tuple)->Optional[ctk.CTkImage]:
		try:
			path=os.path.join(os.path.dirname(os.path.dirname(__file__)),"data","icons",filename)
			if os.path.exists(path):
				img=Image.open(path)
				return ctk.CTkImage(light_image=img,dark_image=img,size=size)
		except Exception as e:logger.warning(f"Icon load failed {filename}: {e}")
		return None
	def _create_ui(self):
		self.configure(fg_color="transparent")
		self.grid_rowconfigure(0,weight=0)
		self.grid_rowconfigure(1,weight=1)
		self.grid_columnconfigure(0,weight=1)
		top=ctk.CTkFrame(self,fg_color="transparent")
		top.grid(row=0,column=0,sticky="ew",padx=2,pady=2)
		self._preset_combo=ctk.CTkComboBox(top,values=self._get_preset_names(),command=self._on_preset_change)
		self._preset_combo.set(self._settings_service.get_setting('current_preset_name','default'))
		self._preset_combo.pack(side="left",fill="x",expand=True,padx=(0,5))
		btn_settings=ctk.CTkButton(top,text="",image=self._icon_settings,width=32,command=self._open_editor)
		btn_settings.pack(side="right")
		self._preview_frame=ctk.CTkFrame(self)
		self._preview_frame.grid(row=1,column=0,sticky="nsew",padx=3,pady=3)
		self._preview_frame.grid_rowconfigure(0,weight=1)
		self._preview_frame.grid_columnconfigure(0,weight=1)
		self._preview_frame.grid_propagate(False)
		self._preview_frame.configure(width=400,height=300)
		self._preview_frame.bind("<Configure>",self._on_preview_frame_resize)
		self._preview_label=ctk.CTkLabel(self._preview_frame,text="Нет данных",text_color="gray")
		self._preview_label.grid(row=0,column=0,sticky="nsew",padx=3,pady=3)
		self._generate_preview()
	def _on_preview_frame_resize(self,event=None)->None:
		if not self._current_product:
			return
		fw=self._preview_frame.winfo_width()
		fh=self._preview_frame.winfo_height()
		if abs(fw-self._last_preview_size[0])>10 or abs(fh-self._last_preview_size[1])>10:
			self._last_preview_size=(fw,fh)
			if self._preview_after_id:
				try:
					self.after_cancel(self._preview_after_id)
				except Exception:
					pass
			self._preview_after_id=self.after(200,self._generate_preview)
	def destroy(self)->None:
		if self._preview_after_id:
			try:
				self.after_cancel(self._preview_after_id)
			except Exception:
				pass
			self._preview_after_id=None
		super().destroy()
	def _get_preset_names(self):
		presets=self._settings_service.get_setting('sticker_presets',{})
		return list(presets.keys()) if presets else ['default']
	def _on_preset_change(self,choice:str):
		self._settings_service.set_setting('current_preset_name',choice)
		self._preset_combo.set(choice)
		self._generate_preview()
	def _open_editor(self):
		self._editor=StickerEditor(self,self._settings_service,product=self._current_product,search_service=self._search_service)
		self._editor.grab_set()
	def _on_editor_close(self):
		try:
			if not self._preview_label.winfo_exists():return
		except Exception:return
		self._preset_combo.configure(values=self._get_preset_names())
		current=self._settings_service.get_setting('current_preset_name','default')
		if current in self._get_preset_names():self._preset_combo.set(current)
		try:self._generate_preview()
		except Exception:pass
	def set_product(self,product:Optional[Product]):
		self._current_product=product
		self._generate_preview()
	def clear(self):self.set_product(None)
	def _generate_preview(self):
		product=self._current_product
		address_text=" "
		if product:
			if hasattr(product,'storage_locations') and product.storage_locations:
				address_text=product.storage_locations[0] if isinstance(product.storage_locations,list) else str(product.storage_locations)
			elif hasattr(product,'address') and product.address:address_text=product.address
		else:
			if self._sample_product_cache is None:
				if self._search_service:
					try:
						results=self._search_service.search(" ")
						product_with_address=None
						first_valid_ascii=None
						for i,p in enumerate(results):
							if i>=50:break
							article=p.article or " "
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
							self._sample_address_cache=" "
					except Exception as e:logger.error(f"Failed to get sample product: {e}",exc_info=True)
			product=self._sample_product_cache
			address_text=self._sample_address_cache or " "
		if not product:
			try:self._preview_label.configure(image=None,text="Нет данных")
			except:pass
			return
		try:
			preset=self._settings_service.get_setting('sticker_presets',{}).get(
				self._settings_service.get_setting('current_preset_name','default'),{})
			preset=normalize_preset(preset)
			article_text=product.article or ""
			name_text=product.name or ""
			non_canonical_article=article_text
			if product and hasattr(product,'barcodes') and product.barcodes:
				if len(product.barcodes) >= 2:
					non_canonical_article=product.barcodes[0]
				elif len(product.barcodes) == 1:
					non_canonical_article=product.barcodes[0]
			name_text=format_sticker_name(
				name=name_text,
				article=non_canonical_article,
				prefix_article=preset.get('name', {}).get('prefix_article', False),
				truncate_for_km=preset.get('name', {}).get('truncate_for_km', False),
				max_models=preset.get('name', {}).get('max_models', 1)
			)
			pil_img=StickerGenerator(preset).generate(
				article=article_text,name=name_text,address=address_text)
			self.update_idletasks()
			fw=self._preview_frame.winfo_width()
			fh=self._preview_frame.winfo_height()
			if fw<=20 or fh<=20:
				fw,fh=400,300
			padding=10
			max_w=max(100,fw-2*padding)
			max_h=max(100,fh-2*padding)
			iw,ih=pil_img.size
			ratio=min(max_w/iw,max_h/ih)
			new_w=max(50,int(iw*ratio))
			new_h=max(50,int(ih*ratio))
			new_size=(new_w,new_h)
			pil_img=pil_img.resize(new_size,Image.Resampling.LANCZOS)
			self._ctk_image=ctk.CTkImage(light_image=pil_img,dark_image=pil_img,size=new_size)
			self._preview_label.configure(image=self._ctk_image,text="")
		except Exception as e:
			logger.error(f"Preview generation failed: {e}")
			try:self._preview_label.configure(image=None,text=f"Ошибка: {str(e)[:40]}")
			except:pass