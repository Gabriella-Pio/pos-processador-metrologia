"""Testes dos modelos e ViewModel da Home."""
from __future__ import annotations

from datetime import datetime

import pytest

from src.core.domain.project_workspace import ProjectSlotSnapshot, ProjectWorkspace
from src.ui.features.home.models.dashboard import (
    ProjectSummary,
    filter_projects,
    project_summary_from_workspace,
)
from src.ui.features.home.viewmodels.home_viewmodel import HomeViewModel


def _sample_workspace(**overrides) -> ProjectWorkspace:
    base = ProjectWorkspace(
        id="proj-1",
        client_project="Cargill",
        report_mode="mixed",
        template_id="default",
        slots=[
            ProjectSlotSnapshot(
                source_pdf_path="/tmp/a.pdf",
                evaluated_component="Eixo",
                source_kind="mmc",
                template_id="default",
            ),
            ProjectSlotSnapshot(
                source_pdf_path="/tmp/b.pdf",
                evaluated_component="Flange",
                source_kind="tomo",
                template_id="default",
            ),
        ],
        active_index=0,
        display_name="Lote Cargill",
        updated_at=datetime(2026, 8, 6, 15, 11),
    )
    for key, value in overrides.items():
        object.__setattr__(base, key, value)
    return base


def test_project_summary_from_workspace_batch() -> None:
    workspace = _sample_workspace()
    summary = project_summary_from_workspace(workspace)
    assert summary.project_id == "proj-1"
    assert summary.document_count == 2
    assert summary.is_batch is True
    assert summary.components == ("Eixo", "Flange")


def test_filter_projects_matches_component() -> None:
    projects = [
        ProjectSummary(
            project_id="1",
            client_project="Cargill",
            display_name="Projeto A",
            document_count=1,
            updated_at=datetime.now(),
            components=("Eixo",),
        ),
        ProjectSummary(
            project_id="2",
            client_project="Global",
            display_name="Projeto B",
            document_count=1,
            updated_at=datetime.now(),
            components=("Flange",),
        ),
    ]
    result = filter_projects(projects, "flange")
    assert len(result) == 1
    assert result[0].project_id == "2"


def test_apply_projects_filters_by_client_and_period() -> None:
    from src.ui.features.home.models.dashboard import (
        RecentFilesFilterState,
        apply_projects_filters,
    )

    now = datetime(2026, 8, 6, 12, 0)
    projects = [
        ProjectSummary(
            project_id="1",
            client_project="Cargill",
            display_name="relatorio_a",
            document_count=1,
            updated_at=datetime(2026, 8, 5),
            components=("Eixo",),
        ),
        ProjectSummary(
            project_id="2",
            client_project="Global",
            display_name="relatorio_b",
            document_count=1,
            updated_at=datetime(2026, 7, 1),
            components=("Flange",),
        ),
    ]
    state = RecentFilesFilterState(project="Cargill", period="30d")
    result = apply_projects_filters(projects, state, now=now)
    assert len(result) == 1
    assert result[0].project_id == "1"


def test_home_viewmodel_emits_ongoing_projects() -> None:
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])

    class _RecentRepo:
        def list_recent(self, limit: int = 20):
            return []

    class _TemplateRepo:
        def list_templates(self):
            return []

    class _ProjectService:
        def list_ongoing(self, limit: int = 50):
            return [_sample_workspace()]

    received: list[ProjectSummary] = []
    vm = HomeViewModel(_RecentRepo(), _TemplateRepo(), _ProjectService())
    vm.ongoing_projects_loaded.connect(received.extend)
    vm.load_dashboard()
    assert len(received) == 1
    assert received[0].display_name == "Lote Cargill"
