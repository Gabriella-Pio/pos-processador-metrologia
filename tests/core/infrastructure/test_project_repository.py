"""Testes do repositório de projetos."""
from __future__ import annotations

from pathlib import Path

from src.core.application.project_service import ProjectService
from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession
from src.core.infrastructure.database import DatabaseManager
from src.core.infrastructure.project_repository import SQLiteProjectRepository


def test_projects_roundtrip(db_path: Path) -> None:
    db = DatabaseManager(str(db_path))
    repo = SQLiteProjectRepository(db)
    service = ProjectService(repo)

    session = ProjectSession(
        client_project="Cliente Lab",
        template_id="default",
        report_mode="mixed",
        active_index=1,
        documents=[
            ProjectDocumentSlot(
                source_pdf_path=Path("/data/a.pdf"),
                evaluated_component="Peça A",
            ),
            ProjectDocumentSlot(
                source_pdf_path=Path("/data/b.pdf"),
                evaluated_component="Peça B",
                template_id="tomografia",
                source_kind="insp_ect",
            ),
        ],
    )
    project_id = service.save_session(session)
    assert project_id

    loaded = service.load_session(project_id)
    assert loaded is not None
    assert loaded.client_project == "Cliente Lab"
    assert loaded.active_index == 1
    assert len(loaded.documents) == 2
    assert loaded.documents[1].template_id == "tomografia"

    ongoing = service.list_ongoing(limit=5)
    assert len(ongoing) == 1
    assert ongoing[0].id == project_id
    assert len(ongoing[0].slots) == 2
