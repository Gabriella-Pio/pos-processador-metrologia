"""Testes de auditoria e limpeza de armazenamento local."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from src.core.application.storage_cleanup import (
    audit_storage,
    clear_bosello_rendered_cache,
    clear_orphan_section_photos,
    clear_preview_temp,
    collect_referenced_file_paths,
    delete_stale_projects,
    format_storage_size,
    list_stale_projects,
)


def _init_db(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE projects (
                id TEXT PRIMARY KEY,
                client_project TEXT NOT NULL,
                report_mode TEXT NOT NULL DEFAULT 'mixed',
                template_id TEXT NOT NULL DEFAULT 'default',
                slots_json TEXT NOT NULL DEFAULT '[]',
                active_index INTEGER NOT NULL DEFAULT 0,
                draft_json TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT NOT NULL,
                display_name TEXT NOT NULL DEFAULT ''
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE project_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                responsible TEXT NOT NULL,
                description TEXT NOT NULL,
                snapshot_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE workspace_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_pdf_path TEXT NOT NULL,
                client_project TEXT NOT NULL,
                evaluated_component TEXT NOT NULL,
                template_id TEXT NOT NULL DEFAULT 'default',
                section_overrides TEXT NOT NULL DEFAULT '{}',
                parsed_overrides TEXT NOT NULL DEFAULT '{}',
                section_order TEXT,
                images TEXT NOT NULL DEFAULT '[]',
                bosello_captured_paths TEXT NOT NULL DEFAULT '[]',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_pdf_path, client_project, evaluated_component)
            )
            """
        )
        conn.commit()


def test_format_storage_size() -> None:
    assert format_storage_size(512) == "512 B"
    assert format_storage_size(2048) == "2.0 KB"


def test_collect_referenced_file_paths(tmp_path: Path) -> None:
    db_path = tmp_path / "historico.db"
    _init_db(db_path)
    kept = tmp_path / "kept.png"
    kept.write_bytes(b"x" * 10)
    orphan = tmp_path / "orphan.png"
    orphan.write_bytes(b"y" * 10)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO workspace_sessions (
                source_pdf_path, client_project, evaluated_component, images
            ) VALUES (?, ?, ?, ?)
            """,
            (
                str(tmp_path / "doc.pdf"),
                "Cliente",
                "Peça",
                json.dumps([{"path": str(kept)}]),
            ),
        )
        conn.commit()

    refs = collect_referenced_file_paths(db_path)
    assert kept.resolve() in refs
    assert orphan.resolve() not in refs


def test_clear_preview_temp(tmp_path: Path, monkeypatch) -> None:
    from src.core.application import storage_cleanup

    temp_dir = tmp_path / "temp"
    edited_dir = temp_dir / "edited"
    edited_dir.mkdir(parents=True)
    sample = edited_dir / "edit.png"
    sample.write_bytes(b"z" * 20)

    monkeypatch.setattr(storage_cleanup, "PREVIEW_TEMP_DIR", temp_dir)
    monkeypatch.setattr(storage_cleanup, "PREVIEW_EDIT_CACHE_DIR", edited_dir)

    freed = clear_preview_temp()
    assert freed == 20
    assert not temp_dir.exists()


def test_clear_orphan_section_photos(tmp_path: Path) -> None:
    db_path = tmp_path / "historico.db"
    _init_db(db_path)
    pdf = tmp_path / "lote" / "peca.pdf"
    pdf.parent.mkdir(parents=True)
    photo_dir = pdf.parent / ".pos-metrologia" / "section-photos"
    photo_dir.mkdir(parents=True)
    kept = photo_dir / "kept.png"
    orphan = photo_dir / "orphan.png"
    kept.write_bytes(b"a" * 8)
    orphan.write_bytes(b"b" * 12)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO projects (
                id, client_project, slots_json, updated_at, display_name
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                "p1",
                "Cliente",
                json.dumps([{"source_pdf_path": str(pdf), "evaluated_component": "Peça"}]),
                "2026-01-01 10:00:00",
                "Projeto",
            ),
        )
        conn.execute(
            """
            INSERT INTO workspace_sessions (
                source_pdf_path, client_project, evaluated_component, images
            ) VALUES (?, ?, ?, ?)
            """,
            (str(pdf), "Cliente", "Peça", json.dumps([{"path": str(kept)}])),
        )
        conn.commit()

    freed = clear_orphan_section_photos(db_path)
    assert freed == 12
    assert kept.is_file()
    assert not orphan.exists()


def test_clear_bosello_rendered_cache(tmp_path: Path) -> None:
    db_path = tmp_path / "historico.db"
    _init_db(db_path)
    pdf = tmp_path / "bosello.pdf"
    pdf.write_bytes(b"%PDF")
    cache_dir = pdf.parent / ".pos-metrologia" / "bosello-rendered" / "bosello"
    cache_dir.mkdir(parents=True)
    cached = cache_dir / "img_01.png"
    cached.write_bytes(b"c" * 16)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO projects (
                id, client_project, slots_json, updated_at, display_name
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                "p1",
                "Cliente",
                json.dumps([{"source_pdf_path": str(pdf), "evaluated_component": "Tomo"}]),
                "2026-01-01 10:00:00",
                "Tomografia",
            ),
        )
        conn.commit()

    freed = clear_bosello_rendered_cache(db_path)
    assert freed == 16
    assert not cache_dir.exists()
    assert pdf.is_file()


def test_delete_stale_projects(tmp_path: Path) -> None:
    db_path = tmp_path / "historico.db"
    _init_db(db_path)
    old_date = (datetime.now() - timedelta(days=200)).strftime("%Y-%m-%d %H:%M:%S")
    new_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO projects (
                id, client_project, slots_json, updated_at, display_name
            ) VALUES (?, ?, ?, ?, ?)
            """,
            ("old", "Cliente", "[]", old_date, "Antigo"),
        )
        conn.execute(
            """
            INSERT INTO projects (
                id, client_project, slots_json, updated_at, display_name
            ) VALUES (?, ?, ?, ?, ?)
            """,
            ("new", "Cliente", "[]", new_date, "Recente"),
        )
        conn.execute(
            """
            INSERT INTO project_versions (
                project_id, version_number, responsible, description, snapshot_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("old", 1, "Lab", "v1", "{}", old_date),
        )
        conn.commit()

    stale = list_stale_projects(db_path, months=3)
    assert len(stale) == 1
    assert stale[0].project_id == "old"

    removed = delete_stale_projects(db_path, months=3)
    assert removed == 1

    with sqlite3.connect(db_path) as conn:
        remaining = {row[0] for row in conn.execute("SELECT id FROM projects")}
        versions = conn.execute("SELECT COUNT(*) FROM project_versions").fetchone()[0]

    assert remaining == {"new"}
    assert versions == 0


def test_audit_storage_reports_categories(tmp_path: Path, monkeypatch) -> None:
    from src.core.application import storage_cleanup

    db_path = tmp_path / "historico.db"
    _init_db(db_path)
    temp_dir = tmp_path / "preview-temp"
    temp_dir.mkdir()
    (temp_dir / "frame.png").write_bytes(b"t" * 5)
    monkeypatch.setattr(storage_cleanup, "PREVIEW_TEMP_DIR", temp_dir)
    monkeypatch.setattr(storage_cleanup, "PREVIEW_EDIT_CACHE_DIR", temp_dir / "edited")

    categories = {item.key: item for item in audit_storage(db_path)}
    assert categories["preview_temp"].file_count == 1
    assert categories["preview_temp"].total_bytes == 5
    assert categories["bosello_cache"].file_count == 0
