"""Testes do store de fotos do PDF unificado."""
from __future__ import annotations

from pathlib import Path

from src.core.application.unified_media import (
    add_unified_image,
    resolve_unified_layout_images,
    seed_unified_images_from_pieces,
)
from src.core.domain.ports import ReportDocument, ReportImage
from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession


def _doc_with_photo(stem: str, photo: Path, *, section_id: str = "introducao") -> ReportDocument:
    return ReportDocument(
        source_pdf_path=Path(f"/tmp/{stem}.pdf"),
        client_project="Cargill",
        evaluated_component=stem,
        images=[
            ReportImage(image_path=photo, section_id=section_id, image_id=f"id-{stem}"),
        ],
        source_kind="calypso",
    )


def test_seed_takes_one_photo_per_section(tmp_path: Path) -> None:
    photo_a = tmp_path / "a.png"
    photo_b = tmp_path / "b.png"
    photo_a.write_bytes(b"a")
    photo_b.write_bytes(b"b")

    session = ProjectSession(
        client_project="Cargill",
        documents=[
            ProjectDocumentSlot(
                source_pdf_path=Path("/tmp/a.pdf"),
                evaluated_component="A",
                document=_doc_with_photo("A", photo_a),
            ),
            ProjectDocumentSlot(
                source_pdf_path=Path("/tmp/b.pdf"),
                evaluated_component="B",
                document=_doc_with_photo("B", photo_b),
            ),
        ],
    )
    assert seed_unified_images_from_pieces(session) is True
    assert session.unified_images_ready is True
    assert len(session.unified_images) == 1
    assert session.unified_images[0].image_path == photo_a
    assert seed_unified_images_from_pieces(session) is False

    layout = {"introducao": {"enabled": True, "order": 1}, "anexos": {"enabled": True, "order": 2}}
    resolved = resolve_unified_layout_images(session, session.documents, layout=layout)
    assert len(resolved) == 1

    # Usuário ainda pode adicionar fotos no store unificado.
    extra = tmp_path / "extra.png"
    extra.write_bytes(b"x")
    add_unified_image(session, extra, "introducao")
    resolved2 = resolve_unified_layout_images(session, session.documents, layout=layout)
    assert len(resolved2) == 2


def test_remove_unified_image_stays_empty_without_falling_back(tmp_path: Path) -> None:
    from src.core.application.unified_media import remove_unified_image

    photo_a = tmp_path / "a.png"
    photo_a.write_bytes(b"a")
    session = ProjectSession(
        client_project="Cargill",
        documents=[
            ProjectDocumentSlot(
                source_pdf_path=Path("/tmp/a.pdf"),
                evaluated_component="A",
                document=_doc_with_photo("A", photo_a),
            ),
        ],
    )
    assert seed_unified_images_from_pieces(session) is True
    image = session.unified_images[0]
    remove_unified_image(session, image)
    assert session.unified_images == []
    assert session.unified_images_ready is True
    layout = {"introducao": {"enabled": True}}
    resolved = resolve_unified_layout_images(session, session.documents, layout=layout)
    assert resolved == []


def test_seed_keeps_all_bosello_views(tmp_path: Path) -> None:
    photo_a = tmp_path / "a.png"
    photo_b = tmp_path / "b.png"
    photo_a.write_bytes(b"a")
    photo_b.write_bytes(b"b")
    doc = ReportDocument(
        source_pdf_path=Path("/tmp/bosello.pdf"),
        client_project="Cargill",
        evaluated_component="Tomo",
        images=[
            ReportImage(
                image_path=photo_a,
                section_id="tomografia",
                image_id="b1",
                bosello_import=True,
            ),
            ReportImage(
                image_path=photo_b,
                section_id="tomografia",
                image_id="b2",
                bosello_import=True,
            ),
        ],
        source_kind="insp_ect",
    )
    session = ProjectSession(
        client_project="Cargill",
        documents=[
            ProjectDocumentSlot(
                source_pdf_path=Path("/tmp/bosello.pdf"),
                evaluated_component="Tomo",
                document=doc,
            ),
        ],
    )
    assert seed_unified_images_from_pieces(session) is True
    assert len(session.unified_images) == 2


def test_resolve_falls_back_to_one_per_section(tmp_path: Path) -> None:
    photo_a = tmp_path / "a.png"
    photo_b = tmp_path / "b.png"
    photo_a.write_bytes(b"a")
    photo_b.write_bytes(b"b")
    session = ProjectSession(
        client_project="Cargill",
        documents=[
            ProjectDocumentSlot(
                source_pdf_path=Path("/tmp/a.pdf"),
                evaluated_component="A",
                document=_doc_with_photo("A", photo_a),
            ),
            ProjectDocumentSlot(
                source_pdf_path=Path("/tmp/b.pdf"),
                evaluated_component="B",
                document=_doc_with_photo("B", photo_b),
            ),
        ],
    )
    layout = {"introducao": {"enabled": True}}
    resolved = resolve_unified_layout_images(session, session.documents, layout=layout)
    assert len(resolved) == 1
    assert resolved[0].image_path == photo_a
