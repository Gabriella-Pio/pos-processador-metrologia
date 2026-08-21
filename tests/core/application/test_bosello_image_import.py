"""Testes de importação de imagens Bosello."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from PIL import Image

from src.core.application.bosello_image_import import (
    _copy_capture,
    _safe_path_component,
    attach_bosello_captures,
    bosello_images_storage_dir,
    build_bosello_image_document,
    build_manual_tomography_document,
    ensure_bosello_capture_library,
    filter_importable_image_paths,
    import_bosello_images,
    is_likely_logo_or_icon,
    merge_bosello_images,
    prune_bosello_logo_images,
    render_bosello_capture_paths,
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
    existing = tmp_path / "existing.png"
    Image.new("RGB", (800, 600), (10, 10, 10)).save(existing)
    document = ReportDocument(
        source_pdf_path=pdf,
        client_project="Cliente",
        evaluated_component="Peça",
        bosello_captured_paths=[existing],
        images=[
            ReportImage(
                image_path=existing,
                section_id="tomografia",
                bosello_import=True,
            )
        ],
    )
    with patch("src.core.application.bosello_image_import.render_bosello_capture_paths") as render_mock:
        render_mock.return_value = [tmp_path / "cap.png"]
        added = merge_bosello_images(document, pdf)
    assert added == 0
    render_mock.assert_not_called()


def test_import_bosello_images_copies_to_persistent_dir(tmp_path: Path) -> None:
    pdf = tmp_path / "relatorio.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    raw1 = tmp_path / "raw1.png"
    raw2 = tmp_path / "raw2.png"
    Image.new("RGB", (800, 600), (10, 10, 10)).save(raw1)
    Image.new("RGB", (900, 700), (20, 20, 20)).save(raw2)

    with patch(
        "src.core.application.bosello_image_import.InspEctParser.extract_graphic_images_from_pdf",
        return_value=[str(raw1), str(raw2)],
    ):
        imported = import_bosello_images(pdf)

    assert len(imported) == 2
    assert all(img.section_id == "tomografia" for img in imported)
    assert all(img.bosello_import for img in imported)
    assert imported[0].image_path.parent.name == "relatorio"
    assert imported[0].image_path.exists()


def test_is_likely_logo_or_icon_detects_small_images(tmp_path: Path) -> None:
    logo = tmp_path / "logo.png"
    Image.new("RGB", (120, 120), (0, 0, 255)).save(logo)
    zeiss = tmp_path / "zeiss.png"
    Image.new("RGB", (295, 295), (0, 0, 255)).save(zeiss)
    photo = tmp_path / "photo.png"
    Image.new("RGB", (640, 480), (10, 10, 10)).save(photo)

    assert is_likely_logo_or_icon(logo) is True
    assert is_likely_logo_or_icon(zeiss) is True
    assert is_likely_logo_or_icon(photo) is False


def test_filter_importable_image_paths_skips_zeiss_logo(require_insp_ect_fixture: Path) -> None:
    from src.core.parser.insp_ect_parser import InspEctParser

    raw_paths = [
        Path(path)
        for path in InspEctParser.extract_graphic_images_from_pdf(str(require_insp_ect_fixture))
    ]
    kept = filter_importable_image_paths(raw_paths)
    sizes = []
    for path in kept:
        with Image.open(path) as img:
            sizes.append(img.size)
    assert len(kept) == 6
    large = [size for size in sizes if size[0] > 1000]
    assert len(large) == 2


def test_import_bosello_images_skips_logos(tmp_path: Path) -> None:
    pdf = tmp_path / "relatorio.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    logo = tmp_path / "raw_logo.png"
    photo = tmp_path / "raw_photo.png"
    Image.new("RGB", (100, 100), (0, 0, 255)).save(logo)
    Image.new("RGB", (800, 600), (20, 20, 20)).save(photo)

    with patch(
        "src.core.application.bosello_image_import.InspEctParser.extract_graphic_images_from_pdf",
        return_value=[str(logo), str(photo)],
    ):
        imported = import_bosello_images(pdf)

    assert len(imported) == 1
    assert imported[0].image_path.name == "img_01.png"


def test_serialize_document_workspace_includes_bosello_library(tmp_path: Path) -> None:
    from src.core.application.project_snapshot_serializer import serialize_document_workspace

    document = ReportDocument(
        source_pdf_path=tmp_path / "a.pdf",
        client_project="Cliente",
        evaluated_component="Peça",
        bosello_captured_paths=[tmp_path / "cap1.png", tmp_path / "cap2.png"],
    )
    payload = serialize_document_workspace(document)
    assert payload["bosello_captured_paths"] == [
        str(tmp_path / "cap1.png"),
        str(tmp_path / "cap2.png"),
    ]


def test_prune_bosello_logo_images_removes_square_logos(tmp_path: Path) -> None:
    logo = tmp_path / "logo.png"
    photo = tmp_path / "photo.png"
    Image.new("RGB", (295, 295), (0, 0, 255)).save(logo)
    Image.new("RGB", (800, 600), (20, 20, 20)).save(photo)
    document = ReportDocument(
        source_pdf_path=tmp_path / "x.pdf",
        client_project="Cliente",
        evaluated_component="Peça",
        images=[
            ReportImage(image_path=logo, section_id="tomografia", bosello_import=True),
            ReportImage(image_path=photo, section_id="tomografia", bosello_import=True),
        ],
    )

    removed = prune_bosello_logo_images(document)

    assert removed == 1
    assert len(document.images) == 1
    assert document.images[0].image_path == photo


def test_remove_from_section_keeps_bosello_library(tmp_path: Path) -> None:
    pdf = tmp_path / "relatorio.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    photo = tmp_path / "raw_photo.png"
    Image.new("RGB", (800, 600), (20, 20, 20)).save(photo)
    with patch(
        "src.core.application.bosello_image_import.InspEctParser.extract_graphic_images_from_pdf",
        return_value=[str(photo)],
    ):
        library = render_bosello_capture_paths(pdf)
    document = ReportDocument(
        source_pdf_path=pdf,
        client_project="Cliente",
        evaluated_component="Peça",
        bosello_captured_paths=library,
    )
    attach_bosello_captures(document, library, "tomografia")
    assert len(document.images) == 1

    from src.ui.features.workspace.commands.media_commands import MediaCommands

    MediaCommands.remove_image(document, document.images[0])
    assert document.images == []
    assert len(document.bosello_captured_paths) == 1

    added = attach_bosello_captures(document, library, "tomografia")
    assert added == 1
    assert len(document.images) == 1


def test_ensure_bosello_capture_library_reuses_existing(tmp_path: Path) -> None:
    pdf = tmp_path / "relatorio.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    photo = tmp_path / "raw_photo.png"
    Image.new("RGB", (800, 600), (20, 20, 20)).save(photo)
    with patch(
        "src.core.application.bosello_image_import.InspEctParser.extract_graphic_images_from_pdf",
        return_value=[str(photo)],
    ) as extract_mock:
        document = ReportDocument(
            source_pdf_path=pdf,
            client_project="Cliente",
            evaluated_component="Peça",
        )
        first = ensure_bosello_capture_library(document, pdf)
        second = ensure_bosello_capture_library(document, pdf)
    assert first == second
    extract_mock.assert_called_once()


def test_render_reuses_disk_cache_without_pdf_extract(tmp_path: Path) -> None:
    pdf = tmp_path / "relatorio.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    cache_dir = bosello_images_storage_dir(pdf)
    cache_dir.mkdir(parents=True)
    cached = cache_dir / "img_01.png"
    Image.new("RGB", (800, 600), (30, 30, 30)).save(cached)

    with patch(
        "src.core.application.bosello_image_import.InspEctParser.extract_graphic_images_from_pdf",
    ) as extract_mock:
        library = render_bosello_capture_paths(pdf, replace_library=False)

    assert library == [cached]
    extract_mock.assert_not_called()


def test_build_bosello_image_document_reuses_disk_cache_on_reopen(tmp_path: Path) -> None:
    pdf = tmp_path / "bosello.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    cache_dir = bosello_images_storage_dir(pdf)
    cache_dir.mkdir(parents=True)
    cached = cache_dir / "img_01.png"
    Image.new("RGB", (800, 600), (40, 40, 40)).save(cached)

    with patch(
        "src.core.application.bosello_image_import.InspEctParser.extract_graphic_images_from_pdf",
    ) as extract_mock:
        document = build_bosello_image_document(pdf)

    extract_mock.assert_not_called()
    assert document.bosello_captured_paths == [cached]
    assert len(document.images) == 1
    assert document.images[0].image_path == cached
    assert document.images[0].bosello_import is True


def test_safe_path_component_strips_windows_invalid_names() -> None:
    assert _safe_path_component("Relatorio fim. ") == "Relatorio fim"
    assert _safe_path_component("a:b*c?.pdf") == "a_b_c_.pdf"
    assert _safe_path_component("...") == "bosello"


def test_render_falls_back_to_workspace_when_copy_next_to_pdf_fails(
    tmp_path: Path,
    monkeypatch,
) -> None:
    pdf = tmp_path / "relatorio.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    raw = tmp_path / "raw.png"
    Image.new("RGB", (800, 600), (10, 10, 10)).save(raw)
    fallback = tmp_path / "workspace-bosello"
    primary = bosello_images_storage_dir(pdf)
    monkeypatch.setattr(
        "src.core.application.bosello_image_import.workspace_bosello_storage_dir",
        lambda _pdf: fallback,
    )
    original_copy = _copy_capture

    def copy_fail_primary(src: Path, dest: Path) -> bool:
        if dest.parent == primary or primary in dest.parents:
            return False
        return original_copy(src, dest)

    monkeypatch.setattr(
        "src.core.application.bosello_image_import._copy_capture",
        copy_fail_primary,
    )
    with patch(
        "src.core.application.bosello_image_import.InspEctParser.extract_graphic_images_from_pdf",
        return_value=[str(raw)],
    ):
        library = render_bosello_capture_paths(pdf)

    assert len(library) == 1
    assert library[0].parent == fallback
    assert library[0].is_file()


def test_build_bosello_document_survives_copy_failure(tmp_path: Path) -> None:
    pdf = tmp_path / "bosello.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    with patch(
        "src.core.application.bosello_image_import.merge_bosello_images",
        side_effect=FileNotFoundError("[WinError 3] path"),
    ):
        document = build_bosello_image_document(pdf)
    assert document.source_kind == "insp_ect"
    assert document.images == []
    assert document.evaluated_component

