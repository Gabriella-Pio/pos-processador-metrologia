"""Testes do modelo de edição de relatório (core)."""
from __future__ import annotations

from pathlib import Path

from src.core.domain.parsed_overrides import build_effective_dto, get_itens_medicao_as_dicts
from src.core.parser.parser import RelatorioCalypsoDto
from src.core.parser.table_extractor import MedicaoItemDto
from src.core.domain.ports import ReportDocument
from src.core.domain.report_field_registry import default_prose_values, merge_section_prose
from src.core.domain.section_numbering import build_section_number_map, format_numbered_heading
from src.core.domain.field_sync import sync_operador_control_info
from src.core.domain.template_diff import is_data_dirty, is_layout_dirty_vs_template, serialize_layout_snapshot
from src.core.infrastructure.template_repository import JSONTemplateRepository


def test_build_effective_dto_applies_scalar_override() -> None:
    dto = RelatorioCalypsoDto(componente="Original")
    effective = build_effective_dto(dto, {"scalar": {"componente": "Editado"}})
    assert effective.componente == "Editado"


def test_build_effective_dto_applies_itens_override() -> None:
    dto = RelatorioCalypsoDto()
    dto.itens_medicao = [
        MedicaoItemDto("a", "Dim", "1", "1", "0.1", "0.1", "0", "Dentro"),
    ]
    rows = [{
        "caracteristica": "b",
        "tipo": "Dim",
        "valor_medido": "2",
        "nominal": "2",
        "tol_superior": "0.1",
        "tol_inferior": "0.1",
        "desvio": "0",
        "status": "Fora",
    }]
    effective = build_effective_dto(dto, {"itens_medicao": rows})
    assert len(effective.itens_medicao) == 1
    assert effective.itens_medicao[0].caracteristica == "b"
    assert effective.itens_medicao[0].status == "Fora"


def test_prose_template_uses_componente_placeholder() -> None:
    prose = default_prose_values("introducao", {})
    assert "{componente}" in prose["objetivo"]


def test_merge_section_prose_user_override_wins() -> None:
    ctx = {"componente": "Peça"}
    merged = merge_section_prose("introducao", {"objetivo": "Texto customizado."}, ctx)
    assert merged["objetivo"] == "Texto customizado."


def test_document_parsed_overrides_field_exists() -> None:
    doc = ReportDocument(
        source_pdf_path=Path("/tmp/x.pdf"),
        client_project="Cliente",
        evaluated_component="Peça",
    )
    doc.parsed_overrides["scalar"] = {"operador": "Maria"}
    dto = RelatorioCalypsoDto(operador="João")
    doc.raw_parsed_data = dto
    effective = build_effective_dto(doc.raw_parsed_data, doc.parsed_overrides)
    assert effective.operador == "Maria"
    assert get_itens_medicao_as_dicts(effective) == []


def test_section_number_map_includes_controle_and_historico() -> None:
    blocks = [
        {"tipo": "conclusao"},
        {"tipo": "controle_tecnico"},
        {"tipo": "historico_versoes"},
    ]
    numbers = build_section_number_map(blocks)
    assert numbers["conclusao"] == 1
    assert numbers["controle_tecnico"] == 2
    assert numbers["historico_versoes"] == 3


def test_format_numbered_heading_controle_tecnico() -> None:
    heading = format_numbered_heading(
        "controle_tecnico",
        "CONTROLE TÉCNICO",
        {"controle_tecnico": 7},
    )
    assert heading == "7. CONTROLE TÉCNICO"


def test_section_number_map_from_blocks() -> None:
    blocks = [
        {"tipo": "cabecalho"},
        {"tipo": "introducao"},
        {"tipo": "identificacao"},
        {"tipo": "resultados"},
    ]
    numbers = build_section_number_map(blocks)
    assert numbers["identificacao"] == 1
    assert numbers["resultados"] == 2
    assert "introducao" not in numbers


def test_format_numbered_heading() -> None:
    heading = format_numbered_heading(
        "identificacao",
        "IDENTIFICAÇÃO E CONDIÇÕES DE MEDIÇÃO",
        {"identificacao": 1},
    )
    assert heading.startswith("1.")


def test_template_content_defaults_round_trip(tmp_path) -> None:
    repo = JSONTemplateRepository(storage_path=str(tmp_path / "templates.json"))
    repo.save_full_template(
        "custom_1",
        {"introducao": {"enabled": True, "order": 0}},
        {"introducao": {"objetivo": "Texto {componente}"}},
        "Meu template",
    )
    assert repo.get_content_defaults("custom_1")["introducao"]["objetivo"] == "Texto {componente}"


