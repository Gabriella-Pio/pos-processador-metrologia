"""Persistência de sessão de edição do workspace."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from src.core.domain.ports import ReportDocument, ReportImage, WorkspaceSessionPort


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
            "attachment_pdf_paths": "TEXT NOT NULL DEFAULT '[]'",
            "bosello_captured_paths": "TEXT NOT NULL DEFAULT '[]'",
        }
        for column, definition in migrations.items():
            if column not in existing:
                conn.execute(
                    f"ALTER TABLE workspace_sessions ADD COLUMN {column} {definition}"
                )

    def save(self, document: ReportDocument) -> None:
        key = (
            str(document.source_pdf_path),
            document.client_project,
            document.evaluated_component,
        )
        images = [
            {
                "path": str(img.image_path),
                "section_id": img.section_id,
                "caption": img.caption or "",
                "bosello_import": bool(img.bosello_import),
            }
            for img in document.images
        ]
        attachment_paths = [str(path) for path in document.attachment_pdf_paths]
        bosello_paths = [str(path) for path in document.bosello_captured_paths]
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO workspace_sessions (
                    source_pdf_path, client_project, evaluated_component,
                    template_id, section_overrides, parsed_overrides,
                    section_order, images, custom_sections, deleted_section_ids,
                    attachment_pdf_paths, bosello_captured_paths, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(source_pdf_path, client_project, evaluated_component)
                DO UPDATE SET
                    template_id=excluded.template_id,
                    section_overrides=excluded.section_overrides,
                    parsed_overrides=excluded.parsed_overrides,
                    section_order=excluded.section_order,
                    images=excluded.images,
                    custom_sections=excluded.custom_sections,
                    deleted_section_ids=excluded.deleted_section_ids,
                    attachment_pdf_paths=excluded.attachment_pdf_paths,
                    bosello_captured_paths=excluded.bosello_captured_paths,
                    updated_at=datetime('now')
                """,
                (
                    key[0], key[1], key[2],
                    document.template_id,
                    json.dumps(document.section_overrides, ensure_ascii=False),
                    json.dumps(document.parsed_overrides, ensure_ascii=False),
                    json.dumps(document.section_order) if document.section_order else None,
                    json.dumps(images, ensure_ascii=False),
                    json.dumps(document.custom_sections, ensure_ascii=False),
                    json.dumps(document.deleted_section_ids, ensure_ascii=False),
                    json.dumps(attachment_paths, ensure_ascii=False),
                    json.dumps(bosello_paths, ensure_ascii=False),
                ),
            )
            conn.commit()

    def load(self, document: ReportDocument) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT template_id, section_overrides, parsed_overrides, section_order,
                       images, custom_sections, deleted_section_ids, attachment_pdf_paths,
                       bosello_captured_paths
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
        document.template_id = row[0]
        document.section_overrides = json.loads(row[1] or "{}")
        document.parsed_overrides = json.loads(row[2] or "{}")
        order_raw = row[3]
        document.section_order = json.loads(order_raw) if order_raw else None
        images_raw = json.loads(row[4] or "[]")
        document.images = [
            ReportImage(
                image_path=Path(item["path"]),
                section_id=item["section_id"],
                caption=str(item.get("caption") or ""),
                bosello_import=bool(item.get("bosello_import")),
            )
            for item in images_raw
            if item.get("path") and item.get("section_id")
        ]
        document.custom_sections = json.loads(row[5] or "[]")
        document.deleted_section_ids = json.loads(row[6] or "[]")
        attachment_raw = json.loads(row[7] or "[]")
        document.attachment_pdf_paths = [Path(path) for path in attachment_raw if path]
        bosello_raw = json.loads(row[8] or "[]") if len(row) > 8 else []
        document.bosello_captured_paths = [Path(path) for path in bosello_raw if path]
        return True
