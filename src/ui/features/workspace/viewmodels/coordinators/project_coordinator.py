"""Mixin: carga, parse e slots do workspace."""
from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from src.ui.features.workspace.document_commit import (
    commit_document_change,
    emit_dirty_state,
    persist_session,
    refresh_export_validation,
)
from src.core.application.project_snapshot_serializer import deserialize_project_snapshot
from src.core.application.template_media import (
    locked_workspace_media_kinds,
    sanitize_workspace_media_kinds,
)
from src.core.application.document_editing import (
    extract_global_field_values,
    get_measurement_rows,
)
from src.core.application.template_layout import document_has_data_changes
from src.core.domain.field_definitions import CHART_SECTION_IDS
from src.core.domain.pdf_source import has_source_pdf_reference
from src.core.domain.project_session import ProjectSession
from src.core.domain.ports import (
    Annotation,
    ReportDocument,
    ReportImage,
    VersionEntry,
)
from src.ui.features.workspace.commands.media_commands import MediaCommands
from src.ui.features.workspace.commands.parsed_field_commands import ParsedFieldCommands
from src.ui.features.workspace.commands.project_commands import ProjectCommands
from src.ui.features.workspace.commands.section_edit_commands import SectionEditCommands
from src.ui.features.workspace.commands.template_commands import TemplateCommands
from src.ui.features.workspace.commands.version_commands import VersionCommands
from src.ui.features.workspace.helpers.workspace_helpers import (
    catalog_section_presence,
    dimensional_document_for_edit,
    document_with_timeline,
    preview_error_summary,
    slot_progress_label,
    version_status_text as format_version_status,
)
from src.ui.features.workspace.services.unified_session_edits import UnifiedSessionEdits
from src.ui.shared.report_editor.preview_worker import (
    PREVIEW_IMAGE_DEBOUNCE_MS,
    build_preview_metadata,
)

logger = logging.getLogger(__name__)


