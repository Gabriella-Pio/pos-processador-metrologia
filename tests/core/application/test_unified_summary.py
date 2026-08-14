"""Sumário e seções customizadas no modo unificado."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from src.core.application.export_context_builder import build_table_rows, resolve_report_kind
from src.core.application.statistical_aggregator import build_estat_section_editor_rows
from src.core.application.unified_export import build_statistical_mmc_document
from src.core.domain.field_definitions import effective_media_kinds
from src.core.domain.ports import ReportDocument, ReportImage, TechnicalControlInfo
from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession
from src.core.parser.table_extractor import MedicaoItemDto
from src.ui.features.workspace.presenters.section_summary_presenter import SectionSummaryPresenter


def _calypso_doc(stem: str, *, values: list[tuple[str, str, str]]) -> ReportDocument:
    items = [
        MedicaoItemDto(name, "Diâmetro", measured, "10,0", "0,1", "0,1", "0", status)
        for name, measured, status in values
    ]
    dto = SimpleNamespace(
        componente=stem,
        operador="Master",
        maquina_mmc="PRISMO",
        itens_medicao=items,
        numero_medicoes_cabecalho=len(items),
        source_kind="calypso",
    )
    return ReportDocument(
        source_pdf_path=Path(f"/tmp/{stem}.pdf"),
        client_project="Cargill",
        evaluated_component=stem,
        control_info=TechnicalControlInfo(measured_by="Master", reviewed_by="Supervisor"),
        raw_parsed_data=dto,
        source_kind="calypso",
        template_id="default",
    )


def _session(slots: list[ProjectDocumentSlot]) -> ProjectSession:
    return ProjectSession(
        client_project="Cargill",
        template_id="default",
        report_mode="mmc_only",
        documents=slots,
    )


class _ExporterStub:
    def list_sections(self, document: ReportDocument) -> list[dict]:
        from src.core.application.template_block_resolver import resolve_active_template_blocks

        return [
            {"id": b["tipo"], "title": b["tipo"], "custom": False}
            for b in resolve_active_template_blocks(document)
        ]


def test_statistical_identificacao_summary_matches_export(tmp_path: Path) -> None:
    slots = [
        ProjectDocumentSlot(
            tmp_path / "p1.pdf",
            "Peça A",
            document=_calypso_doc("p1", values=[("Diametro_X", "10,0", "Dentro")]),
            source_kind="calypso",
        ),
        ProjectDocumentSlot(
            tmp_path / "p2.pdf",
            "Peça B",
            document=_calypso_doc("p2", values=[("Diametro_X", "10,1", "Dentro")]),
            source_kind="calypso",
        ),
    ]
    unified = build_statistical_mmc_document(_session(slots))
    assert resolve_report_kind(unified) == "estatistico"
    export_rows = build_table_rows(unified, "estatistico")["identificacao"]
    export_ids = [row["id"] for row in export_rows]

    items = SectionSummaryPresenter(_ExporterStub()).build(unified)
    by_id = {item.id: item for item in items}
    assert "identificacao" in by_id
    summary_rows = by_id["identificacao"].table_rows or []
    summary_ids = [row["id"] for row in summary_rows]
    assert summary_ids == export_ids
    assert "client_project" not in summary_ids
    assert "cliente" in summary_ids or "n_pecas" in summary_ids


def test_estat_resumo_exposes_tables_media_and_rows(tmp_path: Path) -> None:
    slots = [
        ProjectDocumentSlot(
            tmp_path / "p1.pdf",
            "Peça A",
            document=_calypso_doc("p1", values=[("Diametro_X", "10,0", "Dentro")]),
            source_kind="calypso",
        ),
        ProjectDocumentSlot(
            tmp_path / "p2.pdf",
            "Peça B",
            document=_calypso_doc("p2", values=[("Diametro_X", "10,1", "Dentro")]),
            source_kind="calypso",
        ),
    ]
    unified = build_statistical_mmc_document(_session(slots))
    assert "tables" in effective_media_kinds(
        "estat_resumo_diametros",
        unified.section_overrides.get("estat_resumo_diametros"),
    )
    rows = build_estat_section_editor_rows(unified.raw_parsed_data, "estat_resumo_diametros")
    assert rows
    assert "n" in rows[0]
    assert "mean" in rows[0]
    assert "fora" in rows[0]
    assert "value" not in rows[0] or not str(rows[0].get("value") or "").startswith("N=")
    items = SectionSummaryPresenter(_ExporterStub()).build(unified)
    diam = next(item for item in items if item.id == "estat_resumo_diametros")
    assert diam.table_rows
    assert "tables" in diam.media_kinds
    assert "n" in (diam.table_rows[0] or {})


def test_estat_resumo_edited_rows_reach_export_context(tmp_path: Path) -> None:
    from src.core.application.export_context_builder import build_table_rows

    slots = [
        ProjectDocumentSlot(
            tmp_path / "p1.pdf",
            "Peça A",
            document=_calypso_doc("p1", values=[("Diametro_X", "10,0", "Dentro")]),
            source_kind="calypso",
        ),
        ProjectDocumentSlot(
            tmp_path / "p2.pdf",
            "Peça B",
            document=_calypso_doc("p2", values=[("Diametro_X", "10,1", "Dentro")]),
            source_kind="calypso",
        ),
    ]
    session = _session(slots)
    session.unified_section_overrides["estat_resumo_diametros"] = {
        "table_rows": [
            {
                "id": "Diametro_X",
                "label": "Diametro_X",
                "nominal": "10 mm",
                "limits": "9,9 a 10,1",
                "n": "2",
                "mean": "10,05 mm",
                "stdev": "0,07 mm",
                "minimum": "10,0 mm",
                "maximum": "1,2 mm",
                "fora": "0",
            }
        ]
    }
    unified = build_statistical_mmc_document(session)
    rows = build_table_rows(unified, "estatistico").get("estat_resumo_diametros") or []
    assert rows
    assert rows[0]["maximum"] == "1,2 mm"


def test_unified_custom_sections_survive_rebuild(tmp_path: Path) -> None:
    slots = [
        ProjectDocumentSlot(
            tmp_path / "p1.pdf",
            "Peça A",
            document=_calypso_doc("p1", values=[("Diametro_X", "10,0", "Dentro")]),
            source_kind="calypso",
        ),
        ProjectDocumentSlot(
            tmp_path / "p2.pdf",
            "Peça B",
            document=_calypso_doc("p2", values=[("Diametro_X", "10,1", "Dentro")]),
            source_kind="calypso",
        ),
    ]
    session = _session(slots)
    session.unified_custom_sections = [
        {"id": "custom_1", "title": "Anexo técnico", "custom": True}
    ]
    session.unified_section_overrides["custom_1"] = {
        "title": "Anexo técnico",
        "body": "Texto custom",
        "media_kinds": ["photos", "tables"],
    }
    unified = build_statistical_mmc_document(session)
    assert any(item.get("id") == "custom_1" for item in unified.custom_sections)
    items = SectionSummaryPresenter(_ExporterStub()).build(unified)
    assert any(item.id == "custom_1" for item in items)
