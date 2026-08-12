"""Testes de consolidação de exportação unificada (lote)."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.core.application.unified_export import (
    UnifiedExportError,
    UnifiedExportKind,
    build_mixed_mmc_bosello_document,
    build_statistical_mmc_document,
    build_unified_export_document,
    resolve_unified_export_kind,
)
from src.core.domain.ports import ReportDocument, ReportImage, TechnicalControlInfo
from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession
from src.core.parser.table_extractor import MedicaoItemDto


def _calypso_doc(stem: str, *, values: list[tuple[str, str, str]]) -> ReportDocument:
    from types import SimpleNamespace

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


def _bosello_doc(stem: str, image_path: Path) -> ReportDocument:
    from types import SimpleNamespace

    dto = SimpleNamespace(componente=stem, source_kind="insp_ect", itens_medicao=[])
    return ReportDocument(
        source_pdf_path=Path(f"/tmp/{stem}_bosello.pdf"),
        client_project="Cargill",
        evaluated_component=stem,
        raw_parsed_data=dto,
        source_kind="insp_ect",
        template_id="tomografia",
        images=[
            ReportImage(
                image_path=image_path,
                section_id="tomografia",
                image_id="img1",
                bosello_import=True,
            )
        ],
        bosello_captured_paths=[image_path],
    )


def _session(slots: list[ProjectDocumentSlot], *, mode: str = "mixed") -> ProjectSession:
    return ProjectSession(
        client_project="Cargill",
        template_id="default",
        report_mode=mode,  # type: ignore[arg-type]
        documents=slots,
        active_index=0,
    )


def test_resolve_kind_statistical() -> None:
    slots = [
        ProjectDocumentSlot(
            Path("/tmp/a.pdf"),
            "Peça",
            document=_calypso_doc("a", values=[("Diametro_X", "10,0", "Dentro")]),
            source_kind="calypso",
        ),
        ProjectDocumentSlot(
            Path("/tmp/b.pdf"),
            "Peça",
            document=_calypso_doc("b", values=[("Diametro_X", "10,1", "Dentro")]),
            source_kind="calypso",
        ),
    ]
    assert resolve_unified_export_kind(_session(slots, mode="mmc_only")) == (
        UnifiedExportKind.STATISTICAL_MMC
    )


def test_resolve_kind_mixed() -> None:
    img = Path("/tmp/fake_bosello.png")
    slots = [
        ProjectDocumentSlot(
            Path("/tmp/mmc.pdf"),
            "Pistão",
            document=_calypso_doc("pistao", values=[("Diametro_X", "25,4", "Dentro")]),
            source_kind="calypso",
        ),
        ProjectDocumentSlot(
            Path("/tmp/tomo.pdf"),
            "Pistão",
            document=_bosello_doc("pistao", img),
            source_kind="insp_ect",
        ),
    ]
    assert resolve_unified_export_kind(_session(slots)) == UnifiedExportKind.MIXED_MMC_BOSSELLO


def test_build_statistical_document(tmp_path: Path) -> None:
    slots = [
        ProjectDocumentSlot(
            tmp_path / "p1.pdf",
            "Carcaça",
            document=_calypso_doc(
                "p1",
                values=[
                    ("Diametro_ASSENTO ENTRADA", "81,99", "Dentro"),
                    ("Cilindricidade EMBOLO", "0,05", "Fora"),
                ],
            ),
            source_kind="calypso",
        ),
        ProjectDocumentSlot(
            tmp_path / "p2.pdf",
            "Carcaça",
            document=_calypso_doc(
                "p2",
                values=[
                    ("Diametro_ASSENTO ENTRADA", "81,98", "Dentro"),
                    ("Cilindricidade EMBOLO", "0,04", "Fora"),
                ],
            ),
            source_kind="calypso",
        ),
    ]
    doc = build_statistical_mmc_document(_session(slots, mode="mmc_only"))
    assert doc.template_id == "estatistico"
    assert len(doc.raw_parsed_data.series) == 2
    assert doc.template_layout_override is not None
    assert doc.template_layout_override["estat_resumo_diametros"]["enabled"] is True
    assert doc.template_layout_override["estat_resumo_cilindricidades"]["enabled"] is True
    assert doc.template_layout_override["estat_resumo_alturas"]["enabled"] is False
    assert doc.template_layout_override["historico_versoes"]["enabled"] is True
    assert doc.template_layout_override["anexos"]["enabled"] is True
    assert len(doc.attachment_pdf_paths) == 2
    intro_rows = doc.section_overrides["introducao"]["table_rows"]
    intro_ids = [r["id"] for r in intro_rows]
    assert "fora_diametro" in intro_ids
    assert "fora_cilindricidade" in intro_ids
    assert "fora_altura" not in intro_ids
    assert next(r for r in intro_rows if r["id"] == "fora_diametro")["label"] == "DIÂMETROS FORA"
    assert next(r for r in intro_rows if r["id"] == "fora_cilindricidade")["label"] == (
        "CILINDRICIDADES FORA"
    )
    cyl_note = doc.section_overrides["estat_resumo_cilindricidades"]["nota"]
    assert "Resumo das cilindricidades" in cyl_note
    assert "ocorrência" in cyl_note
    assert "estat_resumo_diametros" not in doc.section_overrides or not str(
        (doc.section_overrides.get("estat_resumo_diametros") or {}).get("nota") or ""
    ).strip()


def test_statistical_uses_unified_images_store(tmp_path: Path) -> None:
    photo = tmp_path / "peca.png"
    photo.write_bytes(b"png")
    slots = [
        ProjectDocumentSlot(
            tmp_path / "p1.pdf",
            "Carcaça",
            document=_calypso_doc(
                "p1",
                values=[("Diametro_X", "10,0", "Dentro")],
            ),
            source_kind="calypso",
        ),
        ProjectDocumentSlot(
            tmp_path / "p2.pdf",
            "Carcaça",
            document=_calypso_doc(
                "p2",
                values=[("Diametro_X", "10,1", "Dentro")],
            ),
            source_kind="calypso",
        ),
    ]
    session = _session(slots, mode="mmc_only")
    session.unified_images = [
        ReportImage(image_path=photo, section_id="introducao", image_id="u1"),
    ]
    doc = build_statistical_mmc_document(session)
    assert len(doc.images) == 1
    assert doc.images[0].section_id == "introducao"
    assert doc.images[0].image_path == photo


def test_statistical_altura_only_enables_altura_sections(tmp_path: Path) -> None:
    slots = [
        ProjectDocumentSlot(
            tmp_path / "bico13.pdf",
            "BICO",
            document=_calypso_doc(
                "bico13",
                values=[("altura bico", "89,8045 mm", "Dentro")],
            ),
            source_kind="calypso",
        ),
        ProjectDocumentSlot(
            tmp_path / "bico14.pdf",
            "BICO",
            document=_calypso_doc(
                "bico14",
                values=[("altura bico", "89,8100 mm", "Dentro")],
            ),
            source_kind="calypso",
        ),
    ]
    doc = build_statistical_mmc_document(_session(slots, mode="mmc_only"))
    assert [s.tipo for s in doc.raw_parsed_data.series] == ["altura"]
    assert doc.template_layout_override["estat_resumo_alturas"]["enabled"] is True
    assert doc.template_layout_override["estat_detalhe_alturas"]["enabled"] is True
    assert doc.template_layout_override["estat_resumo_diametros"]["enabled"] is False
    assert doc.template_layout_override["estat_resumo_cilindricidades"]["enabled"] is False
    intro = doc.section_overrides.get("introducao") or {}
    assert "alturas" in str(intro.get("escopo", "")).lower()
    intro_rows = intro.get("table_rows") or []
    assert any(r["id"] == "fora_altura" for r in intro_rows)
    assert not any(r["id"] == "fora_diametro" for r in intro_rows)
    assert next(r for r in intro_rows if r["id"] == "fora_altura")["label"] == "ALTURAS FORA"


def test_statistical_respects_unified_deleted_sections(tmp_path: Path) -> None:
    slots = [
        ProjectDocumentSlot(
            tmp_path / "p1.pdf",
            "Peça",
            document=_calypso_doc("p1", values=[("Diametro_X", "10,0", "Dentro")]),
            source_kind="calypso",
        ),
        ProjectDocumentSlot(
            tmp_path / "p2.pdf",
            "Peça",
            document=_calypso_doc("p2", values=[("Diametro_X", "10,1", "Dentro")]),
            source_kind="calypso",
        ),
    ]
    session = _session(slots, mode="mmc_only")
    session.unified_deleted_section_ids = ["historico_versoes", "anexos"]
    doc = build_statistical_mmc_document(session)
    assert "historico_versoes" in doc.deleted_section_ids
    assert "anexos" in doc.deleted_section_ids


def test_statistical_keeps_introducao_photos(tmp_path: Path) -> None:
    foto = tmp_path / "peca.png"
    foto.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)
    doc1 = _calypso_doc("p1", values=[("Diametro_X", "10,0", "Dentro")])
    doc1.images = [
        ReportImage(image_path=foto, section_id="introducao", image_id="intro1")
    ]
    doc2 = _calypso_doc("p2", values=[("Diametro_X", "10,1", "Dentro")])
    slots = [
        ProjectDocumentSlot(tmp_path / "p1.pdf", "Peça", document=doc1, source_kind="calypso"),
        ProjectDocumentSlot(tmp_path / "p2.pdf", "Peça", document=doc2, source_kind="calypso"),
    ]
    unified = build_statistical_mmc_document(_session(slots, mode="mmc_only"))
    assert len(unified.images) == 1
    assert unified.images[0].section_id == "introducao"
    assert Path(unified.images[0].image_path) == foto


def test_build_mixed_requires_bosello_images(tmp_path: Path) -> None:
    img = tmp_path / "cap.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)
    slots = [
        ProjectDocumentSlot(
            tmp_path / "mmc.pdf",
            "Pistão",
            document=_calypso_doc("pistao", values=[("Diametro_X", "25,4", "Dentro")]),
            source_kind="calypso",
        ),
        ProjectDocumentSlot(
            tmp_path / "tomo.pdf",
            "Pistão",
            document=_bosello_doc("pistao", img),
            source_kind="insp_ect",
        ),
    ]
    doc = build_mixed_mmc_bosello_document(_session(slots))
    assert doc.template_id == "mixed"
    assert any(img.section_id == "tomografia" for img in doc.images)
    assert doc.attachment_pdf_paths
    intro_rows = doc.section_overrides["introducao"]["table_rows"]
    by_id = {row["id"]: row for row in intro_rows}
    assert by_id["metodos"]["label"] == "MÉTODOS"
    assert "dimensional (CMM)" in by_id["metodos"]["value"]
    assert "tomográfico (Bosello)" in by_id["metodos"]["value"]
    assert by_id["tipo_analise"]["value"] == "Dimensional e tomográfica"
    assert "PRISMO" in by_id["equipamentos"]["value"]
    grafica = doc.section_overrides.get("grafica", {})
    assert "graphics" in grafica.get("media_kinds", [])
    layout = doc.template_layout_override or {}
    assert layout.get("grafica", {}).get("enabled") is True


def test_build_unified_unsupported() -> None:
    slots = [
        ProjectDocumentSlot(
            Path("/tmp/only.pdf"),
            "X",
            document=_calypso_doc("x", values=[("Diametro_X", "1", "Dentro")]),
            source_kind="calypso",
        )
    ]
    with pytest.raises(UnifiedExportError):
        build_unified_export_document(_session(slots))
