# src/core/parser/utils.py
import re

class ParserUtils:
    @staticmethod
    def converter_para_float(valor_str: str) -> float:
        """Converte string de medida (ex: '0,0040 inch', '-0,0008') para float seguro."""
        if not valor_str or valor_str == "N/A" or valor_str == "-":
            return 0.0
        limpo = re.sub(r'[^\d\.,\-]+', '', valor_str).replace(',', '.')
        try:
            return float(limpo)
        except ValueError:
            return 0.0