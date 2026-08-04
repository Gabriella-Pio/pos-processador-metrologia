"""Persistência de sessão de edição."""
from __future__ import annotations

from src.core.domain.ports import ReportDocument, WorkspaceSessionPort


def save_workspace_session(repo: WorkspaceSessionPort, document: ReportDocument) -> None:
    repo.save(document)


def load_workspace_session(repo: WorkspaceSessionPort, document: ReportDocument) -> bool:
    return repo.load(document)
