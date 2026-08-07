"""Testes do repositório de snapshots de versão."""
from __future__ import annotations

from datetime import datetime

from src.core.domain.version_snapshot import VersionSnapshot
from src.core.infrastructure.database import DatabaseManager
from src.core.infrastructure.version_snapshot_repository import SQLiteVersionSnapshotRepository


def test_version_snapshot_repository_append_and_list(tmp_path) -> None:
    db_path = tmp_path / "historico.db"
    db = DatabaseManager(str(db_path))
    repo = SQLiteVersionSnapshotRepository(db)

    snapshot_id = repo.append(
        VersionSnapshot(
            project_id="proj-abc",
            version_number=1,
            responsible="Ana",
            description="Primeira versão",
            snapshot_json='{"schema_version": 1}',
            created_at=datetime(2026, 8, 6, 12, 0),
        )
    )
    assert snapshot_id > 0

    items = repo.list_for_project("proj-abc")
    assert len(items) == 1
    assert items[0].version_number == 1
    assert items[0].description == "Primeira versão"
