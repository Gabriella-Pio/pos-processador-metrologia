"""
Adapters que traduzem entre o parser/gerador reais (``src/core/parser``,
``src/core/generator``) e as portas (``src/core/domain/ports.py``) consumidas
pela UI. Único lugar onde ``PDFParserService`` e ``ReportGenerator`` são
importados diretamente.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.core.generator.constants import SECTION_TITLES, TEMPLATE_PADRAO_OFICIAL
from src.core.generator.engine import ReportGenerator
from src.core.domain.parsed_overrides import build_effective_dto, build_prose_context
from src.core.parser.parser import PDFParserService
from src.core.domain.placeholder_utils import build_placeholder_context
from src.core.domain.report_field_registry import merge_section_prose, PROSE_TEMPLATES
from src.core.domain.table_row_registry import INTRODUCAO_BLOCK_TITLES, SECTION_HEADING_DEFAULTS, merge_table_rows
from src.core.domain.ports import ReportDocument, TechnicalControlInfo
from src.core.domain.section_schema import is_navigable_section, sections_config_to_blocks
from src.core.domain.section_numbering import build_section_number_map
from src.core.domain.table_row_registry import _FIXED_SECTION_IDS
from src.core.infrastructure.template_repository import JSONTemplateRepository


class RealReportParserAdapter:
    """Adaptador real que traduz o Parser da ZEISS para o contrato da UI."""

    def parse(self, pdf_path: Path) -> ReportDocument:
        dto_resultado = PDFParserService.extrair_dados_avancados(str(pdf_path))

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
        )


class RealReportExporterAdapter:
    """Adaptador real que traduz as ações da UI para a Engine ReportLab real."""

    def __init__(self, template_repository: Optional[JSONTemplateRepository] = None) -> None:
        self._template_repository = template_repository
        self._last_section_anchor_map: dict[str, dict] = {}

    def export(self, document: ReportDocument, output_path: Path) -> Path:
        section_anchor_map: dict[str, dict] = {}
        effective_dto = build_effective_dto(document.raw_parsed_data, document.parsed_overrides)
        section_prose = self._montar_section_prose(document, effective_dto)
        placeholder_context = build_placeholder_context(effective_dto, document)
        table_rows = self._montar_table_rows(document)
        template_config = self._resolver_blocos_template(document)
        ReportGenerator.gerar_relatorio_enriquecido(
            dados_parseados=effective_dto,
            caminho_saida=str(output_path),
            cliente_projeto=document.client_project,
            componente_avaliado=document.evaluated_component,
            fotos_secoes=self._montar_fotos_secoes(document),
            versao_relatorio=self._versao_atual(document),
            controle_tecnico=self._montar_controle_tecnico(document),
            historico_versoes=self._montar_historico_versoes(document),
            template_config=template_config,
            section_page_map=section_anchor_map,
            section_prose=section_prose,
            placeholder_context=placeholder_context,
            table_rows=table_rows,
        )
        self._last_section_anchor_map = section_anchor_map
        document.last_export_path = output_path
        return output_path

    def list_sections(self, document: ReportDocument) -> list[dict]:
        """Sumário real: mesma resolução de blocos usada em ``export()``,
        traduzida para ``{"id", "title"}`` — garante que o que aparece no
        Workspace é sempre fiel ao que vai sair no PDF final.
        """
        blocos = self._resolver_blocos_template(document)
        number_map = build_section_number_map(blocos)
        fotos_por_secao: dict[str, int] = {}
        for imagem in document.images:
            fotos_por_secao[imagem.section_id] = fotos_por_secao.get(imagem.section_id, 0) + 1

        resultado = []
        for bloco in blocos:
            tipo = bloco["tipo"]
            if not is_navigable_section(tipo) and not tipo.startswith("custom_"):
                continue
            if tipo == "tomografia":
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

    # ------------------------------------------------------------- helpers
    def _resolver_blocos_template(self, document: ReportDocument) -> list[dict]:
        if document.template_id == "default" or self._template_repository is None:
            blocos = list(TEMPLATE_PADRAO_OFICIAL)
        else:
            config_salva = self._template_repository.get_template_config(document.template_id)
            blocos = (
                list(TEMPLATE_PADRAO_OFICIAL)
                if not config_salva
                else sections_config_to_blocks(config_salva)
            )
        return self._apply_section_order(blocos, document)

    def get_export_blocks(self, document: ReportDocument) -> list[dict]:
        return self._resolver_blocos_template(document)

    @staticmethod
    def _apply_section_order(blocos: list[dict], document: ReportDocument) -> list[dict]:
        if not document.section_order:
            ordered = list(blocos)
        else:
            order_index = {sid: idx for idx, sid in enumerate(document.section_order)}
            start = [b for b in blocos if b["tipo"] == "cabecalho"]
            end = [b for b in blocos if b["tipo"] == "historico_versoes"]
            middle = [b for b in blocos if b["tipo"] not in _FIXED_SECTION_IDS]
            middle.sort(key=lambda b: order_index.get(b["tipo"], 10_000))
            ordered = start + middle + end
        return RealReportExporterAdapter._inject_custom_sections(ordered, document)

    @staticmethod
    def _inject_custom_sections(blocos: list[dict], document: ReportDocument) -> list[dict]:
        if not document.custom_sections:
            return blocos
        deleted = set(document.deleted_section_ids)
        custom_blocks = [
            {"tipo": section["id"], "config": {"section_id": section["id"]}}
            for section in document.custom_sections
            if section.get("id") not in deleted
        ]
        if not custom_blocks:
            return blocos
        result: list[dict] = []
        inserted = False
        for bloco in blocos:
            if bloco["tipo"] == "historico_versoes" and not inserted:
                result.extend(custom_blocks)
                inserted = True
            result.append(bloco)
        if not inserted:
            result.extend(custom_blocks)
        return result

    def _montar_fotos_secoes(self, document: ReportDocument) -> dict:
        """Agrupa as ``ReportImage`` (já associadas a uma seção pela UI,
        via drag-and-drop) no formato ``{"secao_id": [caminho, ...]}`` que
        o ``ReportGenerator`` espera.
        """
        fotos_por_secao: dict[str, list[str]] = {}
        for imagem in document.images:
            fotos_por_secao.setdefault(imagem.section_id, []).append(str(imagem.image_path))
        return fotos_por_secao

    def _versao_atual(self, document: ReportDocument) -> str:
        if document.version_history:
            return f"v{document.version_history[-1].version_number}"
        return "v1.0"

    def _montar_controle_tecnico(self, document: ReportDocument) -> dict:
        info = document.control_info
        if info is None:
            return {}
        return {
            "measured_by": info.measured_by,
            "reviewed_by": info.reviewed_by,
            "approved_by": info.approved_by,
            "role": info.role,
            "institutional_email": info.institutional_email,
            "timestamp_str": info.timestamp.strftime("%d/%m/%Y %H:%M"),
        }

    def _montar_historico_versoes(self, document: ReportDocument) -> list[dict]:
        return [
            {
                "version_number": entrada.version_number,
                "timestamp_str": entrada.timestamp.strftime("%d/%m/%Y %H:%M"),
                "responsible_name": entrada.responsible_name,
                "description": entrada.description,
            }
            for entrada in document.version_history
        ]

    def _montar_section_prose(self, document: ReportDocument, effective_dto) -> dict[str, dict]:
        ctx = build_prose_context(effective_dto, document)
        result: dict[str, dict] = {}
        section_ids = set(PROSE_TEMPLATES.keys()) | set(document.section_overrides.keys()) | set(SECTION_HEADING_DEFAULTS.keys())
        for section_id in section_ids:
            overrides = dict(document.section_overrides.get(section_id, {}))
            merged = merge_section_prose(section_id, overrides, ctx)
            merged["section_title"] = overrides.get(
                "section_title", SECTION_HEADING_DEFAULTS.get(section_id, merged.get("section_title", ""))
            )
            if section_id == "introducao":
                for key, default in INTRODUCAO_BLOCK_TITLES.items():
                    merged.setdefault(key, overrides.get(key, default))
            result[section_id] = merged
        return result

    def _montar_table_rows(self, document: ReportDocument) -> dict[str, list]:
        stored = document.section_overrides.get("identificacao", {}).get("table_rows")
        return {"identificacao": merge_table_rows("identificacao", stored)}