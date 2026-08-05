from dataclasses import dataclass, field
from typing import List, Union
import fitz
from .header_extractor import HeaderExtractor
from .table_extractor import TableExtractor, MedicaoItemDto
from .source_kind import detect_source_kind
from .insp_ect_parser import InspEctParser, RelatorioInspEctDto

@dataclass
class RelatorioCalypsoDto:
    componente: str = "Não identificado"
    servico_oferecido: str = "Não informado"
    maquina_mmc: str = "Não identificada"
    numero_mmc: str = "Não informado"
    operador: str = "Não informado"
    data_hora: str = "Não informada"
    run: str = "Não informado"
    numero_medicoes_cabecalho: int = 0
    fora_tolerancia_cabecalho: int = 0
    duracao_medicao: str = "00:00:00,0"
    software: str = "ZEISS CALYPSO"
    versao_software: str = "Não informada"
    itens_medicao: List[MedicaoItemDto] = field(default_factory=list)
    avisos_auditoria: List[str] = field(default_factory=list)
    texto_bruto_integral: str = ""
    source_kind: str = "calypso"


ParsedReportDto = Union[RelatorioCalypsoDto, RelatorioInspEctDto]


class PDFParserService:
    @staticmethod
    def extrair_dados_avancados(caminho_pdf: str) -> ParsedReportDto:
        kind = detect_source_kind(caminho_pdf)
        if kind == "insp_ect":
            return InspEctParser.parse(caminho_pdf)

        doc = fitz.open(caminho_pdf)
        texto_completo = ""
        linhas_pag1 = []

        for num_pag, pagina in enumerate(doc):
            txt = pagina.get_text("text")
            texto_completo += txt + "\n"
            if num_pag == 0:
                for l in txt.split("\n"):
                    l_trim = l.strip()
                    if l_trim:
                        linhas_pag1.append(l_trim)

        dto = RelatorioCalypsoDto(texto_bruto_integral=texto_completo)

        # 1. Extrai Cabeçalho
        dados_header = HeaderExtractor.extrair(linhas_pag1, texto_completo)
        for k, v in dados_header.items():
            setattr(dto, k, v)

        linhas_totais = [l.strip() for l in texto_completo.split("\n") if l.strip()]
        # Passa o limite oficial do cabeçalho para blindar a tabela
        dto.itens_medicao = TableExtractor.extrair(linhas_totais, limite_esperado=dto.numero_medicoes_cabecalho)

        # Fallback de contagem
        if dto.numero_medicoes_cabecalho == 0:
            dto.numero_medicoes_cabecalho = len(dto.itens_medicao)

        return dto
