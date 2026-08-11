"""Auditoria e limpeza segura de cache local do workspace."""
from __future__ import annotations

import json
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from src.core.application.bosello_image_import import bosello_images_storage_dir
from src.core.application.image_edit_compositor import _CACHE_DIR as PREVIEW_EDIT_CACHE_DIR
from src.core.domain.pdf_source import source_pdf_path_from_storage

DEFAULT_DB_PATH = Path("output_pdfs/historico.db")
PREVIEW_TEMP_DIR = Path("output_pdfs/temp")
DEFAULT_WORKSPACE_ROOT = Path("output_pdfs/workspace")
_PROJECT_DATE_FMT = "%Y-%m-%d %H:%M:%S"


@dataclass(frozen=True)
class StorageCategory:
    key: str
    label: str
    description: str
    file_count: int
    total_bytes: int


@dataclass(frozen=True)
class StaleProjectRow:
    project_id: str
    display_name: str
    updated_at: datetime


def format_storage_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    if num_bytes < 1024 * 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.1f} MB"
    return f"{num_bytes / (1024 * 1024 * 1024):.2f} GB"


def _dir_stats(path: Path) -> tuple[int, int]:
    if not path.exists():
        return 0, 0
    count = 0
    total = 0
    for entry in path.rglob("*"):
        if entry.is_file():
            count += 1
            try:
                total += entry.stat().st_size
            except OSError:
                continue
    return count, total


def _collect_source_pdf_paths(db_path: Path) -> set[Path]:
    paths: set[Path] = set()
    if not db_path.is_file():
        return paths

    with sqlite3.connect(db_path) as conn:
        for (slots_json,) in conn.execute("SELECT slots_json FROM projects"):
            for slot in json.loads(slots_json or "[]"):
                raw = slot.get("source_pdf_path") or ""
                pdf = source_pdf_path_from_storage(raw)
                if pdf and str(pdf).strip() not in {"", "."}:
                    paths.add(pdf)

        for (source_pdf_path,) in conn.execute(
            "SELECT DISTINCT source_pdf_path FROM workspace_sessions"
        ):
            if source_pdf_path and str(source_pdf_path).strip() not in {"", "."}:
                paths.add(Path(source_pdf_path))

    return paths


def collect_referenced_file_paths(db_path: Path | str) -> set[Path]:
    """Caminhos de fotos e capturas Bosello ainda referenciados no SQLite."""
    db = Path(db_path)
    refs: set[Path] = set()
    if not db.is_file():
        return refs

    with sqlite3.connect(db) as conn:
        rows = conn.execute(
            "SELECT images, bosello_captured_paths FROM workspace_sessions"
        ).fetchall()
    for images_json, bosello_json in rows:
        for raw in json.loads(images_json or "[]"):
            path_value = raw.get("path") if isinstance(raw, dict) else None
            if path_value:
                refs.add(Path(path_value).resolve())
        for path_value in json.loads(bosello_json or "[]"):
            if path_value:
                refs.add(Path(path_value).resolve())
    return refs


def _discover_bosello_rendered_roots(db_path: Path) -> set[Path]:
    roots: set[Path] = set()
    for pdf in _collect_source_pdf_paths(db_path):
        roots.add(bosello_images_storage_dir(pdf).parent)
    default_root = (
        DEFAULT_WORKSPACE_ROOT / ".pos-metrologia" / "bosello-rendered"
    )
    if default_root.exists():
        roots.add(default_root)
    return roots


def _discover_section_photo_dirs(db_path: Path) -> set[Path]:
    dirs: set[Path] = set()
    for pdf in _collect_source_pdf_paths(db_path):
        dirs.add(pdf.parent / ".pos-metrologia" / "section-photos")
    default_dir = DEFAULT_WORKSPACE_ROOT / ".pos-metrologia" / "section-photos"
    if default_dir.exists():
        dirs.add(default_dir)
    return dirs


