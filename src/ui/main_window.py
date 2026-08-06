"""
Janela principal: coordena navegação Home ↔ Workspace ↔ Template Editor.
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QDialog, QMainWindow, QStackedWidget, QVBoxLayout, QWidget

from src.core.application.project_service import ProjectService
from src.core.domain.ports import (
    RecentFilesRepository,
    ReportExporter,
    ReportParser,
    TemplateRepository,
    VersionHistoryRepository,
    WorkspaceSessionPort,
)
from src.ui.accessibility import AppearanceManager
from src.ui.components.feedback import confirm_action, show_friendly_error
from src.ui.components.header import AppHeader
from src.ui.components.modal_overlay import ModalOverlay
from src.ui.dialogs.help_accessibility_dialog import HelpAccessibilityDialog
from src.ui.features.home.dialogs.project_setup_dialog import ProjectSetupDialog
from src.ui.styles import base_stylesheet
from src.ui.controllers.app_state import AppState
from src.ui.features.home.viewmodels.home_viewmodel import HomeViewModel
from src.ui.controllers.navigation_controller import NavigationController
from src.ui.features.workspace.viewmodels.workspace_viewmodel import WorkspaceViewModel
from src.ui.features.templates.viewmodels.template_editor_viewmodel import TemplateEditorViewModel
from src.ui.features.home.components.home_view import HomeView
from src.ui.features.templates.components.template_editor_view import TemplateEditorView
from src.ui.features.workspace.components.workspace_view import WorkspaceView


class MainWindow(QMainWindow):
    def __init__(
        self,
        report_parser: ReportParser,
        report_exporter: ReportExporter,
        recent_files_repo: RecentFilesRepository,
        template_repo: TemplateRepository,
        version_history_repo: VersionHistoryRepository | None = None,
        workspace_session_repo: WorkspaceSessionPort | None = None,
        project_service: ProjectService | None = None,
        version_snapshot_repo=None,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Pós-processamento de Relatórios de Metrologia — SENAI × ZEISS")
        self.setMinimumSize(960, 600)
        self.setStyleSheet(base_stylesheet())

        self._parser = report_parser
        self._template_repo = template_repo
        self._app_state = AppState()

        self._home_vm = HomeViewModel(recent_files_repo, template_repo)
        self._workspace_vm = WorkspaceViewModel(
            self._app_state,
            report_parser,
            report_exporter,
            recent_files_repo,
            version_history_repo,
            template_repo,
            workspace_session_repo,
            project_service,
        )
        self._template_editor_vm = TemplateEditorViewModel(template_repo, report_exporter)
        self._nav_controller = NavigationController()
        self._project_setup_dialog: ProjectSetupDialog | None = None

        central_widget = QWidget()
        central_widget.setObjectName("MainCentral")
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._header = AppHeader(parent=self)
        main_layout.addWidget(self._header)

        self._stack = QStackedWidget()
        self._stack.setObjectName("MainViewStack")
        self._home_view = HomeView(self._home_vm)
        self._workspace_view = WorkspaceView(self._app_state, self._workspace_vm)
        self._template_editor_view = TemplateEditorView(self._template_editor_vm)
        self._stack.addWidget(self._home_view)
        self._stack.addWidget(self._workspace_view)
        self._stack.addWidget(self._template_editor_view)
        main_layout.addWidget(self._stack)
        self.setCentralWidget(central_widget)

        self._connect_signals()
        self._setup_shortcuts()
        AppearanceManager.instance().register_refresh(self._refresh_appearance)
        self._nav_controller.navigate_to(0)

    def _connect_signals(self) -> None:
        self._header.back_requested.connect(self._nav_controller.back)
        self._header.forward_requested.connect(self._nav_controller.forward)
        self._header.home_requested.connect(self._go_home)
        self._header.help_requested.connect(self._open_help)
        self._nav_controller.changed.connect(self._on_navigation_changed)

        self._home_view.new_document_requested.connect(self._open_project_setup)
        self._home_view.template_editor_requested.connect(self._open_template_editor)
        self._home_view.recent_file_opened.connect(self._open_recent_file)
        self._template_editor_view.saved.connect(lambda _tid: self._home_vm.load_dashboard())
        self._template_editor_vm.template_name_changed.connect(self._on_template_name_changed)

    def _setup_shortcuts(self) -> None:
        back = QShortcut(QKeySequence("Alt+Left"), self)
        back.setContext(Qt.ShortcutContext.ApplicationShortcut)
        back.activated.connect(self._nav_controller.back)

        forward = QShortcut(QKeySequence("Alt+Right"), self)
        forward.setContext(Qt.ShortcutContext.ApplicationShortcut)
        forward.activated.connect(self._nav_controller.forward)

        fullscreen = QShortcut(QKeySequence("F11"), self)
        fullscreen.setContext(Qt.ShortcutContext.ApplicationShortcut)
        fullscreen.activated.connect(self._toggle_fullscreen)

        help_shortcut = QShortcut(QKeySequence("F1"), self)
        help_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        help_shortcut.activated.connect(self._open_help)

        new_report = QShortcut(QKeySequence("Ctrl+N"), self)
        new_report.setContext(Qt.ShortcutContext.ApplicationShortcut)
        new_report.activated.connect(self._open_project_setup)

        new_template = QShortcut(QKeySequence("Ctrl+T"), self)
        new_template.setContext(Qt.ShortcutContext.ApplicationShortcut)
        new_template.activated.connect(lambda: self._open_template_editor("new"))

        focus_search = QShortcut(QKeySequence("Ctrl+K"), self)
        focus_search.setContext(Qt.ShortcutContext.ApplicationShortcut)
        focus_search.activated.connect(self._home_view.focus_search)

        clear_search = QShortcut(QKeySequence("Escape"), self)
        clear_search.setContext(Qt.ShortcutContext.ApplicationShortcut)
        clear_search.activated.connect(self._home_view.clear_search_and_filters)

    def _open_help(self) -> None:
        HelpAccessibilityDialog(self).exec()

    def _refresh_appearance(self) -> None:
        self.setStyleSheet(base_stylesheet())
        self._header.refresh_appearance()
        self._home_view.refresh_appearance()
        self._workspace_view.refresh_appearance()
        self._template_editor_view.refresh_appearance()

    def _toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showMaximized()
        else:
            self.showFullScreen()

    def _go_home(self) -> None:
        if self._stack.currentIndex() == 2 and self._template_editor_vm.is_dirty():
            if not confirm_action(
                self,
                "Sair do editor?",
                "Há alterações não salvas no template.",
            ):
                return
        self._nav_controller.navigate_to(0)

    def _on_navigation_changed(self, index: int, can_back: bool, can_forward: bool) -> None:
        self._stack.setCurrentIndex(index)
        self._header.set_navigation_state(can_back, can_forward)

        if index == 0:
            self._header.set_breadcrumb([("Início", None)])
            self._header.set_badge_text("Pós-processador de Relatórios")
            self._home_vm.load_dashboard()
        elif index == 1:
            doc = self._app_state.active_document
            comp_name = doc.evaluated_component if doc else "Workspace de Análise"
            session = self._app_state.project_session
            project_name = session.client_project if session else comp_name

            self._header.set_breadcrumb([
                ("Início", self._go_home),
                ("Workspace", None),
                (comp_name, None),
            ])
            self._header.set_badge_text(project_name)
        elif index == 2:
            name = self._template_editor_vm.template_name or "Template"
            self._header.set_breadcrumb([
                ("Início", self._go_home),
                ("Templates", None),
                (name, None),
            ])
            self._header.set_badge_text("Editor de templates")

    def _on_template_name_changed(self, name: str) -> None:
        if self._stack.currentIndex() != 2:
            return
        display = name.strip() or "Template"
        self._header.set_breadcrumb([
            ("Início", self._go_home),
            ("Templates", None),
            (display, None),
        ])

    def _open_project_setup(self) -> None:
        if self._project_setup_dialog is not None:
            self._project_setup_dialog.raise_()
            self._project_setup_dialog.activateWindow()
            return

        dialog = ProjectSetupDialog(self._parser, self._template_repo, parent=self)
        host = self.centralWidget() or self
        overlay = ModalOverlay(host, dialog)
        dialog.set_overlay(overlay)

        def on_finished(result: int) -> None:
            overlay.deleteLater()
            self._project_setup_dialog = None
            if result != QDialog.DialogCode.Accepted:
                return
            data = dialog.get_result()
            entries = data["pdf_entries"]
            if not entries:
                return
            self._workspace_vm.load_project(
                data["client_project"],
                entries,
                template_id=data["template_id"],
                report_mode=data.get("report_mode", "auto"),
            )
            self._nav_controller.navigate_to(1)

        self._project_setup_dialog = dialog
        overlay.show()
        overlay.raise_()
        dialog.finished.connect(on_finished)
        dialog.setWindowModality(Qt.WindowModality.NonModal)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _open_template_editor(self, template_id: str) -> None:
        if self._stack.currentIndex() == 2 and self._template_editor_vm.is_dirty():
            if not confirm_action(
                self,
                "Abrir outro template?",
                "Há alterações não salvas no template atual.",
            ):
                return
        self._template_editor_view.load_template(template_id)
        self._nav_controller.navigate_to(2)

    def _open_recent_file(self, file_id: str) -> None:
        try:
            self._workspace_vm.load_from_recent(file_id)
            self._nav_controller.navigate_to(1)
        except Exception as exc:
            show_friendly_error(
                self,
                "Erro ao abrir arquivo recente",
                "Não foi possível carregar os dados históricos deste relatório.",
                str(exc),
            )
