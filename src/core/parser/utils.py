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

    @staticmethod
    def inferir_tipo_por_nome(nome_caracteristica: str) -> str:
        """
        Limpa o nome da característica (removendo sublinhados, traços e números) 
        e infere com precisão o tipo metrológico.
        """
        nome_limpo_texto = re.sub(r'[\d_\-]', ' ', nome_caracteristica).lower()
        
        if "diametro" in nome_limpo_texto or "diâmetro" in nome_limpo_texto:
            return "DIÂMETRO"
        elif "cilindricidade" in nome_limpo_texto:
            return "CILINDRICIDADE"
        elif "paralelismo" in nome_limpo_texto:
            return "PARALELISMO"
        elif "coaxialidade" in nome_limpo_texto:
            return "COAXIALIDADE"
        elif "angulo" in nome_limpo_texto or "ângulo" in nome_limpo_texto:
            return "ÂNGULO"
        elif "perpendicularidade" in nome_limpo_texto:
            return "PERPENDICULARIDADE"
        elif nome_limpo_texto.strip().startswith("dim"):
            return "DIMENSÃO LINEAR"
            
        return "GEOMETRIA GERAL"