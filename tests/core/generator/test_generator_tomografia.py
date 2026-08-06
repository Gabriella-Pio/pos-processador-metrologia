"""Smoke: exporta PDF com template tomográfico a partir de fixture INSP ECT."""
from __future__ import annotations

from pathlib import Path

from src.core.domain.section_schema import TEMPLATE_TOMOGRAFIA_OFICIAL
from src.core.generator.engine import ReportGenerator
from src.core.infrastructure.adapters import RealReportExporterAdapter, RealReportParserAdapter
from src.core.infrastructure.template_repository import JSONTemplateRepository


def test_smoke_export_tomography_template(require_insp_ect_fixture: Path, tmp_path: Path) -> None:
    repo = JSONTemplateRepository(str(tmp_path / "templates.json"))
    assert any(t["id"] == "tomografia" for t in repo.list_templates())
    assert repo.get_template_config("tomografia")
    assert repo.get_content_defaults("tomografia")

    document = RealReportParserAdapter().parse(require_insp_ect_fixture)
    document.template_id = "tomografia"
    document.client_project = "Cliente Teste Tomografia"
    document.evaluated_component = "Peça UF"

    out = tmp_path / "tomo_out.pdf"
    exporter = RealReportExporterAdapter(template_repository=repo)
    exporter.export(document, out)
    assert out.exists()
    assert out.stat().st_size > 1000

    sections = exporter.list_sections(document)
    ids = {s["id"] for s in sections}
    assert "tomografia" in ids
    assert "metodo_escopo" in ids
    assert "resultados_inspecao" in ids
    assert "observacoes_limitacoes" in ids


def test_generator_includes_tomografia_when_in_template(require_insp_ect_fixture: Path, tmp_path: Path) -> None:
    from src.core.parser.parser import PDFParserService

    dto = PDFParserService.extrair_dados_avancados(str(require_insp_ect_fixture))
    out = tmp_path / "engine_tomo.pdf"
    ReportGenerator.gerar_relatorio_enriquecido(
        dados_parseados=dto,
        caminho_saida=str(out),
        cliente_projeto="Teste",
        componente_avaliado="Peça",
        template_config=list(TEMPLATE_TOMOGRAFIA_OFICIAL),
        opcoes_extras={"report_kind": "tomografia"},
        section_prose={},
    )
    assert out.exists() and out.stat().st_size > 500
