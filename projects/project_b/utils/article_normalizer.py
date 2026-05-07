import re
from commands import RUS_COMMANDS

class ArticleNormalizer:
    _auto_fix_enabled = True

    @classmethod
    def set_auto_fix(cls, enabled: bool):
        cls._auto_fix_enabled = enabled

    RUS_TO_ENG = {
        'й':'q','ц':'w','у':'e','к':'r','е':'t','н':'y','г':'u','ш':'i','щ':'o','з':'p',
        'х':'[','ъ':']','ф':'a','ы':'s','в':'d','а':'f','п':'g','р':'h','о':'j','л':'k',
        'д':'l','ж':';','э':"'",'я':'z','ч':'x','с':'c','м':'v','и':'b','т':'n','ь':'m',
        'б':',','ю':'.','ё':'`',
        'Й':'Q','Ц':'W','У':'E','К':'R','Е':'T','Н':'Y','Г':'U','Ш':'I','Щ':'O','З':'P',
        'Х':'[','Ъ':']','Ф':'A','Ы':'S','В':'D','А':'F','П':'G','Р':'H','О':'J','Л':'K',
        'Д':'L','Ж':';','Э':"'",'Я':'Z','Ч':'X','С':'C','М':'V','И':'B','Т':'N','Ь':'M',
        'Б':'<','Ю':'>','Ё':'~',
    }
    
    @staticmethod
    def fix_keyboard_layout(text: str) -> str:
        if not ArticleNormalizer._auto_fix_enabled:
            return text
        return ''.join(ArticleNormalizer.RUS_TO_ENG.get(c, c) for c in text)
    
    @staticmethod
    def normalize_command(text: str) -> str:
        if not text:
            return text
        fixed = ArticleNormalizer.fix_keyboard_layout(text)
        fixed = fixed.strip()
        for rus, cmd in RUS_COMMANDS.items():
            if rus.lower() in fixed.lower():
                return cmd
        if fixed.startswith('[CMD]'):
            return fixed
        if 'CMD' in fixed.upper():
            m = re.search(r'CMD[_\w]+', fixed.upper(), re.I)
            if m:
                return f'[{m.group()}]'
        return fixed
    
    @staticmethod
    def normalize(article: str) -> str:
        if not article:
            return ""
        result = ArticleNormalizer.fix_keyboard_layout(str(article))
        result = ArticleNormalizer._clean_barcode_artifacts(result)
        result = result.strip().strip('"\'').strip()
        result = result.replace('\n', ' ').replace('\r', ' ')
        result = re.sub(r'\s+', ' ', result).strip()
        if '/' in result:
            parts = [p.strip() for p in result.split('/') if p.strip()]
            if parts:
                result = parts[0]
        result = re.sub(r'[^\w\s\.\-]', '', result)
        return result
    
    @staticmethod
    def _clean_barcode_artifacts(text: str) -> str:
        if not text:
            return text
        text = re.sub(r'^\]C\d+', '', text)
        text = re.sub(r'^\]d\d+', '', text)
        text = re.sub(r'^\]E\d+', '', text)
        text = re.sub(r'\[C\d+\]$', '', text)
        text = re.sub(r'[\x00-\x1F\x7F]', '', text)
        return text.strip()