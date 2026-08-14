"""Testes de sincronização de anexos e persistência de layout."""
from __future__ import annotations

from pathlib import Path

from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession
from src.core.domain.ports import ReportDocument
from src.ui.features.workspace.commands.project_commands import ProjectCommands


def test_sync_attachment_paths_preserves_persisted_paths() -> None:
    original_a = Path("/data/zeiss_a.pdf")
    original_b = Path("/data/zeiss_b.pdf")
    document = ReportDocument(
        source_pdf_path=Path("/data/export.pdf"),
        client_project="Cliente",
        evaluated_component="Peça",
        attachment_pdf_paths=[original_a, original_b],
    )
    session = ProjectSession(
        client_project="Cliente",
        documents=[
            ProjectDocumentSlot(source_pdf_path=Path("/wrong/export_copy.pdf"), evaluated_component="Peça"),
        ],
    )
    paths = ProjectCommands.sync_attachment_paths(document, session)
    assert paths == [original_a, original_b]


def test_sync_attachment_paths_defaults_to_own_source_only() -> None:
    original_a = Path("/data/zeiss_a.pdf")
    original_b = Path("/data/zeiss_b.pdf")
    document = ReportDocument(
        source_pdf_path=original_a,
        client_project="Cliente",
        evaluated_component="Peça A",
    )
    session = ProjectSession(
        client_project="Cliente",
        documents=[
            ProjectDocumentSlot(source_pdf_path=original_a, evaluated_component="Peça A"),
            ProjectDocumentSlot(source_pdf_path=original_b, evaluated_component="Peça B"),
        ],
    )
    paths = ProjectCommands.sync_attachment_paths(document, session)
    assert paths == [original_a]
    assert document.attachment_pdf_paths == [original_a]


def test_ensure_project_attachment_paths_collapses_full_lote() -> None:
    original_a = Path("/data/zeiss_a.pdf")
    original_b = Path("/data/zeiss_b.pdf")
    doc_a = ReportDocument(
        source_pdf_path=original_a,
        client_project="Cliente",
        evaluated_component="Peça A",
        attachment_pdf_paths=[original_a, original_b],
    )
    doc_b = ReportDocument(
        source_pdf_path=original_b,
        client_project="Cliente",
        evaluated_component="Peça B",
        attachment_pdf_paths=[original_a, original_b],
    )
    session = ProjectSession(
        client_project="Cliente",
        documents=[
            ProjectDocumentSlot(
                source_pdf_path=original_a,
                evaluated_component="Peça A",
                document=doc_a,
            ),
            ProjectDocumentSlot(
                source_pdf_path=original_b,
                evaluated_component="Peça B",
                document=doc_b,
            ),
        ],
    )
    ProjectCommands.ensure_project_attachment_paths(session)
    assert doc_a.attachment_pdf_paths == [original_a]
    assert doc_b.attachment_pdf_paths == [original_b]


def test_resolve_recent_file_prefers_source_pdf_path(tmp_path: Path) -> None:
    source = tmp_path / "zeiss_original.pdf"
    export = tmp_path / "export.pdf"
    source.write_text("zeiss")
    export.write_text("export")

    class FakeRecentRepo:
        def get_by_id(self, file_id: str):
            return {
                "file_path": str(export),
                "source_pdf_path": str(source),
                "client_project": "Cliente",
                "evaluated_component": "Peça",
            }

    resolution = ProjectCommands.resolve_recent_file(FakeRecentRepo(), "1")
    assert resolution.ok
    assert resolution.pdf_path == source


def test_resolve_recent_file_falls_back_to_export_when_no_source(tmp_path: Path) -> None:
    export = tmp_path / "export.pdf"
    export.write_text("export")

    class FakeRecentRepo:
        def get_by_id(self, file_id: str):
            return {
                "file_path": str(export),
                "source_pdf_path": "",
                "client_project": "Cliente",
                "evaluated_component": "Peça",
            }

    resolution = ProjectCommands.resolve_recent_file(FakeRecentRepo(), "1")
    assert resolution.ok
    assert resolution.pdf_path == export


def test_remove_document_slot_requires_multiple_documents() -> None:
    session = ProjectSession(
        client_project="Cliente",
        documents=[
            ProjectDocumentSlot(source_pdf_path=Path("/data/a.pdf"), evaluated_component="A"),
        ],
    )
    ok, message = ProjectCommands.remove_document_slot(session, 0)
    assert not ok
    assert "pelo menos" in message.lower()


def test_remove_document_slot_updates_active_index() -> None:
    session = ProjectSession(
        client_project="Cliente",
        active_index=2,
        documents=[
            ProjectDocumentSlot(source_pdf_path=Path("/data/a.pdf"), evaluated_component="A"),
            ProjectDocumentSlot(source_pdf_path=Path("/data/b.pdf"), evaluated_component="B"),
            ProjectDocumentSlot(source_pdf_path=Path("/data/c.pdf"), evaluated_component="C"),
        ],
    )
    ok, _ = ProjectCommands.remove_document_slot(session, 1)
    assert ok
    assert len(session.documents) == 2
    assert session.active_index == 1
    assert [slot.evaluated_component for slot in session.documents] == ["A", "C"]