def audit_storage(db_path: Path | str = DEFAULT_DB_PATH) -> list[StorageCategory]:
    db = Path(db_path)
    categories: list[StorageCategory] = []

    preview_paths = [PREVIEW_TEMP_DIR, PREVIEW_EDIT_CACHE_DIR]
    preview_count = 0
    preview_bytes = 0
    for path in preview_paths:
        count, size = _dir_stats(path)
        preview_count += count
        preview_bytes += size
    categories.append(
        StorageCategory(
            key="preview_temp",
            label="Cache de preview",
            description="Imagens temporárias geradas para preview e exportação.",
            file_count=preview_count,
            total_bytes=preview_bytes,
        )
    )

    bosello_count = 0
    bosello_bytes = 0
    for root in _discover_bosello_rendered_roots(db):
        count, size = _dir_stats(root)
        bosello_count += count
        bosello_bytes += size
    categories.append(
        StorageCategory(
            key="bosello_cache",
            label="Capturas Bosello renderizadas",
            description="Biblioteca ao lado dos PDFs de origem — pode ser recriada reimportando o Bosello.",
            file_count=bosello_count,
            total_bytes=bosello_bytes,
        )
    )

    referenced = collect_referenced_file_paths(db)
    orphan_count = 0
    orphan_bytes = 0
    section_count = 0
    section_bytes = 0
    for photo_dir in _discover_section_photo_dirs(db):
        count, size = _dir_stats(photo_dir)
        section_count += count
        section_bytes += size
        if not photo_dir.exists():
            continue
        for entry in photo_dir.iterdir():
            if not entry.is_file():
                continue
            try:
                resolved = entry.resolve()
            except OSError:
                continue
            if resolved not in referenced:
                orphan_count += 1
                try:
                    orphan_bytes += entry.stat().st_size
                except OSError:
                    continue
    categories.append(
        StorageCategory(
            key="section_photos",
            label="Fotos copiadas no workspace",
            description=(
                f"{orphan_count} arquivo(s) órfão(s) ({format_storage_size(orphan_bytes)}) "
                "sem referência nas sessões salvas."
            ),
            file_count=section_count,
            total_bytes=section_bytes,
        )
    )
    return categories


def clear_preview_temp() -> int:
    freed = 0
    for path in (PREVIEW_TEMP_DIR, PREVIEW_EDIT_CACHE_DIR):
        if not path.exists():
            continue
        _, size = _dir_stats(path)
        shutil.rmtree(path)
        freed += size
    return freed


def clear_bosello_rendered_cache(db_path: Path | str = DEFAULT_DB_PATH) -> int:
    db = Path(db_path)
    freed = 0
    for root in _discover_bosello_rendered_roots(db):
        if not root.exists():
            continue
        _, size = _dir_stats(root)
        shutil.rmtree(root)
        freed += size
    return freed


def clear_orphan_section_photos(db_path: Path | str = DEFAULT_DB_PATH) -> int:
    db = Path(db_path)
    referenced = collect_referenced_file_paths(db)
    freed = 0
    for photo_dir in _discover_section_photo_dirs(db):
        if not photo_dir.exists():
            continue
        for entry in photo_dir.iterdir():
            if not entry.is_file():
                continue
            try:
                resolved = entry.resolve()
            except OSError:
                continue
            if resolved in referenced:
                continue
            try:
                freed += entry.stat().st_size
                entry.unlink()
            except OSError:
                continue
    return freed


def _parse_project_updated_at(value: str | None) -> datetime:
    if not value:
        return datetime.min
    try:
        return datetime.strptime(value, _PROJECT_DATE_FMT)
    except ValueError:
        return datetime.min


def list_stale_projects(
    db_path: Path | str = DEFAULT_DB_PATH,
    *,
    months: int = 6,
) -> list[StaleProjectRow]:
    db = Path(db_path)
    if not db.is_file() or months <= 0:
        return []

    cutoff = datetime.now() - timedelta(days=months * 30)
    rows: list[StaleProjectRow] = []
    with sqlite3.connect(db) as conn:
        for project_id, display_name, updated_at in conn.execute(
            """
            SELECT id, display_name, updated_at
            FROM projects
            ORDER BY updated_at ASC
            """
        ):
            parsed = _parse_project_updated_at(updated_at)
            if parsed < cutoff:
                rows.append(
                    StaleProjectRow(
                        project_id=project_id,
                        display_name=display_name or project_id,
                        updated_at=parsed,
                    )
                )
    return rows


def delete_stale_projects(
    db_path: Path | str = DEFAULT_DB_PATH,
    *,
    months: int = 6,
) -> int:
    stale = list_stale_projects(db_path, months=months)
    if not stale:
        return 0

    ids = [row.project_id for row in stale]
    db = Path(db_path)
    with sqlite3.connect(db) as conn:
        for project_id in ids:
            conn.execute("DELETE FROM project_versions WHERE project_id = ?", (project_id,))
            conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
    return len(ids)
