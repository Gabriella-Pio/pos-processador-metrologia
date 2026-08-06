"""Smoke tests for SQLite persistence (documentos, versoes, workspace_sessions)."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from src.core.domain.ports import ReportDocument, ReportImage, VersionEntry
from src.core.infrastructure.database import DatabaseManager
from src.core.infrastructure.recent_files_repository import SQLiteRecentFilesAdapter
from src.core.infrastructure.version_history_repository import SQLiteVersionHistoryAdapter
from src.core.infrastructure.workspace_session_repository import SQLiteWorkspaceSessionRepository


def test_documentos_roundtrip(db_path: Path) -> None:
    db = DatabaseManager(str(db_path))
    recent = SQLiteRecentFilesAdapter(db)
    doc = ReportDocument(
        source_pdf_path=Path("/tmp/source.pdf"),
        client_project="Cliente X",
        evaluated_component="Peça Y",
        version_history=[
            VersionEntry(1, datetime(2026, 8, 5, 12, 0, 0), "Operador", "Inicial"),
        ],
    )
    export_path = db_path.parent / "out.pdf"
    file_id = recent.save(doc, str(export_path))
    assert file_id

    listed = recent.list_recent(limit=5)
    assert len(listed) == 1
    assert listed[0]["file_name"] == "out.pdf"
    assert listed[0]["client_project"] == "Cliente X"

    by_id = recent.get_by_id(file_id)
    assert by_id is not None
    assert by_id["evaluated_component"] == "Peça Y"
    assert by_id["file_path"] == str(export_path)


def test_versoes_roundtrip(db_path: Path) -> None:
    db = DatabaseManager(str(db_path))
    versions = SQLiteVersionHistoryAdapter(db)
    source = "/tmp/calypso.pdf"
    entry = VersionEntry(1, datetime(2026, 8, 5, 10, 30, 0), "Ana", "Primeira versão")
    versions.append(source, "Proj", "Comp", entry)

    loaded = versions.list_for_document(source, "Proj", "Comp")
    assert len(loaded) == 1
    assert loaded[0].version_number == 1
    assert loaded[0].responsible_name == "Ana"
    assert loaded[0].description == "Primeira versão"


def test_workspace_sessions_roundtrip(db_path: Path) -> None:
    repo = SQLiteWorkspaceSessionRepository(str(db_path))
    img_path = db_path.parent / "foto.jpg"
    img_path.write_bytes(b"fake")
    doc = ReportDocument(
        source_pdf_path=Path("/tmp/source.pdf"),
        client_project="Cliente",
        evaluated_component="Componente",
        template_id="tomografia",
        section_overrides={"conclusao": {"texto": "OK"}},
        parsed_overrides={"operador": "João"},
        section_order=["introducao", "conclusao"],
        images=[ReportImage(image_path=img_path, section_id="identificacao")],
    )
    repo.save(doc)

    restored = ReportDocument(
        source_pdf_path=Path("/tmp/source.pdf"),
        client_project="Cliente",
        evaluated_component="Componente",
    )
    assert repo.load(restored) is True
    assert restored.template_id == "tomografia"
    assert restored.section_overrides["conclusao"]["texto"] == "OK"
    assert restored.parsed_overrides["operador"] == "João"
    assert restored.section_order == ["introducao", "conclusao"]
    assert len(restored.images) == 1
    assert restored.images[0].section_id == "identificacao"
    assert restored.images[0].image_path == img_path


def test_database_manager_creates_required_tables(db_path: Path) -> None:
    import sqlite3

    DatabaseManager(str(db_path))
    SQLiteWorkspaceSessionRepository(str(db_path))
    with sqlite3.connect(str(db_path)) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    assert "documentos" in tables
    assert "versoes" in tables
    assert "workspace_sessions" in tables
