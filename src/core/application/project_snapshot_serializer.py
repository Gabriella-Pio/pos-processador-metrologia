"""Serialização de snapshot completo de projeto (schema v1)."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from src.core.application.document_workspace_codec import (
    apply_workspace_to_document,
    serialize_document_workspace,
)
from src.core.application.project_serializer import apply_draft_to_session, serialize_session_draft
from src.core.application.slot_meta_codec import document_slot_from_meta, document_slot_to_meta
from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession
from src.core.domain.ports import ReportDocument, VersionEntry

SCHEMA_VERSION = 1

# Reexport — call sites e testes importam daqui.
__all__ = [
    "SCHEMA_VERSION",
    "apply_workspace_to_document",
    "deserialize_project_snapshot",
    "deserialize_version_history",
    "serialize_document_workspace",
    "serialize_project_snapshot",
    "serialize_version_history",
]


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
    draft = serialize_session_draft(session)
    session_payload: dict[str, Any] = {
        "project_id": session.project_id,
        "display_name": session.display_name,
        "client_project": session.client_project,
        "template_id": session.template_id,
        "report_mode": session.report_mode,
        "active_index": session.active_index,
        **draft,
        # Chaves de workspace usam str(Path) — não storage — para casar com restore.
        "slots": [document_slot_to_meta(slot, storage_path=False) for slot in session.documents],
    }
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "session": session_payload,
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
    documents: list[ProjectDocumentSlot] = []
    for item in session_raw.get("slots") or []:
        slot = document_slot_from_meta(item, storage_path=False)
        if slot is not None:
            documents.append(slot)

    session = ProjectSession(
        client_project=str(session_raw.get("client_project") or "Projeto"),
        template_id=str(session_raw.get("template_id") or "default"),
        report_mode=session_raw.get("report_mode") or "mixed",
        documents=documents,
        active_index=int(session_raw.get("active_index") or 0),
        project_id=session_raw.get("project_id"),
        display_name=str(session_raw.get("display_name") or ""),
    )
    apply_draft_to_session(session, session_raw)

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
