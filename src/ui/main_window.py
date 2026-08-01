"""
Janela principal: coordena a navegação entre Dashboard e Workspace
(via ``QStackedWidget``) e monta a árvore de injeção de dependências
da camada de UI.

Esta classe é o único ponto onde implementações concretas do ``core``
(parser real, exportador ReportLab, repositórios SQLite/JSON) são
conectadas às interfaces (``ports``) usadas pelos ViewModels — as views
e ViewModels em si nunca importam essas implementações diretamente.
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QMainWindow, QStackedWidget

from src.core.ports import (
    RecentFilesRepository,
    ReportExporter,
    ReportParser,
    TemplateRepository,
)
from src.ui.dialogs.import_dialog import ImportDialog
from src.ui.styles import base_stylesheet
from src.ui.viewmodels.app_state import AppState
from src.ui.viewmodels.home_viewmodel import HomeViewModel
from src.ui.viewmodels.workspace_viewmodel import WorkspaceViewModel
from src.ui.views.home_view import HomeView
from src.ui.views.template_view import TemplateView
from src.ui.views.workspace_view import WorkspaceView


class MainWindow(QMainWindow):
    """Janela principal da aplicação.

    Dependências concretas do ``core`` (parser, exportador, repositórios)
    são recebidas prontas via injeção — este arquivo apenas as conecta
    às portas esperadas pelos ViewModels, sem conhecer os detalhes de
    parsing de PDF ou geração via ReportLab.
    """

    def __init__(
        self,
        report_parser: ReportParser,
        report_exporter: ReportExporter,
        recent_files_repo: RecentFilesRepository,
        template_repo: TemplateRepository,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Pós-processamento de Relatórios de Metrologia — SENAI × ZEISS")
        self.resize(1280, 800)
        self.setStyleSheet(base_stylesheet())

        self._template_repo = template_repo
        self._app_state = AppState()

        self._home_vm = HomeViewModel(recent_files_repo, template_repo)
        self._workspace_vm = WorkspaceViewModel(
            self._app_state, report_parser, report_exporter, recent_files_repo
        )

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._home_view = HomeView(self._home_vm)
        self._workspace_view = WorkspaceView(self._app_state, self._workspace_vm)

        self._stack.addWidget(self._home_view)
        self._stack.addWidget(self._workspace_view)

        self._connect_navigation()

    def _connect_navigation(self) -> None:
        self._home_view.new_document_requested.connect(self._open_import_flow)
        self._home_view.template_manager_requested.connect(self._open_template_manager)
        self._home_view.recent_file_opened.connect(self._open_recent_file)

    # ------------------------------------------------------------ Rotas
    def _open_import_flow(self) -> None:
        dialog = ImportDialog(self)
        if dialog.exec():
            result = dialog.get_result()
            pdf_paths: list[Path] = result["pdf_paths"]
            if not pdf_paths:
                return
            # Processamento em lote: a primeira peça abre imediatamente
            # no Workspace; as demais seguem a mesma chamada em sequência
            # (poderia evoluir para uma fila com barra de progresso).
            first_pdf = pdf_paths[0]
            self._workspace_vm.load_from_pdf(
                first_pdf, result["client_project"], result["evaluated_component"]
            )
            self._stack.setCurrentWidget(self._workspace_view)

    def _open_template_manager(self) -> None:
        dialog = TemplateView(self._template_repo, parent=self)
        dialog.exec()

    def _open_recent_file(self, file_id: str) -> None:
        # A resolução do file_id -> ReportDocument fica a cargo do
        # RecentFilesRepository/parser real, fora do escopo desta UI.
        self._stack.setCurrentWidget(self._workspace_view)
