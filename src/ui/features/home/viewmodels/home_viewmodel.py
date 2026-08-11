"""ViewModel da tela Home/Dashboard — nenhuma lógica de UI aqui."""
from __future__ import annotations

import logging
import traceback
from datetime import datetime

from PyQt6.QtCore import QObject, pyqtSignal

from src.core.application.project_service import ProjectService
from src.core.domain.ports import RecentFilesRepository, TemplateRepository
from src.core.infrastructure.template_repository import is_builtin_template_id
from src.ui.features.home.models.dashboard import (
    ProjectSummary,
    RecentFileSummary,
    TemplateSummary,
    project_summary_from_workspace,
)

logger = logging.getLogger(__name__)


class HomeViewModel(QObject):
    """Carrega templates e arquivos recentes através das portas de
    repositório (SQLite/JSON), sem conhecer os detalhes de implementação.

    A ``HomeView`` observa ``templates_loaded``, ``ongoing_projects_loaded``
    e ``recent_files_loaded`` e apenas renderiza — toda decisão de dados fica aqui.
    """

    templates_loaded = pyqtSignal(list)  # list[TemplateSummary]
    ongoing_projects_loaded = pyqtSignal(list)  # list[ProjectSummary]
    recent_files_loaded = pyqtSignal(list)  # list[RecentFileSummary]
    error_occurred = pyqtSignal(str, str, str)  # title, message, details

    def __init__(
        self,
        recent_files_repo: RecentFilesRepository,
        template_repo: TemplateRepository,
        project_service: ProjectService | None = None,
    ) -> None:
        super().__init__()
        self._recent_files_repo = recent_files_repo
        self._template_repo = template_repo
        self._project_service = project_service

    def load_dashboard(self) -> None:
        """Carrega templates, projetos em andamento e exports em paralelo lógico
        (chamadas síncronas simples aqui; podem virar QThread/worker
        se o volume de dados justificar, sem alterar a interface).
        """
        self._load_templates()
        self._load_ongoing_projects()
        self._load_recent_files()

    def _load_ongoing_projects(self) -> None:
        if self._project_service is None:
            self.ongoing_projects_loaded.emit([])
            return
        try:
            workspaces = self._project_service.list_ongoing()
        except Exception:  # noqa: BLE001
            logger.exception("Falha ao carregar projetos em andamento")
            self.error_occurred.emit(
                "Não foi possível carregar os projetos",
                "O banco de dados local pode estar indisponível.",
                traceback.format_exc(),
            )
            return
        summaries = [project_summary_from_workspace(workspace) for workspace in workspaces]
        self.ongoing_projects_loaded.emit(summaries)

    def rename_project(self, project_id: str, display_name: str) -> None:
        if self._project_service is None:
            return
        try:
            if self._project_service.rename(project_id, display_name):
                self._load_ongoing_projects()
        except Exception:  # noqa: BLE001
            logger.exception("Falha ao renomear projeto")
            self.error_occurred.emit(
                "Não foi possível renomear o projeto",
                "Tente novamente em instantes.",
                traceback.format_exc(),
            )

    def _load_templates(self) -> None:
        try:
            raw_templates = self._template_repo.list_templates()
        except Exception:  # noqa: BLE001 - convertido em feedback amigável
            logger.exception("Falha ao carregar templates")
            self.error_occurred.emit(
                "Não foi possível carregar os templates",
                "Verifique se o arquivo de configuração de templates não está corrompido.",
                traceback.format_exc(),
            )
            return
        summaries = [
            TemplateSummary(
                template_id=item["id"],
                name=item["name"],
                is_default=item.get("is_default", False),
                deletable=not is_builtin_template_id(item["id"]),
            )
            for item in raw_templates
        ]
        self.templates_loaded.emit(summaries)

    def delete_template(self, template_id: str) -> bool:
        if is_builtin_template_id(template_id):
            self.error_occurred.emit(
                "Template protegido",
                "Os templates padrão do sistema não podem ser excluídos.",
                "",
            )
            return False
        try:
            if not self._template_repo.delete_template(template_id):
                self.error_occurred.emit(
                    "Template não encontrado",
                    "Este template já foi removido ou não existe.",
                    "",
                )
                return False
        except Exception:  # noqa: BLE001
            logger.exception("Falha ao excluir template")
            self.error_occurred.emit(
                "Não foi possível excluir o template",
                "Verifique se o arquivo de configuração não está bloqueado.",
                traceback.format_exc(),
            )
            return False
        self._load_templates()
        return True

    def _load_recent_files(self) -> None:
        try:
            raw_files = self._recent_files_repo.list_recent(limit=50)
        except Exception:  # noqa: BLE001
            logger.exception("Falha ao carregar histórico de arquivos")
            self.error_occurred.emit(
                "Não foi possível carregar o histórico",
                "O banco de dados local pode estar indisponível.",
                traceback.format_exc(),
            )
            return
        summaries = [
            RecentFileSummary(
                file_id=item["id"],
                file_name=item["file_name"],
                client_project=item["client_project"],
                version=item["version"],
                updated_at=item.get("updated_at", datetime.now()),
                evaluated_component=item.get("evaluated_component", ""),
            )
            for item in raw_files
        ]
        self.recent_files_loaded.emit(summaries)
