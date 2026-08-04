"""Persistência de sessão de edição do workspace."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

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
            conn.commit()

    def save(self, document: ReportDocument) -> None:
        key = (
            str(document.source_pdf_path),
            document.client_project,
            document.evaluated_component,
        )
        images = [
            {"path": str(img.image_path), "section_id": img.section_id}
            for img in document.images
        ]
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO workspace_sessions (
                    source_pdf_path, client_project, evaluated_component,
                    template_id, section_overrides, parsed_overrides,
                    section_order, images, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(source_pdf_path, client_project, evaluated_component)
                DO UPDATE SET
                    template_id=excluded.template_id,
                    section_overrides=excluded.section_overrides,
                    parsed_overrides=excluded.parsed_overrides,
                    section_order=excluded.section_order,
                    images=excluded.images,
                    updated_at=datetime('now')
                """,
                (
                    key[0], key[1], key[2],
                    document.template_id,
                    json.dumps(document.section_overrides, ensure_ascii=False),
                    json.dumps(document.parsed_overrides, ensure_ascii=False),
                    json.dumps(document.section_order) if document.section_order else None,
                    json.dumps(images, ensure_ascii=False),
                ),
            )
            conn.commit()

    def load(self, document: ReportDocument) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT template_id, section_overrides, parsed_overrides, section_order, images
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
        return True
