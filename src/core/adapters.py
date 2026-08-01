"""
Adapters que traduzem entre o parser/gerador reais (``src/core/parser``,
``src/core/generator``) e as portas (``src/core/ports.py``) consumidas
pela UI. Único lugar onde ``PDFParserService`` e ``ReportGenerator`` são
importados diretamente.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.core.generator.constants import SECTION_TITLES, TEMPLATE_PADRAO_OFICIAL
from src.core.generator.engine import ReportGenerator
from src.core.parser.parser import PDFParserService
from src.core.ports import ReportDocument, TechnicalControlInfo
from src.core.template_repository import JSONTemplateRepository


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
        ReportGenerator.gerar_relatorio_enriquecido(
            dados_parseados=document.raw_parsed_data,
            caminho_saida=str(output_path),
            cliente_projeto=document.client_project,
            componente_avaliado=document.evaluated_component,
            fotos_secoes=self._montar_fotos_secoes(document),
            versao_relatorio=self._versao_atual(document),
            controle_tecnico=self._montar_controle_tecnico(document),
            historico_versoes=self._montar_historico_versoes(document),
            template_config=self._resolver_blocos_template(document),
            section_page_map=section_anchor_map,
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
        fotos_por_secao: dict[str, int] = {}
        for imagem in document.images:
            fotos_por_secao[imagem.section_id] = fotos_por_secao.get(imagem.section_id, 0) + 1

        resultado = []
        for bloco in blocos:
            tipo = bloco["tipo"]
            if tipo in {"cabecalho", "tomografia"}:
                # O engine só inclui tomografia se opcoes_extras pedir
                # explicitamente — hoje o adapter não envia essa opção,
                # então ela nunca aparece no PDF final (mantém coerência).
                continue
            quantidade_fotos = fotos_por_secao.get(tipo, 0)
            resultado.append(
                {
                    "id": tipo,
                    "title": SECTION_TITLES.get(tipo, tipo.title()),
                    "image_count": quantidade_fotos,
                    "has_images": quantidade_fotos > 0,
                    "page_start": (self._last_section_anchor_map.get(tipo) or {}).get("page"),
                    "anchor_rect": (self._last_section_anchor_map.get(tipo) or None),
                }
            )
        return resultado

    # ------------------------------------------------------------- helpers
    def _resolver_blocos_template(self, document: ReportDocument) -> list[dict]:
        """Resolve a lista de blocos ``[{"tipo", "config"}, ...]`` deste
        documento: usa o template padrão oficial, a menos que o documento
        aponte pra um template customizado com configuração salva.
        """
        if document.template_id == "default" or self._template_repository is None:
            return TEMPLATE_PADRAO_OFICIAL

        config_salva = self._template_repository.get_template_config(document.template_id)
        if not config_salva:
            return TEMPLATE_PADRAO_OFICIAL

        secoes_ativas = [
            (secao_id, dados["order"])
            for secao_id, dados in config_salva.items()
            if dados.get("enabled")
        ]
        secoes_ativas.sort(key=lambda item: item[1])
        return [{"tipo": secao_id, "config": {}} for secao_id, _ in secoes_ativas]

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