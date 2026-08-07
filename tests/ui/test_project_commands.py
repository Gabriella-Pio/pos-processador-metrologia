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


def test_sync_attachment_paths_defaults_from_project_slots() -> None:
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
    assert paths == [original_a, original_b]
    assert document.attachment_pdf_paths == [original_a, original_b]


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
