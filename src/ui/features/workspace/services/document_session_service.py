"""Carregamento e troca de documentos no workspace."""
from __future__ import annotations

import logging
import traceback
from pathlib import Path

from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession
from src.core.domain.ports import ReportDocument, ReportParser, TemplateRepository, VersionHistoryRepository

logger = logging.getLogger(__name__)


class DocumentSessionService:
    def __init__(
        self,
        parser: ReportParser,
        template_repo: TemplateRepository | None = None,
        version_history_repo: VersionHistoryRepository | None = None,
    ) -> None:
        self._parser = parser
        self._template_repo = template_repo
        self._version_history_repo = version_history_repo

    def parse_slot(self, session: ProjectSession, index: int) -> tuple[bool, str]:
        slot = session.documents[index]
        try:
            document = self._parser.parse(slot.source_pdf_path)
        except Exception:
            logger.exception("Falha ao ler o PDF: %s", slot.source_pdf_path)
            return False, traceback.format_exc()
        document.client_project = session.client_project
        document.evaluated_component = slot.evaluated_component
        document.template_id = session.template_id
        self.apply_template_defaults(document)
        slot.document = document
        return True, ""

    def apply_template_defaults(self, document: ReportDocument) -> None:
        if self._template_repo is None:
            return
        content = self._template_repo.get_content_defaults(document.template_id)
        if not content:
            return
        for section_id, defaults in content.items():
            if isinstance(defaults, dict):
                document.section_overrides[section_id] = dict(defaults)

    def load_versions_for_document(self, document: ReportDocument) -> None:
        if self._version_history_repo is None:
            return
        document.version_history = self._version_history_repo.list_for_document(
            str(document.source_pdf_path),
            document.client_project,
            document.evaluated_component,
        )

    def build_project_session(
        self,
        client_project: str,
        pdf_entries: list[tuple[Path, str]],
        template_id: str = "default",
    ) -> ProjectSession:
        session = ProjectSession(client_project=client_project, template_id=template_id)
        for pdf_path, component in pdf_entries:
            session.documents.append(
                ProjectDocumentSlot(
                    source_pdf_path=pdf_path,
                    evaluated_component=component,
                )
            )
        return session
