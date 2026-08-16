"""Mixin: preview, export e versões."""
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


class WorkspaceLifecycleCoordinator:

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
                # Fallback silencioso para a peça ativa — evita modal a cada refresh do preview.
                logger.info("Preview unificado indisponível: %s", exc.message)
                return self._document_with_project_timeline(self._active_document())
            except Exception:
                logger.exception("Falha ao montar preview unificado")
                return self._document_with_project_timeline(self._active_document())
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

