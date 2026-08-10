"""Comandos de carregamento e navegação de projeto no workspace."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.core.application.session import load_workspace_session
from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession
from src.core.domain.ports import RecentFilesRepository, ReportDocument, WorkspaceSessionPort
from src.ui.features.workspace.commands.section_edit_commands import SectionEditCommands
from src.ui.features.workspace.services.document_session_service import DocumentSessionService


@dataclass(frozen=True)
class RecentFileResolution:
    ok: bool
    pdf_path: Path | None = None
    client_project: str = ""
    evaluated_component: str = ""
    error_title: str = ""
    error_message: str = ""


class ProjectCommands:
    @staticmethod
    def default_attachment_paths(
        document: ReportDocument,
        session: ProjectSession,
    ) -> list[Path]:
        """PDFs de origem para anexos — preserva sessão salva ou deriva dos slots."""
        if document.attachment_pdf_paths:
            return list(document.attachment_pdf_paths)
        if session.documents:
            return [slot.source_pdf_path for slot in session.documents]
        if document.source_pdf_path:
            return [document.source_pdf_path]
        return []

    @staticmethod
    def sync_attachment_paths(document: ReportDocument, session: ProjectSession) -> list[Path]:
        paths = ProjectCommands.default_attachment_paths(document, session)
        if paths and not document.attachment_pdf_paths:
            document.attachment_pdf_paths = list(paths)
        return paths

    @staticmethod
    def ensure_project_attachment_paths(session: ProjectSession) -> None:
        """Define anexos como PDFs ZEISS originais de todos os slots do projeto."""
        originals = [
            slot.source_pdf_path
            for slot in session.documents
            if slot.source_pdf_path and str(slot.source_pdf_path).strip()
        ]
        if not originals:
            return
        for slot in session.documents:
            doc = slot.document
            if doc is None:
                continue
            export_path = str(doc.last_export_path) if doc.last_export_path else None
            current = [p for p in doc.attachment_pdf_paths if str(p) != export_path]
            if not current:
                doc.attachment_pdf_paths = list(originals)

    @staticmethod
    def append_document_slots(
        session: ProjectSession,
        paths: list[Path],
        default_component: str,
    ) -> int:
        start_index = len(session.documents)
        for pdf_path in paths:
            session.documents.append(
                ProjectDocumentSlot(
                    source_pdf_path=pdf_path,
                    evaluated_component=default_component,
                )
            )
        return start_index

    @staticmethod
    def parse_slot(
        doc_service: DocumentSessionService,
        session_repo: WorkspaceSessionPort | None,
        session: ProjectSession,
        index: int,
    ) -> tuple[bool, str]:
        ok, details = doc_service.parse_slot(session, index)
        if not ok:
            return False, details
        slot_doc = session.documents[index].document
        if slot_doc is not None and session_repo is not None:
            load_workspace_session(session_repo, slot_doc)
            ProjectCommands.sync_attachment_paths(slot_doc, session)
        if slot_doc is not None:
            SectionEditCommands.ensure_fixed_sections_enabled(slot_doc)
        return True, ""

    @staticmethod
    def activate_document(
        session: ProjectSession,
        index: int,
        doc_service: DocumentSessionService,
        session_repo: WorkspaceSessionPort | None,
    ) -> ReportDocument | None:
        session.set_active_index(index)
        document = session.active_document
        if document is None:
            return None
        doc_service.load_versions_for_document(document)
        if session_repo is not None:
            load_workspace_session(session_repo, document)
        ProjectCommands.sync_attachment_paths(document, session)
        SectionEditCommands.ensure_fixed_sections_enabled(document)
        return document

    @staticmethod
    def resolve_recent_file(
        recent_files_repo: RecentFilesRepository | None,
        file_id: str,
    ) -> RecentFileResolution:
        if recent_files_repo is None:
            return RecentFileResolution(
                ok=False,
                error_title="Histórico indisponível",
                error_message="O repositório de arquivos recentes não está configurado.",
            )
        record = recent_files_repo.get_by_id(file_id)
        if record is None:
            return RecentFileResolution(
                ok=False,
                error_title="Arquivo não encontrado",
                error_message="Este registro não existe mais no histórico local.",
            )
        pdf_path = Path(record.get("source_pdf_path") or record["file_path"])
        if not pdf_path.exists():
            export_path = Path(record["file_path"])
            if export_path.exists() and export_path != pdf_path:
                pdf_path = export_path
            else:
                return RecentFileResolution(
                    ok=False,
                    error_title="Arquivo ausente",
                    error_message=f"O PDF não foi encontrado em:\n{pdf_path}",
                )
        return RecentFileResolution(
            ok=True,
            pdf_path=pdf_path,
            client_project=record.get("client_project", "Projeto"),
            evaluated_component=record.get(
                "evaluated_component", record.get("file_name", "Componente")
            ),
        )
