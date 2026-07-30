import re
from dataclasses import dataclass
from typing import List, Tuple
from .constants import (
    LIXO_TECNICO, SIGLAS_VALIDAS, TERMOS_PARAMETROS_MAQUINA, 
    TERMOS_CARACTERISTICAS, TERMOS_PARADA_BLOCO
)
from .utils import ParserUtils

@dataclass
class MedicaoItemDto:
    caracteristica: str
    valor_medido: str
    nominal: str
    tol_superior: str
    tol_inferior: str
    desvio: str
    status: str

class TableExtractor:

    @staticmethod
    def _eh_lixo_ou_parametro(linha_lower: str, linha_original: str) -> bool:
        if any(t in linha_lower for t in TERMOS_PARAMETROS_MAQUINA):
            return True
        if linha_lower in LIXO_TECNICO:
            return True
        if linha_original.startswith("+/") or linha_original in ["+/-", "+", "-"]:
            return True
        if re.match(r"^-?\d+([\.,]\d+)?(\s*(mm|inch|°))?$", linha_original):
            return True
        if linha_lower.startswith("max") or linha_lower.startswith("min"):
            return True
        if re.match(r"^\d+\s+-?[\d\.,]+", linha_original):
            return True
        return False

    @staticmethod
    def _eh_caracteristica_real(linhas: List[str], index_atual: int) -> bool:
        """Valida se a linha atual representa uma característica geométrica válida ou antecede uma unidade."""
        linha = linhas[index_atual]
        linha_limpa = " ".join(linha.split())
        linha_lower = linha_limpa.lower()

        if "_" in linha or linha.startswith("DIM "):
            return True
        if linha_lower in SIGLAS_VALIDAS:
            return True
        if any(termo in linha_lower for termo in TERMOS_CARACTERISTICAS):
            return True
            
        if index_atual + 1 < len(linhas):
            proxima_linha = linhas[index_atual + 1].lower()
            if "mm" in proxima_linha or "inch" in proxima_linha:
                if not re.match(r"^-?\d+([\.,]\d+)?", linha_limpa):
                    return True

        return False

    @staticmethod
    def _coletar_bloco_numerico(linhas: List[str], index_atual: int) -> List[str]:
        """Coleta os valores numéricos estritos associados à característica usando os termos de parada centralizados."""
        nums = []
        j = index_atual + 1
        
        while j < len(linhas) and j < index_atual + 12:
            prox = linhas[j]
            prox_lower = prox.lower()
            
            if any(p in prox_lower for p in TERMOS_PARADA_BLOCO) or "_" in prox or prox.startswith("DIM "):
                break
                
            if "mm" in prox or "inch" in prox or "°" in prox or re.match(r"^-?\d+([\.,]\d+)", prox):
                nums.append(prox)
            j += 1
            
        return nums

    @staticmethod
    def _mapear_colunas_numericas(nums_coletados: List[str]) -> Tuple[str, str, str, str, str]:
        """Distribui dinamicamente os valores coletados nas colunas corretas (Completa, Unilateral ou Omitida)."""
        val_medido = nums_coletados[0]
        nominal = nums_coletados[1]
        tol_sup = "0.0000"
        tol_inf = "0.0000"
        desvio = "0.0000"

        if len(nums_coletados) >= 5:
            tol_sup = nums_coletados[2]
            tol_inf = nums_coletados[3]
            desvio = nums_coletados[4]
        elif len(nums_coletados) == 4:
            terceiro_valor_float = ParserUtils.converter_para_float(nums_coletados[2])
            if terceiro_valor_float >= 0:
                tol_sup = nums_coletados[2]
                tol_inf = "N/A"
            else:
                tol_inf = nums_coletados[2]
                tol_sup = "N/A"
            desvio = nums_coletados[3]
        elif len(nums_coletados) == 3:
            tol_sup = "N/A"
            tol_inf = "N/A"
            desvio = nums_coletados[2]
        else:
            desvio = nums_coletados[2] if len(nums_coletados) > 2 else "0.0000"

        return val_medido, nominal, tol_sup, tol_inf, desvio

    @staticmethod
    def _calcular_status(desvio_str: str, tol_sup_str: str, tol_inf_str: str) -> str:
        """Calcula o status de conformidade metrológica."""
        if tol_sup_str == "N/A" or tol_inf_str == "N/A":
            return "Dentro"

        desvio = ParserUtils.converter_para_float(desvio_str)
        tol_sup = ParserUtils.converter_para_float(tol_sup_str)
        tol_inf = ParserUtils.converter_para_float(tol_inf_str)

        if desvio > tol_sup or desvio < tol_inf:
            return "Fora"
        return "Dentro"

    @classmethod
    def extrair(cls, linhas_totais: List[str], limite_esperado: int = 0) -> List[MedicaoItemDto]:
        itens = []
        i = 0

        while i < len(linhas_totais):
            linha = linhas_totais[i]
            linha_limpa = " ".join(linha.split())
            linha_lower = linha_limpa.lower()

            if cls._eh_lixo_ou_parametro(linha_lower, linha_limpa):
                i += 1
                continue

            if cls._eh_caracteristica_real(linhas_totais, i) and not linha.startswith("Page") and not "of" in linha:
                nums_coletados = cls._coletar_bloco_numerico(linhas_totais, i)

                if len(nums_coletados) >= 2:
                    if not any(item.caracteristica.lower() == linha_limpa.lower() for item in itens):
                        
                        val_medido, nominal, tol_sup, tol_inf, desvio = cls._mapear_colunas_numericas(nums_coletados)
                        status_item = cls._calcular_status(desvio, tol_sup, tol_inf)

                        itens.append(MedicaoItemDto(
                            caracteristica=linha_limpa,
                            valor_medido=val_medido,
                            nominal=nominal,
                            tol_superior=tol_sup,
                            tol_inferior=tol_inf,
                            desvio=desvio,
                            status=status_item
                        ))
            i += 1

        if limite_esperado > 0 and len(itens) > limite_esperado:
            itens = itens[:limite_esperado]
            
        return itens