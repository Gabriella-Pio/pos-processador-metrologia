"""Carregamento e troca de documentos no workspace."""
from __future__ import annotations

import logging
import traceback
from pathlib import Path

from src.core.application.batch_processing import (
    ReportMode,
    infer_report_mode,
    template_id_for_kind,
)
from src.core.application.project_serializer import default_display_name
from src.core.application.template_apply import apply_template_content_defaults, apply_template_layout
from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession
from src.core.domain.ports import ReportDocument, ReportParser, TemplateRepository, VersionHistoryRepository
from src.core.parser.source_kind import detect_source_kind

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
        kind = document.source_kind or detect_source_kind(slot.source_pdf_path)
        document.source_kind = kind
        slot.source_kind = kind
        template_id = session.effective_template_id(slot) if slot.template_id or session.report_mode == "mixed" else session.template_id
        if session.report_mode == "mixed":
            template_id = slot.template_id or template_id_for_kind(kind)  # type: ignore[arg-type]
            slot.template_id = template_id
        elif session.report_mode == "tomo_only":
            template_id = "tomografia"
            slot.template_id = template_id
        else:
            template_id = session.template_id
            slot.template_id = template_id
        document.template_id = template_id
        self.apply_template_defaults(document)
        slot.document = document
        return True, ""

    def apply_template_defaults(self, document: ReportDocument) -> None:
        if self._template_repo is None:
            return
        apply_template_layout(document, self._template_repo)
        apply_template_content_defaults(document, self._template_repo)

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
        report_mode: ReportMode | str = "auto",
    ) -> ProjectSession:
        paths = [path for path, _ in pdf_entries]
        kinds = [detect_source_kind(path) for path in paths]
        mode: ReportMode
        if report_mode == "auto":
            mode = infer_report_mode(kinds)  # type: ignore[assignment]
        else:
            mode = report_mode  # type: ignore[assignment]

        if mode == "tomo_only":
            effective_template = "tomografia"
        elif mode == "mmc_only":
            effective_template = template_id if template_id != "tomografia" else "default"
        else:
            effective_template = template_id

        session = ProjectSession(
            client_project=client_project,
            template_id=effective_template,
            report_mode=mode if mode in {"mmc_only", "tomo_only", "mixed"} else "mixed",
        )
        for pdf_path, component in pdf_entries:
            kind = detect_source_kind(pdf_path)
            slot_template = (
                template_id_for_kind(kind)  # type: ignore[arg-type]
                if session.report_mode == "mixed"
                else session.template_id
            )
            session.documents.append(
                ProjectDocumentSlot(
                    source_pdf_path=pdf_path,
                    evaluated_component=component,
                    source_kind=kind,
                    template_id=slot_template,
                )
            )
        session.display_name = default_display_name(session)
        return session
