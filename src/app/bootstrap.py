"""Composition root — wiring de dependências da aplicação."""
from __future__ import annotations

from src.core.infrastructure.database import DatabaseManager
from src.core.infrastructure.project_repository import SQLiteProjectRepository
from src.core.infrastructure.recent_files_repository import SQLiteRecentFilesAdapter
from src.core.infrastructure.template_repository import JSONTemplateRepository
from src.core.infrastructure.version_history_repository import SQLiteVersionHistoryAdapter
from src.core.infrastructure.version_snapshot_repository import SQLiteVersionSnapshotRepository
from src.core.infrastructure.workspace_session_repository import SQLiteWorkspaceSessionRepository
from src.core.application.project_service import ProjectService
from src.ui.main_window import MainWindow


def create_main_window() -> MainWindow:
    # Adapters (parser/ReportLab) importados aqui — não no topo — para o módulo
    # bootstrap não puxar fitz/ReportLab antes da MainWindow existir.
    from src.core.infrastructure.adapters import RealReportExporterAdapter, RealReportParserAdapter

    db_manager = DatabaseManager()
    recent_files_repo = SQLiteRecentFilesAdapter(db_manager)
    version_history_repo = SQLiteVersionHistoryAdapter(db_manager)
    project_repo = SQLiteProjectRepository(db_manager)
    project_service = ProjectService(project_repo)
    version_snapshot_repo = SQLiteVersionSnapshotRepository(db_manager)
    workspace_session_repo = SQLiteWorkspaceSessionRepository()
    template_repo = JSONTemplateRepository()
    report_parser = RealReportParserAdapter()
    report_exporter = RealReportExporterAdapter(template_repository=template_repo)
    return MainWindow(
        report_parser=report_parser,
        report_exporter=report_exporter,
        recent_files_repo=recent_files_repo,
        template_repo=template_repo,
        version_history_repo=version_history_repo,
        workspace_session_repo=workspace_session_repo,
        project_service=project_service,
        version_snapshot_repo=version_snapshot_repo,
    )
