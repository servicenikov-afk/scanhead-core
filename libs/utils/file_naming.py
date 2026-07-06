# --- libs/utils/file_naming.py ---
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
import datetime
from pathlib import Path
from typing import Optional, Dict, Any
class FileNameGenerator:
	DEFAULT_TEMPLATE="{date}_{type}_{time}"
	DATE_FORMAT="%Y-%m-%d"
	TIME_FORMAT="%H-%M-%S"
	def __init__(self,base_dir:Optional[Path]=None):
		self.base_dir=base_dir or Path.cwd()
		self._counter=0
	def generate(self,template:Optional[str]=None,ext:str="txt",**kwargs:Any)->Path:
		if template is None:template=self.DEFAULT_TEMPLATE
		now=datetime.datetime.now()
		variables:Dict[str,Any]={"date":now.strftime(self.DATE_FORMAT),"time":now.strftime(self.TIME_FORMAT),"timestamp":int(now.timestamp()),"type":kwargs.get("type","data"),"prefix":kwargs.get("prefix",""),"suffix":kwargs.get("suffix","")}
		if "{counter}" in template:
			self._counter+=1
			variables["counter"]=self._counter
		else:self._counter=0
		try:filename=template.format(**variables)
		except KeyError as e:raise ValueError(f"Неизвестная переменная в шаблоне: {e}")
		filename=self._clean_filename(filename)
		if not filename.endswith(f".{ext}"):filename=f"{filename}.{ext}"
		return self.base_dir/filename
	def _clean_filename(self,name:str)->str:
		name=name.replace(" ","_")
		while "__"in name:name=name.replace("__","_")
		while "--"in name:name=name.replace("--","-")
		name=name.strip("_-")
		name=name.replace("__","_")
		return name
	def reset_counter(self):
		self._counter=0