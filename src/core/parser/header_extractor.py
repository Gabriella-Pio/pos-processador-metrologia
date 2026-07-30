import re
from typing import Dict, List, Any
from .normalizer import TextNormalizer
from .constants import (
    CHAVES_COMPONENTE, CHAVES_OPERADOR, CHAVES_MAQUINA_MMC,
    CHAVES_NUMERO_MMC, CHAVES_DATA_HORA, CHAVES_NUMERO_MEDICOES,
    CHAVES_FORA_TOLERANCIA, CHAVES_DURACAO
)

class HeaderExtractor:

    @staticmethod
    def _inicializar_dicionario() -> Dict[str, Any]:
        """Retorna o dicionário padrão com os valores iniciais do cabeçalho."""
        return {
            "componente": "Não identificado",
            "servico_oferecido": "Não informado",
            "maquina_mmc": "Não identificada",
            "numero_mmc": "Não informado",
            "operador": "Não informado",
            "data_hora": "Não informada",
            "run": "Não informado",
            "numero_medicoes_cabecalho": 0,
            "fora_tolerancia_cabecalho": 0,
            "duracao_medicao": "00:00:00,0"
        }

    @staticmethod
    def _processar_linha_chave(linha_norm: str, proxima_linha: str, dados: dict) -> bool:
        """Verifica a linha atual contra as tuplas de chaves e extrai o valor correspondente."""
        
        if any(k in linha_norm for k in CHAVES_COMPONENTE) and dados["componente"] == "Não identificado":
            if "serviço" not in linha_norm and "mmc" not in linha_norm:
                dados["componente"] = proxima_linha
                return True

        elif any(k in linha_norm for k in CHAVES_OPERADOR):
            dados["operador"] = proxima_linha
            return True

        elif any(k in linha_norm for k in CHAVES_MAQUINA_MMC):
            dados["maquina_mmc"] = proxima_linha
            return True

        elif any(k in linha_norm for k in CHAVES_NUMERO_MMC):
            dados["numero_mmc"] = proxima_linha
            return True

        elif any(k in linha_norm for k in CHAVES_DATA_HORA):
            if "202" in proxima_linha:
                dados["data_hora"] = proxima_linha
                return True

        elif any(k in linha_norm for k in CHAVES_NUMERO_MEDICOES):
            try:
                dados["numero_medicoes_cabecalho"] = int(proxima_linha.strip())
            except ValueError:
                pass
            return True

        elif any(k in linha_norm for k in CHAVES_FORA_TOLERANCIA):
            try:
                dados["fora_tolerancia_cabecalho"] = int(proxima_linha.strip())
            except ValueError:
                pass
            return True

        elif any(k in linha_norm for k in CHAVES_DURACAO):
            dados["duracao_medicao"] = proxima_linha
            return True

        return False

    @staticmethod
    def _aplicar_fallbacks(dados: dict, linhas_pag1: List[str], texto_completo: str) -> dict:
        """Aplica regras de segurança caso algum campo importante não tenha sido capturado."""
        
        # Fallback para o Número da MMC via Regex (procura por string puramente numérica longa)
        if dados["numero_mmc"] == "Não informado" or not dados["numero_mmc"].isdigit():
            for linha in linhas_pag1:
                if re.match(r"^\d{6,14}$", linha):
                    dados["numero_mmc"] = linha
                    break

        # Fallback para Data e Hora via Regex no texto integral
        if dados["data_hora"] == "Não informada" or "Page" in dados["data_hora"]:
            m_dt = re.search(r"\b\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}\b", texto_completo)
            if m_dt:
                dados["data_hora"] = m_dt.group(0)

        return dados

    @classmethod
    def extrair(cls, linhas_pag1: List[str], texto_completo: str) -> dict:
        dados = cls._inicializar_dicionario()
        i = 0

        while i < len(linhas_pag1):
            linha_original = linhas_pag1[i]
            linha_norm = TextNormalizer.remover_acentos(linha_original)

            if i + 1 < len(linhas_pag1):
                proxima_linha = linhas_pag1[i + 1]
                avancou = cls._processar_linha_chave(linha_norm, proxima_linha, dados)
                if avancou:
                    i += 1  # Pula o valor já lido na próxima linha
            i += 1

        return cls._aplicar_fallbacks(dados, linhas_pag1, texto_completo)