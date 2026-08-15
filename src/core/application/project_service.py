"""Serviço de persistência de projetos multi-PDF."""
from __future__ import annotations

import uuid

from src.core.application.project_serializer import session_to_workspace, workspace_to_session
from src.core.domain.project_session import ProjectSession
from src.core.domain.project_workspace import ProjectWorkspace
from src.core.domain.ports import ProjectRepositoryPort


class ProjectService:
    def __init__(self, project_repo: ProjectRepositoryPort | None) -> None:
        self._repo = project_repo

    def save_session(self, session: ProjectSession) -> str | None:
        if self._repo is None:
            return session.project_id
        if not session.project_id:
            session.project_id = str(uuid.uuid4())
        workspace = session_to_workspace(session)
        self._repo.save(workspace)
        return session.project_id

    def load_metadata(self, project_id: str) -> ProjectWorkspace | None:
        if self._repo is None:
            return None
        return self._repo.get(project_id)

    def load_session(self, project_id: str) -> ProjectSession | None:
        workspace = self.load_metadata(project_id)
        if workspace is None:
            return None
        return workspace_to_session(workspace)

    def list_ongoing(self, limit: int = 50) -> list[ProjectWorkspace]:
        if self._repo is None:
            return []
        return self._repo.list_recent(limit)

    def rename(self, project_id: str, display_name: str) -> bool:
        if self._repo is None:
            return False
        workspace = self._repo.get(project_id)
        if workspace is None:
            return False
        cleaned = display_name.strip()
        if not cleaned:
            return False
        workspace.display_name = cleaned
        self._repo.save(workspace)
        return True

    def delete(self, project_id: str) -> bool:
        if self._repo is None:
            return False
        return self._repo.delete(project_id)

    def delete_many(self, project_ids: list[str]) -> int:
        if self._repo is None:
            return 0
        removed = 0
        for project_id in project_ids:
            if self._repo.delete(project_id):
                removed += 1
        return removed
