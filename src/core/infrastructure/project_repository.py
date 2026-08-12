"""Adapter SQLite para projetos em edição."""
from __future__ import annotations

import json
from datetime import datetime

from src.core.application.project_serializer import slots_from_json, slots_to_json
from src.core.domain.project_workspace import ProjectWorkspace
from src.core.domain.ports import ProjectRepositoryPort
from src.core.infrastructure.database import DatabaseManager


class SQLiteProjectRepository(ProjectRepositoryPort):
    _FORMATO_DATA = "%Y-%m-%d %H:%M:%S"

    def __init__(self, db_manager: DatabaseManager) -> None:
        self._db = db_manager

    def save(self, workspace: ProjectWorkspace) -> None:
        now = (workspace.updated_at or datetime.now()).strftime(self._FORMATO_DATA)
        slots_json = json.dumps(slots_to_json(workspace.slots), ensure_ascii=False)
        draft_json = json.dumps(workspace.draft or {}, ensure_ascii=False)
        with self._db._conectar() as conn:
            conn.execute(
                """
                INSERT INTO projects (
                    id, client_project, report_mode, template_id,
                    slots_json, active_index, draft_json, updated_at, display_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    client_project=excluded.client_project,
                    report_mode=excluded.report_mode,
                    template_id=excluded.template_id,
                    slots_json=excluded.slots_json,
                    active_index=excluded.active_index,
                    draft_json=excluded.draft_json,
                    updated_at=excluded.updated_at,
                    display_name=excluded.display_name
                """,
                (
                    workspace.id,
                    workspace.client_project,
                    workspace.report_mode,
                    workspace.template_id,
                    slots_json,
                    workspace.active_index,
                    draft_json,
                    now,
                    workspace.display_name or workspace.client_project,
                ),
            )
            conn.commit()

    def get(self, project_id: str) -> ProjectWorkspace | None:
        with self._db._conectar() as conn:
            row = conn.execute(
                """
                SELECT id, client_project, report_mode, template_id,
                       slots_json, active_index, updated_at, display_name, draft_json
                FROM projects WHERE id = ?
                """,
                (project_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_workspace(row)

    def list_recent(self, limit: int = 50) -> list[ProjectWorkspace]:
        with self._db._conectar() as conn:
            rows = conn.execute(
                """
                SELECT id, client_project, report_mode, template_id,
                       slots_json, active_index, updated_at, display_name, draft_json
                FROM projects ORDER BY updated_at DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_workspace(row) for row in rows]

    def _row_to_workspace(self, row: tuple) -> ProjectWorkspace:
        slots_raw = json.loads(row[4] or "[]")
        updated = self._parse_data(row[6]) if row[6] else None
        draft_raw = row[8] if len(row) > 8 else "{}"
        try:
            draft = json.loads(draft_raw or "{}")
        except (TypeError, json.JSONDecodeError):
            draft = {}
        if not isinstance(draft, dict):
            draft = {}
        return ProjectWorkspace(
            id=row[0],
            client_project=row[1],
            report_mode=row[2] or "mixed",
            template_id=row[3] or "default",
            slots=slots_from_json(slots_raw),
            active_index=int(row[5] or 0),
            display_name=row[7] or row[1],
            updated_at=updated,
            draft=draft,
        )

    def _parse_data(self, value: str) -> datetime:
        try:
            return datetime.strptime(value, self._FORMATO_DATA)
        except (ValueError, TypeError):
            return datetime.now()
