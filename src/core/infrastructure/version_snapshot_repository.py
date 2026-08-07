"""Adapter SQLite para snapshots de versão de projeto (Fase 4)."""
from __future__ import annotations

from datetime import datetime

from src.core.domain.version_snapshot import VersionSnapshot
from src.core.domain.ports import VersionSnapshotPort
from src.core.infrastructure.database import DatabaseManager


class SQLiteVersionSnapshotRepository(VersionSnapshotPort):
    _FORMATO_DATA = "%Y-%m-%d %H:%M:%S"

    def __init__(self, db_manager: DatabaseManager) -> None:
        self._db = db_manager

    def append(self, snapshot: VersionSnapshot) -> int:
        created = (snapshot.created_at or datetime.now()).strftime(self._FORMATO_DATA)
        with self._db._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO project_versions (
                    project_id, version_number, responsible,
                    description, snapshot_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot.project_id,
                    snapshot.version_number,
                    snapshot.responsible,
                    snapshot.description,
                    snapshot.snapshot_json,
                    created,
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def list_for_project(self, project_id: str) -> list[VersionSnapshot]:
        with self._db._conectar() as conn:
            rows = conn.execute(
                """
                SELECT id, project_id, version_number, responsible,
                       description, snapshot_json, created_at
                FROM project_versions
                WHERE project_id = ?
                ORDER BY version_number ASC
                """,
                (project_id,),
            ).fetchall()
        result: list[VersionSnapshot] = []
        for row in rows:
            result.append(
                VersionSnapshot(
                    id=int(row[0]),
                    project_id=row[1],
                    version_number=int(row[2]),
                    responsible=row[3],
                    description=row[4],
                    snapshot_json=row[5],
                    created_at=self._parse_data(row[6]),
                )
            )
        return result

    def _parse_data(self, value: str) -> datetime:
        try:
            return datetime.strptime(value, self._FORMATO_DATA)
        except (ValueError, TypeError):
            return datetime.now()
