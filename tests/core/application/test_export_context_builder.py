"""Testes do montador de contexto de exportação."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.core.application.export_context_builder import (
    build_anexo_pdfs,
    build_export_context,
    build_foto_captions,
    build_fotos_secoes,
    resolve_report_kind,
    resolve_versao_atual,
)
from src.core.domain.ports import ReportDocument, ReportImage, TechnicalControlInfo, VersionEntry
from src.core.parser.parser import RelatorioCalypsoDto


def _doc(**kwargs) -> ReportDocument:
    defaults = {
        "source_pdf_path": Path("/tmp/origem.pdf"),
        "client_project": "Cliente",
        "evaluated_component": "Peça",
    }
    defaults.update(kwargs)
    return ReportDocument(**defaults)


def test_resolve_report_kind_mmc_by_default() -> None:
    assert resolve_report_kind(_doc()) == "mmc"


def test_resolve_report_kind_tomografia_template() -> None:
    assert resolve_report_kind(_doc(template_id="tomografia")) == "tomografia"


def test_resolve_report_kind_insp_ect_source() -> None:
    assert resolve_report_kind(_doc(source_kind="insp_ect")) == "tomografia"


def test_resolve_versao_atual_from_history() -> None:
    doc = _doc(
        version_history=[
            VersionEntry(1, datetime(2025, 1, 1), "A", "Primeira"),
            VersionEntry(3, datetime(2025, 2, 1), "B", "Revisão"),
        ]
    )
    assert resolve_versao_atual(doc) == "v3"


def test_resolve_versao_atual_default() -> None:
    assert resolve_versao_atual(_doc()) == "v1.0"


def test_build_anexo_pdfs_uses_source_when_empty(tmp_path) -> None:
    pdf = tmp_path / "origem.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    doc = _doc(source_pdf_path=pdf)
    assert build_anexo_pdfs(doc) == [str(pdf)]


def test_build_anexo_pdfs_deduplicates(tmp_path) -> None:
    pdf = tmp_path / "origem.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    doc = _doc(
        source_pdf_path=pdf,
        attachment_pdf_paths=[pdf, pdf],
    )
    assert len(build_anexo_pdfs(doc)) == 1


def test_build_fotos_secoes_groups_by_section(tmp_path) -> None:
    img_a = tmp_path / "a.jpg"
    img_b = tmp_path / "b.jpg"
    img_a.write_bytes(b"x")
    img_b.write_bytes(b"y")
    doc = _doc(
        images=[
            ReportImage(img_a, "identificacao"),
            ReportImage(img_b, "identificacao"),
            ReportImage(img_a, "grafica"),
        ]
    )
    fotos = build_fotos_secoes(doc)
    assert fotos["identificacao"] == [str(img_a), str(img_b)]
    assert fotos["grafica"] == [str(img_a)]


def test_build_foto_captions_only_with_text(tmp_path) -> None:
    img = tmp_path / "a.jpg"
    img.write_bytes(b"x")
    doc = _doc(
        images=[
            ReportImage(img, "grafica", caption="Vista lateral"),
            ReportImage(tmp_path / "b.jpg", "grafica"),
        ]
    )
    captions = build_foto_captions(doc)
    assert captions == {str(img): "Vista lateral"}


def test_build_export_context_section_prose_user_override() -> None:
    doc = _doc(
        raw_parsed_data=RelatorioCalypsoDto(componente="Peça A"),
        section_overrides={"introducao": {"objetivo": "Objetivo customizado."}},
    )
    ctx = build_export_context(doc)
    assert ctx.section_prose["introducao"]["objetivo"] == "Objetivo customizado."
    assert ctx.report_kind == "mmc"


def test_build_export_context_tomografia_identificacao_rows() -> None:
    doc = _doc(template_id="tomografia", raw_parsed_data=RelatorioCalypsoDto())
    ctx = build_export_context(doc)
    assert ctx.report_kind == "tomografia"
    assert len(ctx.table_rows["identificacao"]) > 0
    row_ids = {row.get("id") for row in ctx.table_rows["identificacao"]}
    assert "evaluated_component" in row_ids


def test_build_export_context_applies_control_info_to_rows() -> None:
    doc = _doc(
        control_info=TechnicalControlInfo(
            measured_by="Maria",
            reviewed_by="João",
            approved_by="",
        ),
        raw_parsed_data=RelatorioCalypsoDto(),
    )
    ctx = build_export_context(doc)
    valores = {row.get("id"): row.get("value") for row in ctx.table_rows["controle_tecnico"]}
    assert valores.get("measured_by") == "Maria"
    assert valores.get("reviewed_by") == "João"


def test_build_export_context_controle_tecnico_dict() -> None:
    ts = datetime(2025, 6, 15, 14, 30)
    doc = _doc(
        control_info=TechnicalControlInfo(
            measured_by="Maria",
            reviewed_by="João",
            timestamp=ts,
        ),
        raw_parsed_data=RelatorioCalypsoDto(),
    )
    ctx = build_export_context(doc)
    assert ctx.controle_tecnico["measured_by"] == "Maria"
    assert ctx.controle_tecnico["timestamp_str"] == "15/06/2025 14:30"
