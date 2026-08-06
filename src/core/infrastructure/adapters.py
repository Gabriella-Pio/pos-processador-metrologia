"""
Adapters que traduzem entre o parser/gerador reais (``src/core/parser``,
``src/core/generator``) e as portas (``src/core/domain/ports.py``) consumidas
pela UI. Único lugar onde ``PDFParserService`` e ``ReportGenerator`` são
importados diretamente.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.core.application.export_context_builder import build_export_context
from src.core.application.template_block_resolver import (
    resolve_active_template_blocks,
    resolve_template_blocks,
)
from src.core.domain.section_numbering import build_section_number_map
from src.core.domain.section_schema import is_navigable_section
from src.core.domain.ports import ReportDocument, TechnicalControlInfo
from src.core.generator.constants import SECTION_TITLES
from src.core.generator.engine import ReportGenerator
from src.core.infrastructure.template_repository import JSONTemplateRepository
from src.core.parser.parser import PDFParserService


class RealReportParserAdapter:
    """Adaptador real que traduz o Parser da ZEISS para o contrato da UI."""

    def parse(self, pdf_path: Path) -> ReportDocument:
        dto_resultado = PDFParserService.extrair_dados_avancados(str(pdf_path))
        source_kind = getattr(dto_resultado, "source_kind", "calypso") or "calypso"
        maquina = getattr(dto_resultado, "maquina_mmc", "Não identificada")
        if source_kind == "insp_ect":
            maquina = getattr(dto_resultado, "equipamento_default", maquina) or maquina

        return ReportDocument(
            source_pdf_path=pdf_path,
            client_project=getattr(dto_resultado, "cliente_projeto", "Cliente Padrão"),
            evaluated_component=getattr(dto_resultado, "componente", "Componente Inspecionado"),
            control_info=TechnicalControlInfo(
                measured_by=getattr(dto_resultado, "operador", "Operador Metrologista"),
                reviewed_by="Supervisor SENAI",
                approved_by="",
                role="Técnico de Laboratório",
                institutional_email="metrologia@senaigo.com.br",
            ),
            # Payload opaco: a UI só carrega isso de volta pro exportador,
            # nunca lê seu conteúdo diretamente (ver comentário em ports.py).
            raw_parsed_data=dto_resultado,
            source_kind=source_kind,
        )


class RealReportExporterAdapter:
    """Adaptador real que traduz as ações da UI para a Engine ReportLab real."""

    def __init__(self, template_repository: Optional[JSONTemplateRepository] = None) -> None:
        self._template_repository = template_repository
        self._last_section_anchor_map: dict[str, dict] = {}

    def export(self, document: ReportDocument, output_path: Path) -> Path:
        section_anchor_map: dict[str, dict] = {}
        ctx = build_export_context(document)
        template_config = resolve_active_template_blocks(document, self._template_repository)
        ReportGenerator.gerar_relatorio_enriquecido(
            dados_parseados=ctx.effective_dto,
            caminho_saida=str(output_path),
            cliente_projeto=document.client_project,
            componente_avaliado=document.evaluated_component,
            fotos_secoes=ctx.fotos_secoes,
            versao_relatorio=ctx.versao_relatorio,
            controle_tecnico=ctx.controle_tecnico,
            historico_versoes=ctx.historico_versoes,
            template_config=template_config,
            section_page_map=section_anchor_map,
            section_prose=ctx.section_prose,
            placeholder_context=ctx.placeholder_context,
            table_rows=ctx.table_rows,
            opcoes_extras={
                "report_kind": ctx.report_kind,
                "foto_captions": ctx.foto_captions,
                "anexo_pdfs": ctx.anexo_pdfs,
            },
        )
        self._last_section_anchor_map = section_anchor_map
        document.last_export_path = output_path
        return output_path

    def list_sections(self, document: ReportDocument) -> list[dict]:
        """Sumário real: mesma resolução de blocos usada em ``export()``,
        traduzida para ``{"id", "title"}`` — garante que o que aparece no
        Workspace é sempre fiel ao que vai sair no PDF final.
        """
        blocos = resolve_template_blocks(document, self._template_repository)
        number_map = build_section_number_map(blocos)
        fotos_por_secao: dict[str, int] = {}
        for imagem in document.images:
            fotos_por_secao[imagem.section_id] = fotos_por_secao.get(imagem.section_id, 0) + 1

        resultado = []
        for bloco in blocos:
            tipo = bloco["tipo"]
            if not is_navigable_section(tipo) and not tipo.startswith("custom_"):
                continue
            quantidade_fotos = fotos_por_secao.get(tipo, 0)
            resultado.append(
                {
                    "id": tipo,
                    "title": SECTION_TITLES.get(tipo, tipo.replace("_", " ").title()),
                    "section_number": number_map.get(tipo),
                    "image_count": quantidade_fotos,
                    "has_images": quantidade_fotos > 0,
                    "page_start": (self._last_section_anchor_map.get(tipo) or {}).get("page"),
                    "anchor_rect": (self._last_section_anchor_map.get(tipo) or None),
                    "custom": tipo.startswith("custom_"),
                }
            )
        return resultado

    def get_export_blocks(self, document: ReportDocument) -> list[dict]:
        return resolve_active_template_blocks(document, self._template_repository)
