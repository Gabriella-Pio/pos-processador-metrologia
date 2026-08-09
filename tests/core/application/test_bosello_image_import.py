"""Testes de importação de imagens Bosello."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from src.core.application.bosello_image_import import (
    build_bosello_image_document,
    build_manual_tomography_document,
    import_bosello_images,
    merge_bosello_images,
)
from src.core.domain.ports import ReportDocument, ReportImage
from src.core.infrastructure.adapters import RealReportParserAdapter


def test_build_manual_tomography_document_has_no_pdf() -> None:
    document = build_manual_tomography_document("Peça UF")
    assert document.template_id == "tomografia"
    assert document.source_kind == "insp_ect"
    assert document.images == []
    assert document.evaluated_component == "Peça UF"


def test_adapter_uses_image_only_path_for_insp_ect(require_insp_ect_fixture: Path) -> None:
    with patch(
        "src.core.infrastructure.adapters.build_bosello_image_document",
        wraps=build_bosello_image_document,
    ) as build_mock:
        document = RealReportParserAdapter().parse(require_insp_ect_fixture)
    build_mock.assert_called_once_with(require_insp_ect_fixture)
    assert document.source_kind == "insp_ect"


def test_merge_bosello_images_skips_when_auto_import_already_present(tmp_path: Path) -> None:
    pdf = tmp_path / "bosello.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    document = ReportDocument(
        source_pdf_path=pdf,
        client_project="Cliente",
        evaluated_component="Peça",
        images=[
            ReportImage(
                image_path=tmp_path / "existing.png",
                section_id="tomografia",
                bosello_import=True,
            )
        ],
    )
    with patch("src.core.application.bosello_image_import.import_bosello_images") as import_mock:
        added = merge_bosello_images(document, pdf)
    assert added == 0
    import_mock.assert_not_called()


def test_import_bosello_images_copies_to_persistent_dir(tmp_path: Path) -> None:
    pdf = tmp_path / "relatorio.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    raw_paths = [str(tmp_path / "raw1.png"), str(tmp_path / "raw2.png")]
    for path in raw_paths:
        Path(path).write_bytes(b"png")

    with patch(
        "src.core.application.bosello_image_import.InspEctParser.extract_graphic_images_from_pdf",
        return_value=raw_paths,
    ):
        imported = import_bosello_images(pdf)

    assert len(imported) == 2
    assert all(img.section_id == "tomografia" for img in imported)
    assert all(img.bosello_import for img in imported)
    assert imported[0].image_path.parent.name == "relatorio"
    assert imported[0].image_path.exists()
