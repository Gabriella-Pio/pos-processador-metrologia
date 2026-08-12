"""Serialização entre ``ProjectSession`` e ``ProjectWorkspace``."""
from __future__ import annotations

import uuid
from typing import Any

from src.core.domain.image_workspace import deserialize_report_image, serialize_report_image
from src.core.domain.pdf_source import (
    has_source_pdf_reference,
    source_pdf_path_from_storage,
    source_pdf_path_to_storage,
)
from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession
from src.core.domain.project_workspace import ProjectSlotSnapshot, ProjectWorkspace


def default_display_name(session: ProjectSession) -> str:
    """Nome inicial do projeto — stem do primeiro PDF importado."""
    if session.documents:
        first = session.documents[0].source_pdf_path
        if has_source_pdf_reference(first):
            return first.stem
    return session.client_project.strip() or "Projeto"


def resolved_display_name(session: ProjectSession) -> str:
    name = session.display_name.strip()
    if name:
        return name
    return default_display_name(session)


def serialize_session_draft(session: ProjectSession) -> dict[str, Any]:
    return {
        "unified_deleted_section_ids": list(session.unified_deleted_section_ids),
        "unified_section_overrides": dict(session.unified_section_overrides),
        "unified_images": [serialize_report_image(img) for img in session.unified_images],
    }


def apply_draft_to_session(session: ProjectSession, draft: dict[str, Any] | None) -> None:
    if not isinstance(draft, dict):
        return
    session.unified_deleted_section_ids = list(draft.get("unified_deleted_section_ids") or [])
    session.unified_section_overrides = dict(draft.get("unified_section_overrides") or {})
    images_raw = draft.get("unified_images") or []
    session.unified_images = [
        image
        for item in images_raw
        if isinstance(item, dict) and (image := deserialize_report_image(item)) is not None
    ]


def session_to_workspace(session: ProjectSession) -> ProjectWorkspace:
    project_id = session.project_id or str(uuid.uuid4())
    slots = [
        ProjectSlotSnapshot(
            source_pdf_path=source_pdf_path_to_storage(slot.source_pdf_path),
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
        draft=serialize_session_draft(session),
    )


def workspace_to_session(workspace: ProjectWorkspace) -> ProjectSession:
    documents = [
        ProjectDocumentSlot(
            source_pdf_path=source_pdf_path_from_storage(slot.source_pdf_path),
            evaluated_component=slot.evaluated_component,
            source_kind=slot.source_kind,
            template_id=slot.template_id,
        )
        for slot in workspace.slots
    ]
    display_name = (workspace.display_name or "").strip()
    if not display_name and workspace.slots:
        first = source_pdf_path_from_storage(workspace.slots[0].source_pdf_path)
        if has_source_pdf_reference(first):
            display_name = first.stem
    session = ProjectSession(
        client_project=workspace.client_project,
        template_id=workspace.template_id,
        report_mode=workspace.report_mode,
        documents=documents,
        active_index=workspace.active_index,
        project_id=workspace.id,
        display_name=display_name,
    )
    apply_draft_to_session(session, workspace.draft)
    return session


def slots_to_json(slots: list[ProjectSlotSnapshot]) -> list[dict]:
    return [
        {
            "source_pdf_path": source_pdf_path_to_storage(slot.source_pdf_path),
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
        slots.append(
            ProjectSlotSnapshot(
                source_pdf_path=path,
                evaluated_component=str(item.get("evaluated_component") or "Componente"),
                source_kind=str(item.get("source_kind") or "calypso"),
                template_id=item.get("template_id"),
            )
        )
    return slots
