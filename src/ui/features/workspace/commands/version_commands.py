"""Comandos de histórico de versões do documento."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from src.core.application.project_snapshot_serializer import (
    apply_workspace_to_document,
    deserialize_project_snapshot,
)
from src.core.application.version_snapshot_service import VersionSnapshotService
from src.core.domain.project_session import ProjectSession
from src.core.domain.ports import ReportDocument, VersionEntry
from src.ui.features.workspace.services.document_session_service import DocumentSessionService


class VersionCommands:
    @staticmethod
    def create_entry(
        document: ReportDocument,
        responsible_name: str,
        description: str,
    ) -> VersionEntry:
        existing = document.version_history
        next_number = max((entry.version_number for entry in existing), default=0) + 1
        return VersionEntry(
            version_number=next_number,
            timestamp=datetime.now(),
            responsible_name=responsible_name,
            description=description,
        )

    @staticmethod
    def document_from_snapshot(
        snapshot_service: VersionSnapshotService,
        doc_service: DocumentSessionService,
        session: ProjectSession,
        version_number: int,
    ) -> ReportDocument | None:
        """Hidrata o documento da aba ativa a partir de um snapshot de projeto."""
        if not session.project_id:
            return None
        snapshot = snapshot_service.get_snapshot(session.project_id, version_number)
        if snapshot is None:
            return None
        try:
            restored, workspaces, histories = deserialize_project_snapshot(
                snapshot.snapshot_json
            )
        except (ValueError, TypeError):
            return None
        if not restored.documents:
            return None
        index = min(max(session.active_index, 0), len(restored.documents) - 1)
        if not doc_service.parse_slot(restored, index)[0]:
            return None
        slot = restored.documents[index]
        document = slot.document
        if document is None:
            return None
        key = str(slot.source_pdf_path)
        if key in workspaces:
            apply_workspace_to_document(document, workspaces[key])
        if key in histories:
            document.version_history = histories[key]
        return document

    @staticmethod
    def apply_snapshot_workspaces(
        session: ProjectSession,
        workspaces: dict[str, dict[str, Any]],
        histories: dict[str, list[VersionEntry]],
        *,
        session_repo=None,
    ) -> None:
        """Aplica workspace/histórico já parseados em cada slot (UI thread)."""
        for slot in session.documents:
            document = slot.document
            if document is None:
                continue
            key = str(slot.source_pdf_path)
            if key in workspaces:
                apply_workspace_to_document(document, workspaces[key])
            if key in histories:
                document.version_history = histories[key]
            if session_repo is not None:
                session_repo.save(document)
