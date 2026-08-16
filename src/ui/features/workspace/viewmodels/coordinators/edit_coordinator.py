"""Mixin: edição de seções, campos, template e undo."""
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


class WorkspaceEditCoordinator:

    def _commit_document_change(self, **kwargs: bool | object) -> None:
        commit_document_change(self, **kwargs)


    def _emit_dirty_state(self) -> None:
        emit_dirty_state(self)


    def _schedule_session_save(self) -> None:
        self._session_timer.start()


    def _persist_session(self) -> None:
        persist_session(self)


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

