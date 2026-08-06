"""Serialização entre ``ProjectSession`` e ``ProjectWorkspace``."""
from __future__ import annotations

import uuid
from pathlib import Path

from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession
from src.core.domain.project_workspace import ProjectSlotSnapshot, ProjectWorkspace


def default_display_name(session: ProjectSession) -> str:
    """Nome inicial do projeto — stem do primeiro PDF importado."""
    if session.documents:
        return session.documents[0].source_pdf_path.stem
    return session.client_project.strip() or "Projeto"


def resolved_display_name(session: ProjectSession) -> str:
    name = session.display_name.strip()
    if name:
        return name
    return default_display_name(session)


def session_to_workspace(session: ProjectSession) -> ProjectWorkspace:
    project_id = session.project_id or str(uuid.uuid4())
    slots = [
        ProjectSlotSnapshot(
            source_pdf_path=str(slot.source_pdf_path),
            evaluated_component=slot.evaluated_component,
            source_kind=slot.source_kind,
            template_id=slot.template_id,
        )
        for slot in session.documents
    ]
    return ProjectWorkspace(
        id=project_id,
        client_project=session.client_project,
        template_id=session.template_id,
        report_mode=session.report_mode,
        slots=slots,
        active_index=session.active_index,
        display_name=resolved_display_name(session),
    )


def workspace_to_session(workspace: ProjectWorkspace) -> ProjectSession:
    documents = [
        ProjectDocumentSlot(
            source_pdf_path=Path(slot.source_pdf_path),
            evaluated_component=slot.evaluated_component,
            source_kind=slot.source_kind,
            template_id=slot.template_id,
        )
        for slot in workspace.slots
    ]
    display_name = (workspace.display_name or "").strip()
    if not display_name and workspace.slots:
        display_name = Path(workspace.slots[0].source_pdf_path).stem
    return ProjectSession(
        client_project=workspace.client_project,
        template_id=workspace.template_id,
        report_mode=workspace.report_mode,
        documents=documents,
        active_index=workspace.active_index,
        project_id=workspace.id,
        display_name=display_name,
    )


def slots_to_json(slots: list[ProjectSlotSnapshot]) -> list[dict]:
    return [
        {
            "source_pdf_path": slot.source_pdf_path,
            "evaluated_component": slot.evaluated_component,
            "source_kind": slot.source_kind,
            "template_id": slot.template_id,
        }
        for slot in slots
    ]


def slots_from_json(raw: list) -> list[ProjectSlotSnapshot]:
    slots: list[ProjectSlotSnapshot] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        path = str(item.get("source_pdf_path") or "").strip()
        if not path:
            continue
        slots.append(
            ProjectSlotSnapshot(
                source_pdf_path=path,
                evaluated_component=str(item.get("evaluated_component") or "Componente"),
                source_kind=str(item.get("source_kind") or "calypso"),
                template_id=item.get("template_id"),
            )
        )
    return slots
