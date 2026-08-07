"""Serviço de snapshots de versão por projeto."""
from __future__ import annotations

from datetime import datetime

from src.core.application.project_snapshot_serializer import serialize_project_snapshot
from src.core.domain.project_session import ProjectSession
from src.core.domain.ports import VersionEntry, VersionSnapshotPort
from src.core.domain.version_snapshot import VersionSnapshot


class VersionSnapshotService:
    def __init__(self, repo: VersionSnapshotPort | None) -> None:
        self._repo = repo

    def next_version_number(self, project_id: str) -> int:
        snapshots = self.list_versions(project_id)
        if not snapshots:
            return 1
        return max(snapshot.version_number for snapshot in snapshots) + 1

    def create_snapshot(
        self,
        session: ProjectSession,
        responsible: str,
        description: str,
    ) -> VersionSnapshot | None:
        if self._repo is None or not session.project_id:
            return None
        version_number = self.next_version_number(session.project_id)
        created_at = datetime.now()
        snapshot = VersionSnapshot(
            project_id=session.project_id,
            version_number=version_number,
            responsible=responsible.strip(),
            description=description.strip(),
            snapshot_json=serialize_project_snapshot(session),
            created_at=created_at,
        )
        snapshot_id = self._repo.append(snapshot)
        snapshot.id = snapshot_id
        return snapshot

    def list_versions(self, project_id: str) -> list[VersionSnapshot]:
        if self._repo is None or not project_id:
            return []
        return self._repo.list_for_project(project_id)

    def get_snapshot(self, project_id: str, version_number: int) -> VersionSnapshot | None:
        for snapshot in self.list_versions(project_id):
            if snapshot.version_number == version_number:
                return snapshot
        return None

    def list_timeline_entries(self, project_id: str) -> list[VersionEntry]:
        return [
            VersionEntry(
                version_number=snapshot.version_number,
                timestamp=snapshot.created_at or datetime.now(),
                responsible_name=snapshot.responsible,
                description=snapshot.description,
            )
            for snapshot in self.list_versions(project_id)
        ]
