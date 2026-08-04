"""Composition root — wiring de dependências da aplicação."""
from __future__ import annotations

from src.core.infrastructure.adapters import RealReportExporterAdapter, RealReportParserAdapter
from src.core.infrastructure.database import DatabaseManager
from src.core.infrastructure.recent_files_repository import SQLiteRecentFilesAdapter
from src.core.infrastructure.template_repository import JSONTemplateRepository
from src.core.infrastructure.version_history_repository import SQLiteVersionHistoryAdapter
from src.ui.main_window import MainWindow


def create_main_window() -> MainWindow:
    db_manager = DatabaseManager()
    recent_files_repo = SQLiteRecentFilesAdapter(db_manager)
    version_history_repo = SQLiteVersionHistoryAdapter(db_manager)
    template_repo = JSONTemplateRepository()
    report_parser = RealReportParserAdapter()
    report_exporter = RealReportExporterAdapter(template_repository=template_repo)
    return MainWindow(
        report_parser=report_parser,
        report_exporter=report_exporter,
        recent_files_repo=recent_files_repo,
        template_repo=template_repo,
        version_history_repo=version_history_repo,
    )
