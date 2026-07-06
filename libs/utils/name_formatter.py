# --- libs/utils/name_formatter.py ---
# ⚠️ Minified code — DO NOT reformat or deobfuscate until beta.
import re
from typing import Optional

def format_sticker_name(name: str, article: str, prefix_article: bool = False, truncate_for_km: bool = False, max_models: int = 1) -> str:
	if not name:return name or ""
	if prefix_article and article:name = f"{article.strip()} {name.strip()}"
	if truncate_for_km:
		match = re.search(r'для\s+к/м', name, re.IGNORECASE)
		if match:
			rest = name[match.end():]
			parts = rest.split(',')
			if len(parts) > max_models:
				name = name[:match.start()].strip()
	return name