class WorkspaceProjectCoordinator:

    def _begin_busy(self, title: str, detail: str = "") -> None:
        self.busy_changed.emit(True, title, detail)


    def _update_busy_progress(self, current: int, total: int, detail: str = "") -> None:
        self.busy_progress.emit(current, total, detail)
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is not None:
            app.processEvents()


    def _end_busy(self) -> None:
        self.busy_changed.emit(False, "", "")


    def _parse_session_slots(self, session: ProjectSession, *, active_first: bool = True) -> bool:
        """Parse dos slots. Com vários PDFs: ativo na UI; demais no QThreadPool."""
        total = len(session.documents)
        if total == 0:
            return True

        self._cancel_deferred_parse()
        active = min(max(session.active_index, 0), total - 1)

        if active_first and total > 1:
            slot = session.documents[active]
            self._update_busy_progress(1, total, slot_progress_label(slot, active))
            if not self._parse_slot(session, active):
                return False
            pending = [i for i in range(total) if i != active]
            self._bg_parse_session = session
            self._bg_parse_total = total
            self._bg_parse.enqueue(session, pending)
            return True

        for index in range(total):
            slot = session.documents[index]
            self._update_busy_progress(index + 1, total, slot_progress_label(slot, index))
            if not self._parse_slot(session, index):
                return False
        return True


    def _cancel_deferred_parse(self) -> None:
        self._bg_parse.cancel()
        self._bg_parse_session = None
        self._bg_parse_total = 0


    def _on_background_slot_ready(
        self,
        generation: int,
        index: int,
        document: object,
        notice: str,
    ) -> None:
        session = self._app_state.project_session
        if session is None or session is not self._bg_parse_session:
            return
        if generation != self._bg_parse.generation:
            return
        if not (0 <= index < len(session.documents)):
            return
        if session.documents[index].document is not None:
            return
        if not isinstance(document, ReportDocument):
            return
        self._doc_service.attach_document_to_slot(session, index, document)
        ProjectCommands.finalize_parsed_slot(self._session_repo, session, index)
        if notice:
            self.import_notice.emit("Imagens Bosello", notice)
        done = sum(1 for slot in session.documents if slot.document is not None)
        total = self._bg_parse_total or len(session.documents)
        label = slot_progress_label(session.documents[index], index)
        # Progresso sem bloquear o cursor (overlay só se já estiver busy).
        self.busy_progress.emit(done, total, label)


    def _on_background_slot_failed(self, generation: int, index: int, error: str) -> None:
        session = self._app_state.project_session
        if generation != self._bg_parse.generation:
            return
        label = f"arquivo {index + 1}"
        if session is not None and 0 <= index < len(session.documents):
            label = slot_progress_label(session.documents[index], index)
        self._cancel_deferred_parse()
        self.error_occurred.emit(
            "Não foi possível ler o PDF",
            f"Erro ao processar {label}.",
            error,
        )


    def _on_background_parse_idle(self, generation: int) -> None:
        if generation != self._bg_parse.generation:
            return
        session = self._bg_parse_session
        self._bg_parse_session = None
        if session is None or self._app_state.project_session is not session:
            return
        if any(slot.document is None for slot in session.documents):
            return
        ProjectCommands.ensure_project_attachment_paths(session)
        self._persist_project()


    def _ensure_slot_parsed(self, session: ProjectSession, index: int) -> bool:
        if not (0 <= index < len(session.documents)):
            return False
        if session.documents[index].document is not None:
            return True
        self._bg_parse.claim_for_sync(index)
        slot = session.documents[index]
        self._begin_busy("Lendo PDF…", slot_progress_label(slot, index))
        try:
            ok = self._parse_slot(session, index)
            return ok
        finally:
            self._bg_parse.unclaim(index)
            self._end_busy()
            self._bg_parse.resume_if_needed()


    def _ensure_all_slots_parsed(self, session: ProjectSession) -> bool:
        self._cancel_deferred_parse()
        pending = [i for i, slot in enumerate(session.documents) if slot.document is None]
        if not pending:
            return True
        self._begin_busy(f"Preparando {len(pending)} PDF(s)…")
        try:
            for offset, index in enumerate(pending, start=1):
                slot = session.documents[index]
                self._update_busy_progress(offset, len(pending), slot_progress_label(slot, index))
                if not self._parse_slot(session, index):
                    return False
            return True
        finally:
            self._end_busy()


    def _reset_version_ui_state(self) -> None:
        """Limpa status de versão ao trocar de projeto (evita 'Visualizando vN' fantasma)."""
        self._viewing_version = None
        self._editing_from_version = None
        self._last_registered_version = None
        self.version_status_changed.emit(self.version_status_text())


    def load_project(
        self,
        client_project: str,
        pdf_entries: list[tuple[Path, str]],
        template_id: str = "default",
        report_mode: str = "auto",
        *,
        default_component: str = "",
    ) -> None:
        total = len(pdf_entries)
        self._cancel_deferred_parse()
        self._begin_busy(
            "Preparando projeto…" if total <= 1 else f"Importando lote ({total} PDFs)…",
        )
        try:
            self._reset_version_ui_state()
            session = self._doc_service.build_project_session(
                client_project,
                pdf_entries,
                template_id,
                report_mode=report_mode,
                default_component=default_component or (pdf_entries[0][1] if pdf_entries else ""),
            )
            self._app_state.set_project_session(session)
            self.project_loaded.emit(session)

            if not self._parse_session_slots(session):
                return
            ProjectCommands.ensure_project_attachment_paths(session)
            self._persist_project()
            self.switch_document(0)
        finally:
            self._end_busy()


    def load_project_by_id(self, project_id: str) -> bool:
        if self._project_service is None:
            self.error_occurred.emit(
                "Projetos indisponíveis",
                "O serviço de persistência de projetos não está configurado.",
                "",
            )
            return False
        self._cancel_deferred_parse()
        self._begin_busy("Abrindo projeto…")
        try:
            session = self._project_service.load_session(project_id)
            if session is None:
                self.error_occurred.emit(
                    "Projeto não encontrado",
                    "Este projeto não existe mais ou foi removido.",
                    "",
                )
                return False
            missing = [
                slot.source_pdf_path
                for slot in session.documents
                if has_source_pdf_reference(slot.source_pdf_path) and not slot.source_pdf_path.exists()
            ]
            if missing:
                self.error_occurred.emit(
                    "Arquivos ausentes",
                    "Um ou mais PDFs de origem não foram encontrados:\n"
                    + "\n".join(str(path) for path in missing[:3]),
                    "",
                )
                return False
            self._reset_version_ui_state()
            self._app_state.set_project_session(session)
            self.project_loaded.emit(session)
            from src.core.application.piece_ordering import sort_session_documents

            sort_session_documents(session)
            n = len(session.documents)
            if n > 1:
                self.busy_changed.emit(True, f"Lendo {n} PDFs do projeto…", "")
            if not self._parse_session_slots(session):
                return False
            ProjectCommands.ensure_project_attachment_paths(session)
            active = min(max(session.active_index, 0), len(session.documents) - 1)
            self.switch_document(active)
            return True
        finally:
            self._end_busy()


    def load_from_pdf(self, pdf_path: Path, client_project: str, evaluated_component: str) -> None:
        self.load_project(
            client_project,
            [(pdf_path, evaluated_component)],
            template_id="default",
        )


    def append_pdfs_to_project(self, paths: list[Path], default_component: str) -> None:
        session = self._app_state.project_session
        if session is None or not paths:
            return
        self._begin_busy(
            "Adicionando PDF…" if len(paths) == 1 else f"Adicionando {len(paths)} PDFs…",
        )
        try:
            new_indices = ProjectCommands.append_document_slots(session, paths, default_component)
            total = len(new_indices)
            for offset, index in enumerate(new_indices, start=1):
                slot = session.documents[index]
                self._update_busy_progress(offset, total, slot_progress_label(slot, offset - 1))
                if not self._parse_slot(session, index):
                    return
            ProjectCommands.ensure_project_attachment_paths(session)
            self._persist_project()
            self.project_loaded.emit(session)
        finally:
            self._end_busy()


    def remove_document_from_project(self, index: int) -> bool:
        session = self._app_state.project_session
        if session is None:
            return False
        ok, message = self._doc_service.remove_document_from_session(session, index)
        if not ok:
            if message:
                self.error_occurred.emit("Não foi possível remover", message, "")
            return False
        if self._session_timer.isActive():
            self._session_timer.stop()
            persist_session(self)
        ProjectCommands.ensure_project_attachment_paths(session)
        self._persist_project()
        self.project_loaded.emit(session)
        self.switch_document(session.active_index)
        return True


    def switch_document(self, index: int) -> None:
        session = self._app_state.project_session
        if session is None:
            return
        if session.active_index != index and self._session_timer.isActive():
            self._session_timer.stop()
            persist_session(self)
        if not self._ensure_slot_parsed(session, index):
            return
        document = ProjectCommands.activate_document(
            session, index, self._doc_service, self._session_repo
        )
        if document is None:
            return
        self._app_state.set_active_document(document)
        self.document_loaded.emit(document)
        self._commit_document_change(
            preview=True, summary=True, layout_dirty=True, data_dirty_flag=True, globals_refresh=True, persist=False
        )
        self._persist_project()
        self._emit_templates_list()


    def load_from_recent(self, file_id: str) -> None:
        resolution = ProjectCommands.resolve_recent_file(self._recent_files_repo, file_id)
        if not resolution.ok:
            self.error_occurred.emit(
                resolution.error_title,
                resolution.error_message,
                "",
            )
            return
        assert resolution.pdf_path is not None
        self.load_from_pdf(
            resolution.pdf_path,
            resolution.client_project,
            resolution.evaluated_component,
        )


    def _parse_slot(self, session: ProjectSession, index: int) -> bool:
        ok, details = ProjectCommands.parse_slot(
            self._doc_service, self._session_repo, session, index
        )
        if not ok:
            slot = session.documents[index]
            self.error_occurred.emit(
                "Não foi possível ler o PDF",
                f"Erro ao processar {slot_progress_label(slot, index)}.",
                details,
            )
            return False
        if details:
            self.import_notice.emit("Imagens Bosello", details)
        return True


    def set_display_name(self, display_name: str) -> None:
        session = self._app_state.project_session
        if session is None:
            return
        cleaned = display_name.strip()
        if not cleaned or cleaned == session.display_name:
            return
        session.display_name = cleaned
        self._persist_project()
        self.project_display_name_changed.emit(cleaned)


    def _persist_project(self) -> None:
        session = self._app_state.project_session
        if session is None or self._project_service is None:
            return
        try:
            self._project_service.save_session(session)
        except Exception:
            logger.exception("Falha ao persistir metadados do projeto")

