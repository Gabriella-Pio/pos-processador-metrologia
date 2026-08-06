"""Testes de serialização de projeto."""
from __future__ import annotations

from pathlib import Path

from src.core.application.project_serializer import (
    session_to_workspace,
    slots_from_json,
    slots_to_json,
    workspace_to_session,
)
from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession
from src.core.domain.project_workspace import ProjectSlotSnapshot, ProjectWorkspace


def test_session_to_workspace_roundtrip() -> None:
    session = ProjectSession(
        client_project="Cliente A",
        template_id="default",
        report_mode="mixed",
        project_id="proj-123",
        active_index=1,
        documents=[
            ProjectDocumentSlot(
                source_pdf_path=Path("/data/a.pdf"),
                evaluated_component="Peça A",
                source_kind="calypso",
            ),
            ProjectDocumentSlot(
                source_pdf_path=Path("/data/b.pdf"),
                evaluated_component="Peça B",
                source_kind="insp_ect",
                template_id="tomografia",
            ),
        ],
    )
    workspace = session_to_workspace(session)
    restored = workspace_to_session(workspace)

    assert restored.project_id == "proj-123"
    assert restored.client_project == "Cliente A"
    assert restored.active_index == 1
    assert len(restored.documents) == 2
    assert restored.documents[0].source_pdf_path == Path("/data/a.pdf")
    assert restored.documents[1].template_id == "tomografia"


def test_slots_json_roundtrip() -> None:
    slots = [
        ProjectSlotSnapshot("/x.pdf", "Comp", "calypso", None),
        ProjectSlotSnapshot("/y.pdf", "Comp2", "insp_ect", "tomografia"),
    ]
    raw = slots_to_json(slots)
    restored = slots_from_json(raw)
    assert len(restored) == 2
    assert restored[1].template_id == "tomografia"


def test_workspace_to_session_preserves_metadata() -> None:
    workspace = ProjectWorkspace(
        id="uuid-1",
        client_project="Lab",
        template_id="tomografia",
        report_mode="tomo_only",
        slots=[ProjectSlotSnapshot("/z.pdf", "Z", "insp_ect", "tomografia")],
        active_index=0,
        display_name="Lab Tomo",
    )
    session = workspace_to_session(workspace)
    assert session.project_id == "uuid-1"
    assert session.report_mode == "tomo_only"
    assert session.documents[0].evaluated_component == "Z"
