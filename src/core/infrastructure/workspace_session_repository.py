"""Persistência SQLite do estado de edição via ``document_workspace_codec``."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from src.core.application.document_workspace_codec import (
    apply_workspace_to_document,
    serialize_document_workspace,
)
from src.core.domain.ports import ReportDocument, WorkspaceSessionPort


class SQLiteWorkspaceSessionRepository(WorkspaceSessionPort):
    def __init__(self, db_path: str = "output_pdfs/historico.db") -> None:
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workspace_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_pdf_path TEXT NOT NULL,
                    client_project TEXT NOT NULL,
                    evaluated_component TEXT NOT NULL,
                    template_id TEXT NOT NULL DEFAULT 'default',
                    section_overrides TEXT NOT NULL DEFAULT '{}',
                    parsed_overrides TEXT NOT NULL DEFAULT '{}',
                    section_order TEXT,
                    images TEXT NOT NULL DEFAULT '[]',
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source_pdf_path, client_project, evaluated_component)
                )
            """)
            self._migrate_columns(conn)
            conn.commit()

    def _migrate_columns(self, conn: sqlite3.Connection) -> None:
        cursor = conn.execute("PRAGMA table_info(workspace_sessions)")
        existing = {row[1] for row in cursor.fetchall()}
        migrations = {
            "custom_sections": "TEXT NOT NULL DEFAULT '[]'",
            "deleted_section_ids": "TEXT NOT NULL DEFAULT '[]'",
            "extra_section_ids": "TEXT NOT NULL DEFAULT '[]'",
            "attachment_pdf_paths": "TEXT NOT NULL DEFAULT '[]'",
            "bosello_captured_paths": "TEXT NOT NULL DEFAULT '[]'",
        }
        for column, definition in migrations.items():
            if column not in existing:
                conn.execute(
                    f"ALTER TABLE workspace_sessions ADD COLUMN {column} {definition}"
                )

    def save(self, document: ReportDocument) -> None:
        payload = serialize_document_workspace(document)
        key = (
            str(document.source_pdf_path),
            document.client_project,
            document.evaluated_component,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO workspace_sessions (
                    source_pdf_path, client_project, evaluated_component,
                    template_id, section_overrides, parsed_overrides,
                    section_order, images, custom_sections, deleted_section_ids,
                    extra_section_ids, attachment_pdf_paths, bosello_captured_paths, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(source_pdf_path, client_project, evaluated_component)
                DO UPDATE SET
                    template_id=excluded.template_id,
                    section_overrides=excluded.section_overrides,
                    parsed_overrides=excluded.parsed_overrides,
                    section_order=excluded.section_order,
                    images=excluded.images,
                    custom_sections=excluded.custom_sections,
                    deleted_section_ids=excluded.deleted_section_ids,
                    extra_section_ids=excluded.extra_section_ids,
                    attachment_pdf_paths=excluded.attachment_pdf_paths,
                    bosello_captured_paths=excluded.bosello_captured_paths,
                    updated_at=datetime('now')
                """,
                (
                    key[0],
                    key[1],
                    key[2],
                    payload.get("template_id") or "default",
                    json.dumps(payload.get("section_overrides") or {}, ensure_ascii=False),
                    json.dumps(payload.get("parsed_overrides") or {}, ensure_ascii=False),
                    (
                        json.dumps(payload["section_order"])
                        if payload.get("section_order")
                        else None
                    ),
                    json.dumps(payload.get("images") or [], ensure_ascii=False),
                    json.dumps(payload.get("custom_sections") or [], ensure_ascii=False),
                    json.dumps(payload.get("deleted_section_ids") or [], ensure_ascii=False),
                    json.dumps(payload.get("extra_section_ids") or [], ensure_ascii=False),
                    json.dumps(payload.get("attachment_pdf_paths") or [], ensure_ascii=False),
                    json.dumps(payload.get("bosello_captured_paths") or [], ensure_ascii=False),
                ),
            )
            conn.commit()

    def load(self, document: ReportDocument) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT template_id, section_overrides, parsed_overrides, section_order,
                       images, custom_sections, deleted_section_ids, attachment_pdf_paths,
                       bosello_captured_paths, extra_section_ids
                FROM workspace_sessions
                WHERE source_pdf_path=? AND client_project=? AND evaluated_component=?
                """,
                (
                    str(document.source_pdf_path),
                    document.client_project,
                    document.evaluated_component,
                ),
            ).fetchone()
        if row is None:
            return False
        order_raw = row[3]
        workspace = {
            "template_id": row[0],
            "section_overrides": json.loads(row[1] or "{}"),
            "parsed_overrides": json.loads(row[2] or "{}"),
            "section_order": json.loads(order_raw) if order_raw else None,
            "images": json.loads(row[4] or "[]"),
            "custom_sections": json.loads(row[5] or "[]"),
            "deleted_section_ids": json.loads(row[6] or "[]"),
            "attachment_pdf_paths": json.loads(row[7] or "[]"),
            "bosello_captured_paths": json.loads(row[8] or "[]") if len(row) > 8 else [],
            "extra_section_ids": json.loads(row[9] or "[]") if len(row) > 9 else [],
        }
        apply_workspace_to_document(document, workspace)
        return True
