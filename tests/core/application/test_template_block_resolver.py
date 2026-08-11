"""Testes do resolvedor de blocos de template."""
from __future__ import annotations

from pathlib import Path

from src.core.application.template_block_resolver import (
    apply_section_order,
    inject_custom_sections,
    resolve_active_template_blocks,
    resolve_template_blocks,
)
from src.core.domain.ports import ReportDocument
from src.core.domain.section_schema import TEMPLATE_TOMOGRAFIA_OFICIAL
from src.core.generator.constants import TEMPLATE_PADRAO_OFICIAL
from src.core.infrastructure.template_repository import JSONTemplateRepository


def _doc(**kwargs) -> ReportDocument:
    defaults = {
        "source_pdf_path": Path("/tmp/x.pdf"),
        "client_project": "Cliente",
        "evaluated_component": "Peça",
    }
    defaults.update(kwargs)
    return ReportDocument(**defaults)


def test_resolve_default_template_without_repository() -> None:
    doc = _doc(template_id="default")
    blocos = resolve_template_blocks(doc, template_repository=None)
    tipos = [b["tipo"] for b in blocos]
    assert tipos == [b["tipo"] for b in TEMPLATE_PADRAO_OFICIAL]


def test_resolve_tomography_template_uses_official_blocks(tmp_path) -> None:
    repo = JSONTemplateRepository(str(tmp_path / "templates.json"))
    doc = _doc(template_id="tomografia")
    blocos = resolve_template_blocks(doc, template_repository=repo)
    tipos = [b["tipo"] for b in blocos]
    assert "metodo_escopo" in tipos
    assert "tomografia" in tipos
    assert tipos[0] == "cabecalho"
    assert tipos[-1] == "anexos"


def test_resolve_uses_template_layout_override() -> None:
    doc = _doc(
        template_layout_override={
            "introducao": {"enabled": True, "order": 0},
            "conclusao": {"enabled": True, "order": 99},
            "resultados": {"enabled": False, "order": 2},
        }
    )
    blocos = resolve_template_blocks(doc)
    tipos = [b["tipo"] for b in blocos]
    assert tipos == ["introducao", "conclusao"]


def test_estatistico_layout_does_not_leak_mmc_sections() -> None:
    from src.core.application.statistical_aggregator import build_estatistico_sections_config

    # Layout dinâmico típico (diâmetro + cilindricidade).
    layout = build_estatistico_sections_config(["diametro", "cilindricidade"])
    doc = _doc(template_layout_override=layout)
    tipos = [b["tipo"] for b in resolve_template_blocks(doc)]
    assert "estat_resumo_diametros" in tipos
    assert "estat_resumo_cilindricidades" in tipos
    assert "estat_graficos" in tipos
    assert "estat_graficos_comp" in tipos
    assert "historico_versoes" in tipos
    assert "anexos" in tipos
    assert "controle_tecnico" not in tipos
    assert "resultados" not in tipos
    assert "grafica" not in tipos


def test_resolve_saved_custom_template(tmp_path) -> None:
    repo = JSONTemplateRepository(str(tmp_path / "templates.json"))
    repo.save_template(
        "custom_mmc",
        {
            "introducao": {"enabled": True, "order": 0},
            "resultados": {"enabled": False, "order": 1},
            "conclusao": {"enabled": True, "order": 2},
        },
    )
    doc = _doc(template_id="custom_mmc")
    tipos = [b["tipo"] for b in resolve_template_blocks(doc, repo)]
    assert "introducao" in tipos
    assert "conclusao" in tipos
    assert "resultados" not in tipos


def test_apply_section_order_respects_document_order() -> None:
    blocos = [
        {"tipo": "cabecalho", "config": {}},
        {"tipo": "conclusao", "config": {}},
        {"tipo": "introducao", "config": {}},
        {"tipo": "identificacao", "config": {}},
        {"tipo": "historico_versoes", "config": {}},
        {"tipo": "anexos", "config": {}},
    ]
    doc = _doc(section_order=["identificacao", "introducao", "conclusao", "historico_versoes"])
    ordered = apply_section_order(blocos, doc)
    tipos = [b["tipo"] for b in ordered]
    assert tipos.index("cabecalho") == 0
    assert tipos.index("introducao") == 1
    assert tipos.index("identificacao") < tipos.index("conclusao")
    assert tipos.index("conclusao") < tipos.index("historico_versoes")
    assert tipos[-1] == "anexos"


def test_inject_custom_sections_before_anexos() -> None:
    blocos = [
        {"tipo": "introducao", "config": {}},
        {"tipo": "historico_versoes", "config": {}},
        {"tipo": "anexos", "config": {}},
    ]
    doc = _doc(custom_sections=[{"id": "custom_obs", "title": "Obs"}])
    result = inject_custom_sections(blocos, doc)
    tipos = [b["tipo"] for b in result]
    assert tipos.index("historico_versoes") < tipos.index("custom_obs")
    assert tipos.index("custom_obs") < tipos.index("anexos")
    assert tipos[-1] == "anexos"


def test_inject_custom_sections_skips_deleted() -> None:
    blocos = [{"tipo": "introducao", "config": {}}]
    doc = _doc(
        custom_sections=[{"id": "custom_a"}, {"id": "custom_b"}],
        deleted_section_ids=["custom_a"],
    )
    result = inject_custom_sections(blocos, doc)
    tipos = [b["tipo"] for b in result]
    assert "custom_a" not in tipos
    assert "custom_b" in tipos


def test_resolve_active_template_blocks_skips_deleted_standard_sections() -> None:
    doc = _doc(deleted_section_ids=["resultados", "grafica"])
    tipos = [b["tipo"] for b in resolve_active_template_blocks(doc)]
    assert "resultados" not in tipos
    assert "grafica" not in tipos
    assert "introducao" in tipos
    assert "anexos" in tipos


def test_resolve_active_template_blocks_keeps_protected_sections() -> None:
    doc = _doc(deleted_section_ids=["introducao", "cabecalho", "historico_versoes", "anexos"])
    tipos = [b["tipo"] for b in resolve_active_template_blocks(doc)]
    assert "introducao" in tipos
    assert "cabecalho" in tipos
    assert "historico_versoes" not in tipos
    assert "anexos" not in tipos


def test_resolve_template_blocks_keeps_deleted_for_summary() -> None:
    doc = _doc(deleted_section_ids=["resultados"])
    tipos = [b["tipo"] for b in resolve_template_blocks(doc)]
    assert "resultados" in tipos


def test_tomography_official_block_count_matches_constant() -> None:
    doc = _doc(template_id="tomografia")
    blocos = resolve_template_blocks(doc)
    assert len(blocos) == len(TEMPLATE_TOMOGRAFIA_OFICIAL)
