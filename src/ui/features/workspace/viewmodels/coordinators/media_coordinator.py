"""Mixin: mídia (imagens, Bosello, anotações)."""
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


class WorkspaceMediaCoordinator:

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

