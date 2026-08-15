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

    assert service.rename(project_id, "Novo nome")
    renamed = service.load_metadata(project_id)
    assert renamed is not None
    assert renamed.display_name == "Novo nome"

    assert service.delete(project_id)
    assert service.load_session(project_id) is None
    assert service.list_ongoing() == []


def test_delete_many_projects(db_path: Path) -> None:
    db = DatabaseManager(str(db_path))
    service = ProjectService(SQLiteProjectRepository(db))
    ids = []
    for name in ("A", "B", "C"):
        pid = service.save_session(
            ProjectSession(
                client_project=name,
                template_id="default",
                report_mode="mmc",
                documents=[
                    ProjectDocumentSlot(
                        source_pdf_path=Path(f"/data/{name}.pdf"),
                        evaluated_component=name,
                    )
                ],
            )
        )
        ids.append(pid)
    assert service.delete_many([ids[0], ids[2]]) == 2
    remaining = service.list_ongoing()
    assert len(remaining) == 1
    assert remaining[0].id == ids[1]
