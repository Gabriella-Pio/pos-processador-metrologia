"""Testes do serviço de snapshots de versão."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.core.application.version_snapshot_service import VersionSnapshotService
from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession
from src.core.domain.ports import ReportDocument
from src.core.domain.version_snapshot import VersionSnapshot


class _SnapshotRepoStub:
    def __init__(self) -> None:
        self._items: list[VersionSnapshot] = []
        self._next_id = 1

    def append(self, snapshot: VersionSnapshot) -> int:
        snapshot_id = self._next_id
        self._next_id += 1
        self._items.append(
            VersionSnapshot(
                id=snapshot_id,
                project_id=snapshot.project_id,
                version_number=snapshot.version_number,
                responsible=snapshot.responsible,
                description=snapshot.description,
                snapshot_json=snapshot.snapshot_json,
                created_at=snapshot.created_at,
            )
        )
        return snapshot_id

    def list_for_project(self, project_id: str) -> list[VersionSnapshot]:
        return [item for item in self._items if item.project_id == project_id]


def _session_with_document() -> ProjectSession:
    document = ReportDocument(
        source_pdf_path=Path("/data/a.pdf"),
        client_project="Cargill",
        evaluated_component="Eixo",
    )
    return ProjectSession(
        client_project="Cargill",
        project_id="proj-1",
        display_name="relatorio_a",
        documents=[
            ProjectDocumentSlot(
                source_pdf_path=Path("/data/a.pdf"),
                evaluated_component="Eixo",
                document=document,
            )
        ],
    )


def test_create_and_list_snapshots() -> None:
    repo = _SnapshotRepoStub()
    service = VersionSnapshotService(repo)
    session = _session_with_document()

    first = service.create_snapshot(session, "Ana", "v1")
    assert first is not None
    assert first.version_number == 1
    assert first.id == 1

    second = service.create_snapshot(session, "Bruno", "v2")
    assert second is not None
    assert second.version_number == 2

    timeline = service.list_timeline_entries("proj-1")
    assert len(timeline) == 2
    assert timeline[0].version_number == 1
    assert timeline[1].responsible_name == "Bruno"

    loaded = service.get_snapshot("proj-1", 1)
    assert loaded is not None
    assert "relatorio_a" in loaded.snapshot_json
