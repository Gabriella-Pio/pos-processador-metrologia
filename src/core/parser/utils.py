# src/core/parser/utils.py
import re

from src.core.domain.number_utils import to_float


class ParserUtils:
    @staticmethod
    def converter_para_float(valor_str: str) -> float:
        """Converte string de medida (ex: '0,0040 inch', '-0,0008') para float seguro."""
        return to_float(valor_str)

    @staticmethod
    def inferir_tipo_por_nome(nome_caracteristica: str) -> str:
        """
        Limpa o nome da característica (removendo sublinhados, traços e números)
        e infere com precisão o tipo metrológico.
        """
        nome_limpo_texto = re.sub(r"[\d_\-]", " ", nome_caracteristica).lower()

        if "diametro" in nome_limpo_texto or "diâmetro" in nome_limpo_texto:
            return "DIÂMETRO"
        if "cilindricidade" in nome_limpo_texto:
            return "CILINDRICIDADE"
        if "altura" in nome_limpo_texto:
            return "ALTURA"
        if "paralelismo" in nome_limpo_texto:
            return "PARALELISMO"
        if "coaxialidade" in nome_limpo_texto:
            return "COAXIALIDADE"
        if "angulo" in nome_limpo_texto or "ângulo" in nome_limpo_texto:
            return "ÂNGULO"
        if "perpendicularidade" in nome_limpo_texto:
            return "PERPENDICULARIDADE"
        if any(
            token in nome_limpo_texto
            for token in (
                "comprimento",
                "largura",
                "profundidade",
                "espessura",
                "distancia",
                "distância",
                "raio",
            )
        ):
            return "DIMENSÃO LINEAR"
        if nome_limpo_texto.strip().startswith("dim"):
            return "DIMENSÃO LINEAR"

        return "GEOMETRIA GERAL"
