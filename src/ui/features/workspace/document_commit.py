"""Helpers de commit e persistência de alterações no documento."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.core.application.export_report import validate_export
from src.core.application.session import save_workspace_session

if TYPE_CHECKING:
    from src.ui.features.workspace.viewmodels.workspace_viewmodel import WorkspaceViewModel

logger = logging.getLogger(__name__)


def commit_document_change(
    vm: WorkspaceViewModel,
    *,
    preview: bool = True,
    summary: bool = True,
    layout_dirty: bool = False,
    data_dirty_flag: bool = False,
    globals_refresh: bool = False,
    persist: bool = True,
) -> None:
    if globals_refresh:
        vm.refresh_global_fields()
    if summary:
        vm.refresh_sections_summary()
    if preview:
        vm.schedule_preview()
    if layout_dirty or data_dirty_flag:
        emit_dirty_state(vm)
    if persist:
        vm._schedule_session_save()
    refresh_export_validation(vm)


def emit_dirty_state(vm: WorkspaceViewModel) -> None:
    layout = vm.is_layout_dirty()
    data = vm.is_data_dirty()
    vm.layout_dirty_changed.emit(layout)
    vm.data_dirty_changed.emit(data)
    vm.template_dirty_changed.emit(layout)


def persist_session(vm: WorkspaceViewModel) -> None:
    document = vm._active_document()
    if document is None or vm._session_repo is None:
        return
    try:
        save_workspace_session(vm._session_repo, document)
    except Exception:
        logger.exception("Falha ao persistir sessão do workspace")
    vm._persist_project()


def refresh_export_validation(vm: WorkspaceViewModel) -> None:
    document = vm._active_document()
    if document is None:
        return
    issues = validate_export(document)
    vm.export_validation_ready.emit([
        {"level": i.level, "message": i.message} for i in issues
    ])