def test_build_template_preview_document() -> None:
    from src.core.application.template_preview import (
        build_template_preview_document,
        build_template_sections_summary,
        split_template_content_defaults,
    )

    sections_config = {
        "introducao": {"enabled": True, "order": 0},
        "identificacao": {"enabled": True, "order": 1},
        "resultados": {"enabled": False, "order": 2},
    }
    content = {
        "introducao": {"objetivo": "Objetivo {componente}"},
        "_global": {"client_project": "ACME", "evaluated_component": "Peça A"},
    }
    section_defaults, global_defaults = split_template_content_defaults(content)
    assert global_defaults["client_project"] == "ACME"
    assert "introducao" in section_defaults

    doc = build_template_preview_document("custom_1", sections_config, content)
    assert doc.client_project == "ACME"
    assert doc.template_layout_override == sections_config
    assert doc.section_overrides["introducao"]["objetivo"] == "Objetivo {componente}"
    assert "resultados" in doc.deleted_section_ids

    summary = build_template_sections_summary(sections_config, content)
    assert any(s["id"] == "introducao" for s in summary)
    assert summary[0]["enabled"] is True


def test_sections_list_panel_template_mode() -> None:
    from PyQt6.QtWidgets import QApplication

    from src.ui.shared.report_editor.sections_list_panel import SectionsListPanel

    app = QApplication.instance() or QApplication([])
    panel = SectionsListPanel(mode="template")
    panel.render_sections([
        {"id": "introducao", "title": "Introdução", "enabled": True},
        {"id": "resultados", "title": "Resultados", "enabled": False},
    ])
    assert panel._mode == "template"
    assert panel._list.count() == 2
    assert panel._add_row.parentWidget() is not None


def test_template_custom_section_in_config() -> None:
    from src.core.domain.section_schema import merge_saved_template_config

    config = {
        "introducao": {"enabled": True, "order": 0},
        "custom_1": {"enabled": True, "order": 5, "title": "Observações extras"},
    }
    merged = merge_saved_template_config(config)
    custom = [s for s in merged if s.get("custom")]
    assert len(custom) == 1
    assert custom[0]["label"] == "Observações extras"


def test_interpretacao_editable_in_template_mode() -> None:
    from src.core.domain.report_field_registry import get_edit_fields

    fields = get_edit_fields("interpretacao", defaults_mode=True)
    assert any(f.key == "intro" for f in fields)


def test_effective_media_kinds_override() -> None:
    from src.core.domain.report_field_registry import effective_media_kinds, get_media_blocks

    kinds = effective_media_kinds("introducao", {"media_kinds": ["photos", "graphics"]})
    assert kinds == ["photos", "graphics"]
    blocks = get_media_blocks("introducao", kinds)
    assert len(blocks) == 2


def test_layout_dirty_vs_data_dirty_split(tmp_path) -> None:
    repo = JSONTemplateRepository(storage_path=str(tmp_path / "templates.json"))
    doc = ReportDocument(
        source_pdf_path=Path("/tmp/x.pdf"),
        client_project="Cliente",
        evaluated_component="Peça",
    )
    doc.template_id = "default"
    assert not is_layout_dirty_vs_template(doc, repo)
    assert not is_data_dirty(doc)

    doc.parsed_overrides["scalar"] = {"operador": "Maria"}
    assert not is_layout_dirty_vs_template(doc, repo)
    assert is_data_dirty(doc)

    doc.section_overrides["introducao"] = {"objetivo": "Custom"}
    assert is_layout_dirty_vs_template(doc, repo)


def test_sync_operador_control_info() -> None:
    doc = ReportDocument(
        source_pdf_path=Path("/tmp/x.pdf"),
        client_project="Cliente",
        evaluated_component="Peça",
    )
    sync_operador_control_info(doc, "João")
    assert doc.parsed_overrides["scalar"]["operador"] == "João"
    assert doc.control_info is not None
    assert doc.control_info.measured_by == "João"


def test_serialize_layout_snapshot_excludes_parsed() -> None:
    doc = ReportDocument(
        source_pdf_path=Path("/tmp/x.pdf"),
        client_project="Cliente",
        evaluated_component="Peça",
    )
    doc.section_overrides["introducao"] = {"objetivo": "X"}
    doc.parsed_overrides["scalar"] = {"operador": "Y"}
    snap = serialize_layout_snapshot(doc)
    assert "introducao" in snap["section_overrides"]
    assert "parsed_overrides" not in snap
