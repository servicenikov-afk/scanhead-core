# --- services/printer_service.py ---
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
import logging, os, threading, time, subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Any, Optional
import tkinter as tk
from tkinter import messagebox
from services.interfaces import IPrinterService, ISettingsService
from services.presets_config_utils import normalize_preset
from libs.domain_models import Product
from libs.printing.pdf_renderer import PdfStickerRenderer
from gui.dialogs.print_confirm_dialog import PrintConfirmDialog
from libs.utils.name_formatter import format_sticker_name
logger=logging.getLogger(__name__)
class RealPrinterService(IPrinterService):
	def __init__(self,root:tk.Tk,settings_service:ISettingsService):
		self._root=root
		self._settings_service=settings_service
		self._renderer=PdfStickerRenderer()
		self._temp_dir=Path("temp/print")
		self._temp_dir.mkdir(parents=True,exist_ok=True)
		self._current_dialog:Optional[PrintConfirmDialog]=None
		self._cancelled=False
	def generate_sticker(self,product:Product,preset:dict)->Any:
		logger.warning("[RealPrinterService] generate_sticker() вызван, но не реализован")
		return None
	def print_sticker(self,image:Any,copies:int=1)->bool:
		logger.warning("[RealPrinterService] print_sticker() вызван, но не реализован")
		return False
	def print_queue(self,products:List[Product],one_by_one:bool=False)->bool:
		if not products:
			logger.warning("[RealPrinterService] Пустая очередь печати")
			return False
		logger.info(f"[RealPrinterService] Начало печати {len(products)} стикеров")
		preset_name=self._settings_service.get_setting('current_preset_name','default')
		presets=self._settings_service.get_setting('sticker_presets',{})
		preset=presets.get(preset_name,{})
		preset=normalize_preset(preset)
		self._cancelled=False
		self._current_dialog=PrintConfirmDialog(
			self._root,
			total_count=len(products),
			preset_name=preset_name,
			on_confirm=lambda:self._start_print_worker(products,preset),
			on_cancel=self._on_cancel
		)
		return True
	def _on_cancel(self)->None:
		self._cancelled=True
		logger.info("[RealPrinterService] Печать отменена пользователем")
	def _start_print_worker(self,products:List[Product],preset:dict)->None:
		def worker():
			try:
				timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
				pdf_path=self._temp_dir/f"stickers_{timestamp}.pdf"
				logger.info(f"[RealPrinterService] Рендер PDF: {pdf_path}")
				total=len(products)
				images=[]
				for i,product in enumerate(products):
					if self._cancelled:
						logger.info("[RealPrinterService] Рендер отменён")
						return
					try:
						article=product.article or ""
						name=product.name or ""
						address=""
						if hasattr(product,'storage_locations') and product.storage_locations:
							address=product.storage_locations[0] if isinstance(product.storage_locations,list) else str(product.storage_locations)
						elif hasattr(product,'address') and product.address:
							address=product.address
						if not address:
							logger.warning(f"[RealPrinterService] Пустой address для {product.article}: storage_locations={getattr(product,'storage_locations',None)}, address={getattr(product,'address',None)}")
						non_canonical_article=article
						if hasattr(product,'barcodes') and product.barcodes:
							if len(product.barcodes)>=2:
								non_canonical_article=product.barcodes[0]
							elif len(product.barcodes)==1:
								non_canonical_article=product.barcodes[0]
						name=format_sticker_name(
							name=name,
							article=non_canonical_article,
							prefix_article=preset.get('name',{}).get('prefix_article',False),
							truncate_for_km=preset.get('name',{}).get('truncate_for_km',False),
							max_models=preset.get('name',{}).get('max_models',1)
						)
						from libs.printing.sticker_generator import StickerGenerator
						generator=StickerGenerator(preset)
						pil_img=generator.generate(article=article,name=name,address=address)
						images.append(pil_img)
						self._root.after(0,self._update_progress,i+1,total,f"Рендеринг: {i+1}/{total}")
					except Exception as e:
						logger.error(f"[RealPrinterService] Ошибка рендера стикера {i+1}: {e}",exc_info=True)
						from PIL import Image
						blank=Image.new('RGB',(400,300),color='white')
						images.append(blank)
				if not images:raise ValueError("Нет стикеров для рендера")
				logger.info(f"[RealPrinterService] Сохранение PDF: {pdf_path}")
				if len(images)==1:images[0].save(pdf_path,'PDF',resolution=300.0)
				else:images[0].save(pdf_path,'PDF',save_all=True,append_images=images[1:],resolution=300.0)
				logger.info(f"[RealPrinterService] PDF создан: {pdf_path} ({len(images)} страниц)")
				self._send_to_printer(pdf_path)
				self._root.after(0,self._show_success)
				self._schedule_cleanup(pdf_path,delay_seconds=30)
			except Exception as e:
				logger.error(f"[RealPrinterService] Ошибка печати: {e}",exc_info=True)
				self._root.after(0,self._show_error,str(e))
		threading.Thread(target=worker,daemon=True).start()
	def _update_progress(self,current:int,total:int,status:str)->None:
		if self._current_dialog:self._current_dialog.show_progress(current,total,status)
	def _show_success(self)->None:
		if self._current_dialog:self._current_dialog.show_success()
	def _show_error(self,message:str)->None:
		if self._current_dialog:self._current_dialog.show_error(message)
		try:messagebox.showerror("Ошибка печати",f"Не удалось напечатать стикеры:\n{message}")
		except Exception as e:logger.error(f"[RealPrinterService] Не удалось показать messagebox: {e}")
	def _send_to_printer(self,pdf_path:Path)->None:
		logger.info(f"[RealPrinterService] Отправка на печать: {pdf_path}")
		pdf_readers=[
			r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
			r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe",
			r"C:\Program Files\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe",
			r"C:\Program Files (x86)\Adobe\Acrobat Reader DC\Reader\AcroRd32.exe",
		]
		for reader_path in pdf_readers:
			if os.path.exists(reader_path):
				try:
					if "SumatraPDF" in reader_path:
						subprocess.Popen([reader_path,"-print-to","Default",str(pdf_path)])
					else:
						subprocess.Popen([reader_path,"/t",str(pdf_path),"Default"])
					logger.info(f"[RealPrinterService] Отправлено на печать через {reader_path}")
					return
				except Exception as e:logger.warning(f"[RealPrinterService] Ошибка печати через {reader_path}: {e}")
		if os.name=='nt':
			os.startfile(str(pdf_path))
		else:
			subprocess.run(['xdg-open' if os.name=='posix' else 'open',str(pdf_path)],check=True)
		logger.info("[RealPrinterService] PDF открыт (печать вручную)")
	def _schedule_cleanup(self,pdf_path:Path,delay_seconds:int=30)->None:
		def cleanup():
			try:
				if pdf_path.exists():
					pdf_path.unlink()
					logger.info(f"[RealPrinterService] Удалён временный PDF: {pdf_path}")
			except Exception as e:logger.warning(f"[RealPrinterService] Не удалось удалить временный PDF: {e}")
		threading.Timer(delay_seconds,cleanup).start()