import unicodedata
from .constants import MAPA_LABELS

class TextNormalizer:
    @staticmethod
    def remover_acentos(texto: str) -> str:
        if not texto:
            return ""
        nfkd = unicodedata.normalize('NFKD', texto)
        return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower().strip().replace(":", "")

    @staticmethod
    def normalizar_rotulo(texto: str) -> str:
        limpo = TextNormalizer.remover_acentos(texto)
        limpo = limpo.replace("º", "o").replace("°", "o").replace("ç", "c").replace("ã", "a").replace("é", "e").replace("ú", "u")
        return MAPA_LABELS.get(limpo, limpo)