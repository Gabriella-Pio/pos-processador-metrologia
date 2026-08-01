"""ViewModel da tela Home/Dashboard — nenhuma lógica de UI aqui."""
from __future__ import annotations

import logging
import traceback
from datetime import datetime

from PyQt6.QtCore import QObject, pyqtSignal

from src.core.ports import RecentFilesRepository, TemplateRepository
from src.ui.components.cards import RecentFileSummary, TemplateSummary

logger = logging.getLogger(__name__)


class HomeViewModel(QObject):
    """Carrega templates e arquivos recentes através das portas de
    repositório (SQLite/JSON), sem conhecer os detalhes de implementação.

    A ``HomeView`` observa ``templates_loaded`` e ``recent_files_loaded``
    e apenas renderiza — toda decisão de dados fica aqui.
    """

    templates_loaded = pyqtSignal(list)  # list[TemplateSummary]
    recent_files_loaded = pyqtSignal(list)  # list[RecentFileSummary]
    error_occurred = pyqtSignal(str, str, str)  # title, message, details

    def __init__(
        self,
        recent_files_repo: RecentFilesRepository,
        template_repo: TemplateRepository,
    ) -> None:
        super().__init__()
        self._recent_files_repo = recent_files_repo
        self._template_repo = template_repo

    def load_dashboard(self) -> None:
        """Carrega templates e arquivos recentes em paralelo lógico
        (chamadas síncronas simples aqui; podem virar QThread/worker
        se o volume de dados justificar, sem alterar a interface).
        """
        self._load_templates()
        self._load_recent_files()

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
            )
            for item in raw_templates
        ]
        self.templates_loaded.emit(summaries)

    def _load_recent_files(self) -> None:
        try:
            raw_files = self._recent_files_repo.list_recent(limit=20)
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
            )
            for item in raw_files
        ]
        self.recent_files_loaded.emit(summaries)
