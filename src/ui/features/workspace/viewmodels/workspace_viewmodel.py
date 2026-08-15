"""
ViewModel do Workspace de edição — ponte entre a UI e o core (parser/exportador).
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from src.ui.features.workspace.document_commit import (
    commit_document_change,
    emit_dirty_state,
    persist_session,
    refresh_export_validation,
)
from src.core.application.project_service import ProjectService
from src.core.application.project_snapshot_serializer import deserialize_project_snapshot
from src.core.application.template_media import (
    locked_workspace_media_kinds,
    merge_workspace_media_kinds,
    sanitize_workspace_media_kinds,
)
from src.core.application.version_snapshot_service import VersionSnapshotService
from src.core.application.document_editing import (
    extract_global_field_values,
    get_measurement_rows,
)
from src.core.application.template_layout import document_has_data_changes
from src.core.domain.field_definitions import CHART_SECTION_IDS
from src.core.domain.pdf_source import has_source_pdf_reference, is_usable_source_pdf
from src.core.domain.project_session import ProjectSession
from src.core.domain.ports import (
    Annotation,
    RecentFilesRepository,
    ReportDocument,
    ReportExporter,
    ReportImage,
    ReportParser,
    TemplateRepository,
    VersionEntry,
    VersionHistoryRepository,
    VersionSnapshotPort,
    WorkspaceSessionPort,
)
from src.ui.features.workspace.commands.export_commands import ExportCommands
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
from src.ui.features.workspace.presenters.section_summary_presenter import SectionSummaryPresenter
from src.ui.features.workspace.services.document_session_service import DocumentSessionService
from src.ui.features.workspace.services.preview_service import PreviewService
from src.ui.features.workspace.services.slot_parse_worker import BackgroundSlotParseQueue
from src.ui.features.workspace.services.template_workspace_service import TemplateWorkspaceService
from src.ui.features.workspace.services.unified_session_edits import UnifiedSessionEdits
from src.ui.features.workspace.undo_stack import DocumentUndoStack
from src.ui.controllers.app_state import AppState
from src.ui.shared.report_editor.preview_worker import (
    DebouncedPreviewRunner,
    PREVIEW_IMAGE_DEBOUNCE_MS,
    build_preview_metadata,
)

logger = logging.getLogger(__name__)

_SESSION_SAVE_DEBOUNCE_MS = 2000


class WorkspaceViewModel(QObject):
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
    # busy, título, detalhe (ex.: nome do PDF)
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

    # ------------------------------------------------------------------ commit

    def _commit_document_change(self, **kwargs: bool | object) -> None:
        commit_document_change(self, **kwargs)

    def _emit_dirty_state(self) -> None:
        emit_dirty_state(self)

    def _schedule_session_save(self) -> None:
        self._session_timer.start()

    def _persist_session(self) -> None:
        persist_session(self)

    def _persist_project(self) -> None:
        session = self._app_state.project_session
        if session is None or self._project_service is None:
            return
        try:
            self._project_service.save_session(session)
        except Exception:
            logger.exception("Falha ao persistir metadados do projeto")

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

    def _refresh_export_validation(self) -> None:
        refresh_export_validation(self)

    def _active_document(self) -> ReportDocument | None:
        return self._app_state.active_document

    def _mutate_document(
        self,
        mutate: Callable[[ReportDocument], None],
        **commit: bool | object,
    ) -> bool:
        document = self._active_document()
        if document is None:
            return False
        mutate(document)
        self._commit_document_change(**commit)
        return True

    def _mutate_layout(self, mutate: Callable[[ReportDocument], None]) -> bool:
        return self._mutate_document(
            mutate, preview=True, summary=True, layout_dirty=True
        )

    def _mutate_data(
        self,
        mutate: Callable[[ReportDocument], None],
        *,
        globals_refresh: bool = False,
        summary: bool = True,
    ) -> bool:
        return self._mutate_document(
            mutate,
            preview=True,
            summary=summary,
            data_dirty_flag=True,
            globals_refresh=globals_refresh,
        )

    def push_undo_snapshot(self, label: str) -> None:
        document = self._active_document()
        if document is None:
            return
        self._undo_stack.push(document, label)

    def undo_last_change(self) -> bool:
        document = self._active_document()
        if document is None or not self._undo_stack.undo(document):
            return False
        self._commit_document_change(
            preview=True, summary=True, layout_dirty=True, data_dirty_flag=True, globals_refresh=True
        )
        return True

    # ------------------------------------------------------------------ dirty

    def is_layout_dirty(self) -> bool:
        document = self._active_document()
        if document is None:
            return False
        return self._template_service.is_layout_dirty(document)

    def is_data_dirty(self) -> bool:
        document = self._active_document()
        if document is None:
            return False
        return document_has_data_changes(document)

    def is_template_dirty(self) -> bool:
        return self.is_layout_dirty()

    # ------------------------------------------------------------------ load

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

    def _emit_templates_list(self) -> None:
        self.templates_list_ready.emit(self.list_templates())

    def list_templates(self) -> list[dict]:
        return self._template_service.list_templates()

    def change_template(self, template_id: str) -> None:
        session = self._app_state.project_session
        document = self._active_document()
        if session is None or document is None or self._template_repo is None:
            return
        TemplateCommands.apply_template_change(
            session, document, template_id, self._template_service
        )
        self._commit_document_change(
            preview=True, summary=True, layout_dirty=True, data_dirty_flag=False, globals_refresh=True
        )

    def save_current_as_template(self, name: str, create_new: bool) -> str | None:
        document = self._active_document()
        session = self._app_state.project_session
        if document is None or session is None or not name.strip():
            return None
        template_id = TemplateCommands.save_and_link_template(
            session, document, name, create_new, self._template_service
        )
        if template_id is None:
            return None
        self._emit_templates_list()
        self._emit_dirty_state()
        return template_id

    def reorder_sections(self, ordered_ids: list[str]) -> None:
        def mutate(document: ReportDocument) -> None:
            self.push_undo_snapshot("reorder")
            document.section_order = list(ordered_ids)

        self._mutate_layout(mutate)

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

    # ------------------------------------------------------------------ fields

    def refresh_global_fields(self) -> None:
        document = self._active_document()
        if document is None:
            return
        values, overridden = extract_global_field_values(document)
        self.global_fields_ready.emit(values, overridden)

    def get_effective_itens_medicao(self) -> list[dict[str, str]]:
        # Unificado: mesma fonte do preview (ex.: MMC no misto), não a peça ativa (Bosello).
        if self._is_unified_editing():
            document = self._document_for_preview() or self._dimensional_document_for_edit()
        else:
            document = self._active_document()
        if document is None:
            return []
        return get_measurement_rows(document)

    def _dimensional_document_for_edit(self) -> ReportDocument | None:
        """Documento onde persistem as medições dimensionais (peça CALYPSO base)."""
        return dimensional_document_for_edit(
            self._app_state.project_session,
            self._active_document(),
            unified_editing=self._is_unified_editing(),
        )

    def update_parsed_field(self, key: str, value: str) -> None:
        self._mutate_data(
            lambda doc: ParsedFieldCommands.update_parsed_field(doc, key, value),
            globals_refresh=True,
        )

    def restore_parsed_field(self, key: str) -> None:
        self._mutate_data(
            lambda doc: ParsedFieldCommands.restore_parsed_field(doc, key),
            globals_refresh=True,
        )

    def update_itens_medicao(self, rows: list[dict[str, str]]) -> None:
        if self._is_unified_editing():
            document = self._dimensional_document_for_edit()
            if document is None:
                return
            ParsedFieldCommands.update_itens_medicao(document, rows)
            self._commit_document_change(
                preview=True, summary=True, data_dirty_flag=True
            )
            return
        self._mutate_data(
            lambda doc: ParsedFieldCommands.update_itens_medicao(doc, rows),
        )

    def restore_itens_medicao(self) -> None:
        if self._is_unified_editing():
            document = self._dimensional_document_for_edit()
            if document is None:
                return
            ParsedFieldCommands.restore_itens_medicao(document)
            self._commit_document_change(
                preview=True, summary=True, data_dirty_flag=True
            )
            return
        self._mutate_data(ParsedFieldCommands.restore_itens_medicao)

    def refresh_sections_summary(self) -> None:
        # Modo unificado: sumário deve espelhar o mesmo documento do preview/PDF.
        document = self._document_for_preview()
        if document is None:
            return
        try:
            items = self._presenter.build(document)
            self.sections_summary_ready.emit([item.to_dict() for item in items])
        except Exception:
            logger.exception("Falha ao montar o sumário de seções")

    def _is_unified_editing(self) -> bool:
        return bool(self._export_mode_unified and self._is_multi_document())

    def _commit_unified_layout(self) -> None:
        self._commit_document_change(preview=True, summary=True, layout_dirty=True)

    def update_section_field(self, section_id: str, field: str, value: str) -> None:
        if self._is_unified_editing():
            session = self._app_state.project_session
            if session is not None and UnifiedSessionEdits.update_section_override(
                session, section_id, **{field: value}
            ):
                self._commit_unified_layout()
            return
        self._mutate_layout(
            lambda doc: SectionEditCommands.update_section_field(doc, section_id, field, value)
        )

    def restore_section_block(self, section_id: str, title_key: str, body_key: str) -> None:
        if self._is_unified_editing():
            session = self._app_state.project_session
            if session is not None and UnifiedSessionEdits.pop_override_keys(
                session, section_id, title_key, body_key
            ):
                self._commit_unified_layout()
            return
        self._mutate_layout(
            lambda doc: SectionEditCommands.restore_section_block(
                doc, section_id, title_key, body_key
            )
        )

    def restore_section(self, section_id: str) -> None:
        if self._is_unified_editing():
            session = self._app_state.project_session
            if session is not None and UnifiedSessionEdits.clear_section_override(
                session, section_id
            ):
                self._commit_unified_layout()
            return
        self._mutate_layout(
            lambda doc: SectionEditCommands.restore_section(doc, section_id)
        )

    def restore_section_field(self, section_id: str, field: str) -> None:
        if self._is_unified_editing():
            session = self._app_state.project_session
            if session is not None and UnifiedSessionEdits.pop_override_keys(
                session, section_id, field
            ):
                self._commit_unified_layout()
            return
        self._mutate_layout(
            lambda doc: SectionEditCommands.restore_section_field(doc, section_id, field)
        )

    def update_section_table_rows(self, section_id: str, rows: list[dict[str, str]]) -> None:
        if self._is_unified_editing():
            session = self._app_state.project_session
            if session is not None and UnifiedSessionEdits.update_section_override(
                session, section_id, table_rows=list(rows)
            ):
                self._commit_unified_layout()
            return
        self._mutate_layout(
            lambda doc: SectionEditCommands.update_section_table_rows(doc, section_id, rows)
        )

    def restore_section_table_rows(self, section_id: str) -> None:
        if self._is_unified_editing():
            session = self._app_state.project_session
            if session is not None and UnifiedSessionEdits.pop_override_keys(
                session, section_id, "table_rows"
            ):
                self._commit_unified_layout()
            return
        self._mutate_layout(
            lambda doc: SectionEditCommands.restore_section_table_rows(doc, section_id)
        )

    def delete_section(self, section_id: str) -> bool:
        if self._is_unified_editing():
            session = self._app_state.project_session
            if session is None:
                return False
            UnifiedSessionEdits.delete_section(session, section_id)
            self._commit_unified_layout()
            return True

        document = self._active_document()
        if document is None:
            return False
        if not SectionEditCommands.delete_section(document, section_id):
            return False
        self._commit_document_change(preview=True, summary=True, layout_dirty=True)
        return True

    def set_section_enabled(self, section_id: str, enabled: bool) -> None:
        from src.core.domain.section_schema import PROTECTED_SECTION_IDS

        if section_id in PROTECTED_SECTION_IDS:
            return

        if self._is_unified_editing():
            session = self._app_state.project_session
            if session is None:
                return
            if UnifiedSessionEdits.set_section_enabled(session, section_id, enabled):
                self.refresh_sections_summary()
                self.schedule_preview()
            return

        document = self._active_document()
        if document is None:
            return
        SectionEditCommands.set_section_enabled(document, section_id, enabled)
        self._commit_document_change(preview=True, summary=True, layout_dirty=True)

    def update_section_media_kinds(self, section_id: str, kinds: list[str]) -> None:
        if self._is_unified_editing():
            session = self._app_state.project_session
            if session is None:
                return
            if UnifiedSessionEdits.update_section_media_kinds(
                session,
                section_id,
                kinds,
                template_repo=self._template_repo,
                active_document=session.active_document,
            ):
                self._commit_unified_layout()
            return

        document = self._active_document()
        if document is None:
            return
        locked = locked_workspace_media_kinds(section_id, document, self._template_repo)
        merged = sanitize_workspace_media_kinds(section_id, locked, kinds)
        SectionEditCommands.update_section_media_kinds(document, section_id, merged)
        self._commit_document_change(preview=True, summary=True, layout_dirty=True)

    def update_disabled_chart_ids(self, section_id: str, disabled_ids: list[str]) -> None:
        if self._is_unified_editing():
            session = self._app_state.project_session
            if session is None:
                return
            if UnifiedSessionEdits.update_disabled_chart_ids(session, section_id, disabled_ids):
                self._commit_unified_layout()
            return

        document = self._active_document()
        if document is None:
            return
        SectionEditCommands.update_disabled_chart_ids(document, section_id, disabled_ids)
        self._commit_document_change(preview=True, summary=True, layout_dirty=True)

    def locked_media_kinds(self, section_id: str) -> list[str]:
        if self._is_unified_editing() and section_id in CHART_SECTION_IDS:
            return []
        document = self._active_document()
        if document is None:
            return []
        return locked_workspace_media_kinds(section_id, document, self._template_repo)

    def add_custom_section(self, title: str) -> str | None:
        cleaned = (title or "").strip() or "Nova seção"
        if self._is_unified_editing():
            session = self._app_state.project_session
            if session is None:
                return None
            section_id = UnifiedSessionEdits.add_custom_section(session, cleaned)
            if section_id is not None:
                self._commit_unified_layout()
            return section_id

        document = self._active_document()
        if document is None:
            return None
        section_id = SectionEditCommands.add_custom_section(document, cleaned)
        if section_id is None:
            return None
        self._commit_document_change(preview=True, summary=True, layout_dirty=True, persist=False)
        return section_id

    def list_addable_catalog_sections(self) -> list[dict[str, str]]:
        from src.core.domain.section_schema import list_addable_catalog_sections

        document = (
            self._document_for_preview()
            if self._is_unified_editing()
            else self._active_document()
        )
        if document is None:
            return []
        present, deleted = catalog_section_presence(
            document,
            self._exporter,
            self._app_state.project_session,
            unified_editing=self._is_unified_editing(),
        )
        return list_addable_catalog_sections(
            present_section_ids=present,
            deleted_section_ids=deleted,
        )

    def add_catalog_section(self, section_id: str) -> str | None:
        if self._is_unified_editing():
            session = self._app_state.project_session
            if session is None:
                return None
            added = UnifiedSessionEdits.add_catalog_section(session, section_id)
            if added is not None:
                self._commit_unified_layout()
            return added

        document = self._active_document()
        if document is None:
            return None
        added = SectionEditCommands.add_catalog_section(document, section_id)
        if added is None:
            return None
        self._commit_document_change(preview=True, summary=True, layout_dirty=True, persist=False)
        return added

    def replace_custom_with_catalog(
        self,
        custom_section_id: str,
        catalog_section_id: str,
    ) -> str | None:
        """Troca uma seção personalizada temporária por uma do catálogo."""
        from src.core.domain.section_schema import is_custom_section_id

        if self._is_unified_editing():
            if is_custom_section_id(custom_section_id):
                self.delete_section(custom_section_id)
            return self.add_catalog_section(catalog_section_id)

        document = self._active_document()
        if document is None:
            return None
        if is_custom_section_id(custom_section_id):
            SectionEditCommands.delete_section(document, custom_section_id)
        added = SectionEditCommands.add_catalog_section(document, catalog_section_id)
        if added is None:
            return None
        self._commit_document_change(preview=True, summary=True, layout_dirty=True, persist=False)
        return added

    def get_section_page_map(self) -> dict[str, int]:
        document = self._active_document()
        if document is None:
            return {}
        exporter = self._exporter
        if hasattr(exporter, "_last_section_anchor_map"):
            return {
                sid: (info or {}).get("page", 0)
                for sid, info in exporter._last_section_anchor_map.items()
            }
        return {}

    # ------------------------------------------------------------------ preview

    def schedule_preview(self, *, image_edit: bool = False) -> None:
        if self._viewing_version is not None:
            self._viewing_version = None
            self.version_status_changed.emit(self.version_status_text())
        debounce_ms = PREVIEW_IMAGE_DEBOUNCE_MS if image_edit else None
        self._preview_runner.schedule(debounce_ms=debounce_ms)

    def generate_preview(self) -> None:
        self.schedule_preview()

    def _on_preview_finished(self, pages: list[bytes], metadata: dict) -> None:
        self.preview_ready.emit(pages)
        self.preview_metadata_ready.emit(metadata)

    def _document_for_preview(self) -> ReportDocument | None:
        if self._export_mode_unified and self._is_multi_document():
            session = self._app_state.project_session
            if session is None:
                return None
            from src.core.application.unified_export import (
                UnifiedExportError,
                build_unified_export_document,
            )

            try:
                return self._document_with_project_timeline(
                    build_unified_export_document(session)
                )
            except UnifiedExportError as exc:
                logger.info("Preview unificado indisponível: %s", exc.message)
                self.error_occurred.emit(
                    "Preview unificado indisponível",
                    exc.message,
                    "",
                )
                return None
            except Exception:
                logger.exception("Falha ao montar preview unificado")
                return None
        return self._document_with_project_timeline(self._active_document())

    def _is_multi_document(self) -> bool:
        session = self._app_state.project_session
        return session is not None and len(session.documents) > 1

    @property
    def export_mode_unified(self) -> bool:
        return self._export_mode_unified

    def set_export_mode_unified(self, unified: bool) -> None:
        unified = bool(unified) and self._is_multi_document()
        if self._export_mode_unified == unified:
            return
        if unified:
            session = self._app_state.project_session
            if session is not None and not self._ensure_all_slots_parsed(session):
                return
        self._export_mode_unified = unified
        if unified:
            from src.core.application.piece_ordering import sort_session_documents
            from src.core.application.unified_media import seed_unified_images_from_pieces

            session = self._app_state.project_session
            if session is not None and sort_session_documents(session):
                self.project_loaded.emit(session)
            if session is not None:
                seed_unified_images_from_pieces(session)
                self._persist_project()
            self._begin_busy("Montando relatório unificado…")
            try:
                self.refresh_sections_summary()
                self.schedule_preview()
                self._app_state.notify_images_changed()
                if hasattr(self, "_app_state") and self._active_document() is not None:
                    refresh_export_validation(self)
            finally:
                self._end_busy()
            return
        self.refresh_sections_summary()
        self.schedule_preview()
        self._app_state.notify_images_changed()
        if hasattr(self, "_app_state") and self._active_document() is not None:
            refresh_export_validation(self)

    def _document_with_project_timeline(
        self,
        document: ReportDocument | None,
    ) -> ReportDocument | None:
        return document_with_timeline(document, self.list_version_timeline())

    def _preview_error_summary(self, details: str, *, max_len: int = 240) -> str:
        return preview_error_summary(details, max_len=max_len)

    def _on_preview_failed(self, details: str) -> None:
        self.error_occurred.emit(
            "Não foi possível atualizar o preview",
            self._preview_error_summary(details),
            details,
        )

    # ------------------------------------------------------------------ media

    def images_for_workspace_ui(self) -> list[ReportImage]:
        """Imagens exibidas no sumário/painel — unificadas no modo PDF único."""
        if self._export_mode_unified and self._is_multi_document():
            session = self._app_state.project_session
            if session is not None:
                # Store unificado mesmo vazio (usuário removeu todas) — não voltar às peças.
                return list(session.unified_images)
            document = self._document_for_preview()
            return list(document.images) if document is not None else []
        document = self._active_document()
        return list(document.images) if document is not None else []

    def add_image_to_section(self, image_path: Path, section_id: str) -> None:
        if self._export_mode_unified and self._is_multi_document():
            session = self._app_state.project_session
            if session is None:
                return
            from src.core.application.unified_media import add_unified_image

            add_unified_image(session, image_path, section_id)
            self._persist_project()
            self._app_state.notify_images_changed()
            self._commit_document_change(
                preview=True, summary=True, data_dirty_flag=True, persist=False
            )
            return
        if self._mutate_data(
            lambda doc: MediaCommands.add_image(doc, image_path, section_id),
        ):
            self._app_state.notify_images_changed()

    def add_bosello_captures_to_section(self, image_paths: list[Path], section_id: str) -> int:
        if self._export_mode_unified and self._is_multi_document():
            session = self._app_state.project_session
            if session is None:
                return 0
            from src.core.application.unified_media import add_unified_image

            added = 0
            for path in image_paths:
                add_unified_image(session, path, section_id, bosello_import=True)
                added += 1
            if added:
                self._persist_project()
                self._app_state.notify_images_changed()
                self._commit_document_change(
                    preview=True, summary=True, data_dirty_flag=True, persist=False
                )
            return added

        added = 0

        def mutate(doc: ReportDocument) -> None:
            nonlocal added
            added = MediaCommands.add_bosello_captures(doc, image_paths, section_id)

        if self._mutate_data(mutate):
            self._app_state.notify_images_changed()
        return added

    def remove_image(self, image: ReportImage) -> None:
        if self._export_mode_unified and self._is_multi_document():
            session = self._app_state.project_session
            if session is None:
                return
            from src.core.application.unified_media import remove_unified_image

            remove_unified_image(session, image)
            self._persist_project()
            self._app_state.notify_images_changed()
            self._commit_document_change(
                preview=True, summary=True, data_dirty_flag=True, persist=False
            )
            return
        if self._mutate_data(lambda doc: MediaCommands.remove_image(doc, image)):
            self._app_state.notify_images_changed()

    def update_image_caption(self, image: ReportImage, caption: str) -> None:
        if self._export_mode_unified and self._is_multi_document():
            session = self._app_state.project_session
            if session is None:
                return
            from src.core.application.unified_media import update_unified_image_caption

            update_unified_image_caption(session, image, caption)
            self._persist_project()
            self._commit_document_change(
                preview=True, summary=False, data_dirty_flag=True, persist=False
            )
            return
        self._mutate_data(
            lambda doc: MediaCommands.update_image_caption(doc, image, caption),
            summary=False,
        )

    def add_annotation(self, image: ReportImage, annotation: Annotation) -> None:
        MediaCommands.add_annotation(image, annotation)
        self._notify_image_edits_changed()

    def notify_image_edits_changed(self) -> None:
        self._notify_image_edits_changed()

    def _notify_image_edits_changed(self) -> None:
        if self._export_mode_unified and self._is_multi_document():
            self._persist_project()
        self._app_state.notify_images_changed()
        self._commit_document_change(preview=False, summary=True, data_dirty_flag=True)
        self.schedule_preview(image_edit=True)

    def register_new_version(self, responsible_name: str, description: str) -> None:
        document = self._active_document()
        session = self._app_state.project_session
        if document is None or session is None:
            return

        self._flush_pending_saves()

        if self._snapshot_service is not None and session.project_id:
            snapshot = self._snapshot_service.create_snapshot(
                session, responsible_name, description
            )
            if snapshot is None:
                self.error_occurred.emit(
                    "Não foi possível registrar a versão",
                    "O serviço de snapshots não está disponível.",
                    "",
                )
                return
            entry = VersionEntry(
                version_number=snapshot.version_number,
                timestamp=snapshot.created_at or datetime.now(),
                responsible_name=responsible_name,
                description=description,
            )
            self._last_registered_version = snapshot.version_number
            self._editing_from_version = None
            self._viewing_version = None
        else:
            entry = VersionCommands.create_entry(document, responsible_name, description)

        if self._version_history_repo is not None:
            self._version_history_repo.append(
                str(document.source_pdf_path),
                document.client_project,
                document.evaluated_component,
                entry,
            )
        self._app_state.register_version(entry)
        self.version_timeline_changed.emit(self.list_version_timeline())
        self.version_status_changed.emit(self.version_status_text())
        self.schedule_preview()

    def list_version_timeline(self) -> list[VersionEntry]:
        session = self._app_state.project_session
        if session is not None and session.project_id:
            entries = self._snapshot_service.list_timeline_entries(session.project_id)
            if entries:
                return entries
        document = self._active_document()
        return list(document.version_history) if document is not None else []

    def version_status_text(self) -> str:
        return format_version_status(
            viewing_version=self._viewing_version,
            editing_from_version=self._editing_from_version,
            last_registered_version=self._last_registered_version,
        )

    def restore_version(self, version_number: int) -> bool:
        session = self._app_state.project_session
        if session is None or not session.project_id:
            return False
        snapshot = self._snapshot_service.get_snapshot(session.project_id, version_number)
        if snapshot is None:
            self.error_occurred.emit(
                "Versão não encontrada",
                f"A versão v{version_number} não existe para este projeto.",
                "",
            )
            return False

        self._flush_pending_saves()
        try:
            restored, workspaces, histories = deserialize_project_snapshot(
                snapshot.snapshot_json
            )
        except (ValueError, TypeError) as exc:
            self.error_occurred.emit(
                "Snapshot inválido",
                "Não foi possível ler os dados desta versão.",
                str(exc),
            )
            return False

        restored.project_id = session.project_id
        self._app_state.set_project_session(restored)
        self.project_loaded.emit(restored)

        for index in range(len(restored.documents)):
            if not self._parse_slot(restored, index):
                return False
        VersionCommands.apply_snapshot_workspaces(
            restored,
            workspaces,
            histories,
            session_repo=self._session_repo,
        )

        ProjectCommands.ensure_project_attachment_paths(restored)
        self._persist_project()
        self._editing_from_version = version_number
        self._viewing_version = None
        self._last_registered_version = None
        active = min(max(restored.active_index, 0), len(restored.documents) - 1)
        self.switch_document(active)
        self.version_timeline_changed.emit(self.list_version_timeline())
        self.version_status_changed.emit(self.version_status_text())
        return True

    def preview_version(self, version_number: int) -> bool:
        document = self._document_from_snapshot(version_number)
        if document is None:
            self.error_occurred.emit(
                "Não foi possível visualizar",
                f"A versão v{version_number} não pôde ser carregada para preview.",
                "",
            )
            return False
        self._viewing_version = version_number
        self.version_status_changed.emit(self.version_status_text())
        try:
            pages = self._preview_service.render_pages(document)
            metadata = build_preview_metadata(self._exporter)
            self.preview_ready.emit(pages)
            self.preview_metadata_ready.emit(metadata)
        except Exception:
            logger.exception("Falha ao gerar preview da versão v%s", version_number)
            self.error_occurred.emit(
                "Preview indisponível",
                f"Não foi possível gerar o preview da versão v{version_number}.",
                "",
            )
            return False
        return True

    def export_version_snapshot(self, version_number: int, output_path: Path) -> None:
        document = self._document_from_snapshot(version_number)
        outcome = self._export_commands.export_document(document, output_path)
        if not outcome.success:
            self.error_occurred.emit(
                outcome.error_title,
                outcome.error_message,
                outcome.error_details,
            )
            return
        assert outcome.path is not None
        self.export_finished.emit(outcome.path)

    def clear_version_view_state(self) -> None:
        """Sai do modo 'visualizando versão' e volta ao preview do rascunho atual."""
        if self._viewing_version is None:
            return
        self.schedule_preview()

    def _flush_pending_saves(self) -> None:
        if self._session_timer.isActive():
            self._session_timer.stop()
            persist_session(self)
        self._persist_project()

    def _document_from_snapshot(self, version_number: int) -> ReportDocument | None:
        session = self._app_state.project_session
        if session is None:
            return None
        return VersionCommands.document_from_snapshot(
            self._snapshot_service,
            self._doc_service,
            session,
            version_number,
        )

    def export_document(self, output_path: Path) -> None:
        outcome = self._export_commands.export_document(
            self._document_with_project_timeline(self._active_document()),
            output_path,
        )
        if not outcome.success:
            self.error_occurred.emit(
                outcome.error_title,
                outcome.error_message,
                outcome.error_details,
            )
            return
        assert outcome.path is not None
        self.export_finished.emit(outcome.path)

    def export_unified_document(self, output_path: Path) -> None:
        session = self._app_state.project_session
        if session is not None and not self._ensure_all_slots_parsed(session):
            return
        outcome = self._export_commands.export_unified_document(
            session,
            output_path,
            version_history=self.list_version_timeline(),
        )
        if not outcome.success:
            self.error_occurred.emit(
                outcome.error_title,
                outcome.error_message,
                outcome.error_details,
            )
            return
        assert outcome.path is not None
        self.export_finished.emit(outcome.path)

    def export_all_documents(self, output_dir: Path) -> list[Path]:
        session = self._app_state.project_session
        if session is not None and not self._ensure_all_slots_parsed(session):
            return []
        return self._export_commands.export_all_documents(
            session,
            output_dir,
            switch_document=self.switch_document,
            export_document=self.export_document,
        )
