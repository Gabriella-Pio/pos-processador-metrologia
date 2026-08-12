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


def _doc_with_photo(stem: str, photo: Path) -> ReportDocument:
    return ReportDocument(
        source_pdf_path=Path(f"/tmp/{stem}.pdf"),
        client_project="Cargill",
        evaluated_component=stem,
        images=[
            ReportImage(image_path=photo, section_id="introducao", image_id=f"id-{stem}"),
        ],
        source_kind="calypso",
    )


def test_seed_and_resolve_prefers_unified_store(tmp_path: Path) -> None:
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
    assert len(session.unified_images) == 2
    assert seed_unified_images_from_pieces(session) is False

    layout = {"introducao": {"enabled": True, "order": 1}, "anexos": {"enabled": True, "order": 2}}
    resolved = resolve_unified_layout_images(session, session.documents, layout=layout)
    assert len(resolved) == 2

    # Nova foto só no store unificado — não depende das peças.
    extra = tmp_path / "extra.png"
    extra.write_bytes(b"x")
    add_unified_image(session, extra, "introducao")
    resolved2 = resolve_unified_layout_images(session, session.documents, layout=layout)
    assert len(resolved2) == 3


def test_resolve_falls_back_to_pieces_when_store_empty(tmp_path: Path) -> None:
    photo = tmp_path / "p.png"
    photo.write_bytes(b"p")
    session = ProjectSession(
        client_project="Cargill",
        documents=[
            ProjectDocumentSlot(
                source_pdf_path=Path("/tmp/a.pdf"),
                evaluated_component="A",
                document=_doc_with_photo("A", photo),
            ),
        ],
    )
    layout = {"introducao": {"enabled": True}}
    resolved = resolve_unified_layout_images(session, session.documents, layout=layout)
    assert len(resolved) == 1
    assert resolved[0].section_id == "introducao"
