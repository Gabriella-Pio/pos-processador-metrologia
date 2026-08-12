"""Serialização de snapshot completo de projeto (schema v1)."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession
from src.core.domain.image_workspace import deserialize_report_image, serialize_report_image
from src.core.domain.ports import ReportDocument, VersionEntry

SCHEMA_VERSION = 1


def serialize_document_workspace(document: ReportDocument) -> dict[str, Any]:
    images = [serialize_report_image(img) for img in document.images]
    return {
        "template_id": document.template_id,
        "section_overrides": document.section_overrides,
        "parsed_overrides": document.parsed_overrides,
        "section_order": document.section_order,
        "images": images,
        "bosello_captured_paths": [str(path) for path in document.bosello_captured_paths],
        "custom_sections": document.custom_sections,
        "deleted_section_ids": document.deleted_section_ids,
        "extra_section_ids": list(getattr(document, "extra_section_ids", None) or []),
        "attachment_pdf_paths": [str(path) for path in document.attachment_pdf_paths],
    }


def apply_workspace_to_document(document: ReportDocument, workspace: dict[str, Any]) -> None:
    document.template_id = workspace.get("template_id") or document.template_id
    document.section_overrides = dict(workspace.get("section_overrides") or {})
    document.parsed_overrides = dict(workspace.get("parsed_overrides") or {})
    order_raw = workspace.get("section_order")
    document.section_order = list(order_raw) if order_raw else None
    images_raw = workspace.get("images") or []
    document.images = [
        image
        for item in images_raw
        if (image := deserialize_report_image(item)) is not None
    ]
    document.custom_sections = list(workspace.get("custom_sections") or [])
    document.deleted_section_ids = list(workspace.get("deleted_section_ids") or [])
    document.extra_section_ids = list(workspace.get("extra_section_ids") or [])
    attachment_raw = workspace.get("attachment_pdf_paths") or []
    document.attachment_pdf_paths = [Path(path) for path in attachment_raw if path]
    bosello_raw = workspace.get("bosello_captured_paths") or []
    document.bosello_captured_paths = [Path(path) for path in bosello_raw if path]


def serialize_version_history(entries: list[VersionEntry]) -> list[dict[str, Any]]:
    return [
        {
            "version_number": entry.version_number,
            "timestamp": entry.timestamp.isoformat(),
            "responsible_name": entry.responsible_name,
            "description": entry.description,
        }
        for entry in entries
    ]


def deserialize_version_history(raw: list[Any]) -> list[VersionEntry]:
    entries: list[VersionEntry] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        timestamp_raw = item.get("timestamp")
        if isinstance(timestamp_raw, str):
            try:
                timestamp = datetime.fromisoformat(timestamp_raw)
            except ValueError:
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()
        entries.append(
            VersionEntry(
                version_number=int(item.get("version_number") or 0),
                timestamp=timestamp,
                responsible_name=str(item.get("responsible_name") or ""),
                description=str(item.get("description") or ""),
            )
        )
    return entries


def serialize_project_snapshot(session: ProjectSession) -> str:
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "session": {
            "project_id": session.project_id,
            "display_name": session.display_name,
            "client_project": session.client_project,
            "template_id": session.template_id,
            "report_mode": session.report_mode,
            "active_index": session.active_index,
            "unified_deleted_section_ids": list(session.unified_deleted_section_ids),
            "unified_section_overrides": dict(session.unified_section_overrides),
            "unified_images": [serialize_report_image(img) for img in session.unified_images],
            "slots": [
                {
                    "source_pdf_path": str(slot.source_pdf_path),
                    "evaluated_component": slot.evaluated_component,
                    "source_kind": slot.source_kind,
                    "template_id": slot.template_id,
                }
                for slot in session.documents
            ],
        },
        "slots": [],
    }
    for slot in session.documents:
        if slot.document is None:
            continue
        payload["slots"].append(
            {
                "source_pdf_path": str(slot.source_pdf_path),
                "workspace": serialize_document_workspace(slot.document),
                "version_history": serialize_version_history(slot.document.version_history),
            }
        )
    return json.dumps(payload, ensure_ascii=False)


def deserialize_project_snapshot(
    snapshot_json: str,
) -> tuple[ProjectSession, dict[str, dict[str, Any]], dict[str, list[VersionEntry]]]:
    payload = json.loads(snapshot_json)
    if not isinstance(payload, dict):
        raise ValueError("snapshot payload must be a JSON object")

    session_raw = payload.get("session") or {}
    slots_raw = session_raw.get("slots") or []
    documents: list[ProjectDocumentSlot] = []
    for item in slots_raw:
        if not isinstance(item, dict):
            continue
        path = str(item.get("source_pdf_path") or "").strip()
        if not path:
            continue
        documents.append(
            ProjectDocumentSlot(
                source_pdf_path=Path(path),
                evaluated_component=str(item.get("evaluated_component") or "Componente"),
                source_kind=str(item.get("source_kind") or "calypso"),
                template_id=item.get("template_id"),
            )
        )

    session = ProjectSession(
        client_project=str(session_raw.get("client_project") or "Projeto"),
        template_id=str(session_raw.get("template_id") or "default"),
        report_mode=session_raw.get("report_mode") or "mixed",
        documents=documents,
        active_index=int(session_raw.get("active_index") or 0),
        project_id=session_raw.get("project_id"),
        display_name=str(session_raw.get("display_name") or ""),
        unified_deleted_section_ids=list(
            session_raw.get("unified_deleted_section_ids") or []
        ),
        unified_section_overrides=dict(
            session_raw.get("unified_section_overrides") or {}
        ),
    )
    images_raw = session_raw.get("unified_images") or []
    session.unified_images = [
        image
        for item in images_raw
        if isinstance(item, dict) and (image := deserialize_report_image(item)) is not None
    ]

    workspaces: dict[str, dict[str, Any]] = {}
    histories: dict[str, list[VersionEntry]] = {}
    for item in payload.get("slots") or []:
        if not isinstance(item, dict):
            continue
        path = str(item.get("source_pdf_path") or "").strip()
        if not path:
            continue
        workspace = item.get("workspace")
        if isinstance(workspace, dict):
            workspaces[path] = workspace
        history_raw = item.get("version_history")
        if isinstance(history_raw, list):
            histories[path] = deserialize_version_history(history_raw)

    return session, workspaces, histories
