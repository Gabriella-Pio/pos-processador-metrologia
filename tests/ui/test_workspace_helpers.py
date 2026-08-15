"""Testes dos helpers puros do workspace."""
from __future__ import annotations

from pathlib import Path

from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession
from src.core.domain.ports import ReportDocument, VersionEntry
from src.ui.features.workspace.helpers.workspace_helpers import (
    dimensional_document_for_edit,
    document_with_timeline,
    preview_error_summary,
    slot_progress_label,
    version_status_text,
)


def test_slot_progress_label_prefers_filename() -> None:
    slot = ProjectDocumentSlot(
        source_pdf_path=Path("/data/peca.pdf"),
        evaluated_component="Eixo",
    )
    assert slot_progress_label(slot, 0) == "peca.pdf"


def test_preview_error_summary_uses_last_line() -> None:
    details = "Traceback...\nValueError: falhou aqui"
    assert preview_error_summary(details) == "ValueError: falhou aqui"


def test_version_status_text_priority() -> None:
    assert "Visualizando" in version_status_text(viewing_version=2, editing_from_version=1, last_registered_version=3)
    assert "Editando" in version_status_text(viewing_version=None, editing_from_version=1, last_registered_version=3)
    assert version_status_text(
        viewing_version=None, editing_from_version=None, last_registered_version=None
    ) == "Rascunho salvo"


def test_dimensional_document_picks_calypso_in_unified() -> None:
    calypso = ReportDocument(
        source_pdf_path=Path("/a.pdf"),
        client_project="C",
        evaluated_component="A",
        source_kind="calypso",
    )
    bosello = ReportDocument(
        source_pdf_path=Path("/b.pdf"),
        client_project="C",
        evaluated_component="B",
        source_kind="insp_ect",
    )
    session = ProjectSession(
        client_project="C",
        documents=[
            ProjectDocumentSlot(Path("/b.pdf"), "B", document=bosello, source_kind="insp_ect"),
            ProjectDocumentSlot(Path("/a.pdf"), "A", document=calypso, source_kind="calypso"),
        ],
    )
    assert dimensional_document_for_edit(session, bosello, unified_editing=True) is calypso


def test_document_with_timeline_replaces_history() -> None:
    from datetime import datetime

    doc = ReportDocument(
        source_pdf_path=Path("/a.pdf"),
        client_project="C",
        evaluated_component="A",
    )
    entry = VersionEntry(1, datetime.now(), "Ana", "v1")
    merged = document_with_timeline(doc, [entry])
    assert merged is not None
    assert merged.version_history == [entry]
    assert doc.version_history == []
