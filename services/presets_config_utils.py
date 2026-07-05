#--- services/presets_config_utils.py ---
#⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
from typing import Any
def to_nested(flat:dict)->dict:
	return {
		'sticker':{'width_mm':flat.get('width_mm',58),'height_mm':flat.get('height_mm',35),'orientation':flat.get('orientation','portrait'),'border':flat.get('border',True),'background_color':'#FFFFFF','dpi':300},
		'fonts':{'name_size':flat.get('name_size',7),'article_size':flat.get('article_size',8),'address_size':flat.get('address_size',6)},
		'layout':{'show_barcode':flat.get('barcode_enabled',True),'show_qr':flat.get('barcode_type')=='qr','article_position':'top' if flat.get('article_enabled',True) else 'hidden','show_address':flat.get('address_enabled',True),'address_position':'bottom'},
		'article':{'enabled':flat.get('article_enabled',True),'size':flat.get('article_size',8),'align':flat.get('article_align','center'),'bold':flat.get('article_bold',True),'offset_x':flat.get('article_offset_x',0),'offset_y':flat.get('article_offset_y',15)},
		'name':{'enabled':flat.get('name_enabled',True),'size':flat.get('name_size',7),'align':flat.get('name_align','center'),'max_lines':flat.get('name_max_lines',5),'bold':flat.get('name_bold',False),'italic':flat.get('name_italic',False),'offset_x':flat.get('name_offset_x',0),'offset_y':flat.get('name_offset_y',20)},
		'address':{'enabled':flat.get('address_enabled',True),'size':flat.get('address_size',6),'align':flat.get('address_align','right'),'bold':flat.get('address_bold',False),'italic':flat.get('address_italic',False),'offset_x':flat.get('address_offset_x',0),'offset_y':flat.get('address_offset_y',-165)},
		'barcode':{'enabled':flat.get('barcode_enabled',True),'type':flat.get('barcode_type','auto'),'position':flat.get('barcode_position','bottom'),'qr_size_mm':flat.get('barcode_qr_size_mm',16),'code128_width_mm':flat.get('code128_width_mm',56),'code128_height_mm':flat.get('code128_height_mm',5),'show_text':flat.get('barcode_show_text',True),'text_size':flat.get('barcode_text_size',5),'offset_x':flat.get('barcode_offset_x',0),'offset_y':flat.get('barcode_offset_y',-25),'text_offset_x':flat.get('barcode_text_offset_x',0),'text_offset_y':flat.get('barcode_text_offset_y',-11),'text_scale_x':flat.get('barcode_text_scale_x',10)/10.0,'text_scale_y':flat.get('barcode_text_scale_y',50)/10.0}
	}
def normalize_preset(preset:dict)->dict:
	if not preset:return to_nested({})
	if 'sticker' in preset and 'fonts' in preset and 'layout' in preset:return preset
	flat={k:v for k,v in preset.items() if not isinstance(v,dict)}
	for section in ['sticker','fonts','layout','article','name','address','barcode']:
		if section in preset and isinstance(preset[section],dict):flat.update(preset[section])
	return to_nested(flat)
def to_flat(nested:dict)->dict:
	flat={}
	for section in ['sticker','fonts','layout','article','name','address','barcode']:
		if section in nested and isinstance(nested[section],dict):flat.update(nested[section])
	return flat