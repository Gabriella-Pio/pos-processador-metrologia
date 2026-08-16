"""Diálogos e ações de versão no workspace."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QPoint, Qt, QTimer
from PyQt6.QtGui import QCursor, QFontMetrics, QPixmap
from PyQt6.QtWidgets import (
    QFileDialog,
    QToolButton,
    QWidget,
)

from src.core.application.project_serializer import resolved_display_name
from src.core.domain.ports import ReportDocument
from src.ui.components.feedback import confirm_action, show_friendly_error, show_info
from src.ui.components.icons import icon_close
from src.ui.components.modal_presentation import present_modal_dialog
from src.ui.features.workspace.components.workspace_tab_labels import (
    document_header_label,
    document_tab_label,
    document_tab_tooltip,
)
from src.ui.features.workspace.commands.project_commands import ProjectCommands
from src.ui.features.workspace.components.workspace_preview_chrome import (
    sync_export_mode_menu_icons,
)
from src.ui.features.workspace.dialogs.save_template_dialog import SaveTemplateDialog
from src.ui.features.workspace.dialogs.version_register_dialog import VersionRegisterDialog


class WorkspaceVersionFlowMixin:

    def _refresh_versions(self) -> None:
        self._section_editor.render_versions(self._vm.list_version_timeline())


    def _on_version_timeline_changed(self, entries: list) -> None:
        self._section_editor.render_versions(entries)


    def _on_register_version(self) -> None:
        document = self._app_state.active_document
        if document is None:
            return
        default_responsible = ""
        if document.control_info is not None:
            default_responsible = document.control_info.measured_by or ""
        dialog = VersionRegisterDialog(default_responsible, self)
        if present_modal_dialog(self, dialog) != dialog.DialogCode.Accepted:
            return
        responsible, description = dialog.get_values()
        self._vm.register_new_version(responsible, description)


    def _on_preview_version(self, version_number: int) -> None:
        self._vm.preview_version(version_number)


    def _on_restore_version(self, version_number: int) -> None:
        if not self._vm.restore_version(version_number):
            return
        self._on_version_status_changed(self._vm.version_status_text())


    def _on_export_version(self, version_number: int) -> None:
        document = self._app_state.active_document
        default_name = "relatorio.pdf"
        if document is not None:
            default_name = f"{document.evaluated_component}_v{version_number}.pdf"
        path, _ = QFileDialog.getSaveFileName(
            self,
            f"Exportar versão v{version_number}",
            default_name,
            "PDF (*.pdf)",
        )
        if path:
            self._vm.export_version_snapshot(version_number, Path(path))

