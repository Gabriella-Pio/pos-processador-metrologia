"""
ViewModel do Workspace de edição — ponte entre a UI e o core (parser/exportador).
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from src.ui.features.workspace.document_commit import persist_session
from src.core.application.project_service import ProjectService
from src.core.application.version_snapshot_service import VersionSnapshotService
from src.core.domain.project_session import ProjectSession
from src.core.domain.ports import (
    RecentFilesRepository,
    ReportExporter,
    ReportParser,
    TemplateRepository,
    VersionHistoryRepository,
    VersionSnapshotPort,
    WorkspaceSessionPort,
)
from src.ui.features.workspace.commands.export_commands import ExportCommands
from src.ui.features.workspace.presenters.section_summary_presenter import SectionSummaryPresenter
from src.ui.features.workspace.services.document_session_service import DocumentSessionService
from src.ui.features.workspace.services.preview_service import PreviewService
from src.ui.features.workspace.services.slot_parse_worker import BackgroundSlotParseQueue
from src.ui.features.workspace.services.template_workspace_service import TemplateWorkspaceService
from src.ui.features.workspace.undo_stack import DocumentUndoStack
from src.ui.controllers.app_state import AppState
from src.ui.features.workspace.viewmodels.coordinators import (
    WorkspaceEditCoordinator,
    WorkspaceLifecycleCoordinator,
    WorkspaceMediaCoordinator,
    WorkspaceProjectCoordinator,
)
from src.ui.shared.report_editor.preview_worker import DebouncedPreviewRunner

_SESSION_SAVE_DEBOUNCE_MS = 2000


class WorkspaceViewModel(
    WorkspaceProjectCoordinator,
    WorkspaceEditCoordinator,
    WorkspaceMediaCoordinator,
    WorkspaceLifecycleCoordinator,
    QObject,
):
    document_loaded = pyqtSignal(object)
    project_loaded = pyqtSignal(object)
    project_display_name_changed = pyqtSignal(str)
    import_notice = pyqtSignal(str, str)
    export_finished = pyqtSignal(Path)
    sections_summary_ready = pyqtSignal(list)
    preview_ready = pyqtSignal(list)
    preview_metadata_ready = pyqtSignal(dict)
    preview_generating = pyqtSignal(bool)
    global_fields_ready = pyqtSignal(dict, object)
    layout_dirty_changed = pyqtSignal(bool)
    data_dirty_changed = pyqtSignal(bool)
    template_dirty_changed = pyqtSignal(bool)
    templates_list_ready = pyqtSignal(list)
    export_validation_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str, str, str)
    version_timeline_changed = pyqtSignal(list)
    version_status_changed = pyqtSignal(str)
    busy_changed = pyqtSignal(bool, str, str)
    busy_progress = pyqtSignal(int, int, str)


    def __init__(
        self,
        app_state: AppState,
        parser: ReportParser,
        exporter: ReportExporter,
        recent_files_repo: RecentFilesRepository | None = None,
        version_history_repo: VersionHistoryRepository | None = None,
        template_repo: TemplateRepository | None = None,
        session_repo: WorkspaceSessionPort | None = None,
        project_service: ProjectService | None = None,
        version_snapshot_repo: VersionSnapshotPort | None = None,
    ) -> None:
        super().__init__()
        self._app_state = app_state
        self._parser = parser
        self._exporter = exporter
        self._recent_files_repo = recent_files_repo
        self._version_history_repo = version_history_repo
        self._template_repo = template_repo
        self._session_repo = session_repo
        self._project_service = project_service
        self._snapshot_service = VersionSnapshotService(version_snapshot_repo)
        self._last_registered_version: int | None = None
        self._editing_from_version: int | None = None
        self._viewing_version: int | None = None
        self._doc_service = DocumentSessionService(parser, template_repo, version_history_repo)
        self._template_service = TemplateWorkspaceService(template_repo, exporter)
        self._presenter = SectionSummaryPresenter(exporter)
        self._preview_service = PreviewService(exporter)
        self._preview_runner = DebouncedPreviewRunner(self._preview_service, parent=self)
        self._preview_runner.set_document_getter(self._document_for_preview)
        self._preview_runner.generating.connect(self.preview_generating.emit)
        self._preview_runner.finished.connect(self._on_preview_finished)
        self._preview_runner.failed.connect(self._on_preview_failed)
        self._undo_stack = DocumentUndoStack()
        self._export_commands = ExportCommands(exporter, recent_files_repo)
        self._export_mode_unified = False

        self._session_timer = QTimer(self)
        self._session_timer.setSingleShot(True)
        self._session_timer.setInterval(_SESSION_SAVE_DEBOUNCE_MS)
        self._session_timer.timeout.connect(lambda: persist_session(self))
        self._bg_parse = BackgroundSlotParseQueue(self._doc_service, parent=self)
        self._bg_parse.slot_ready.connect(self._on_background_slot_ready)
        self._bg_parse.slot_failed.connect(self._on_background_slot_failed)
        self._bg_parse.queue_idle.connect(self._on_background_parse_idle)
        self._bg_parse_session: ProjectSession | None = None
        self._bg_parse_total = 0

