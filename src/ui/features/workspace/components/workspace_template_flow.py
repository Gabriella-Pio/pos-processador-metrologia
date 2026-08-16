"""Fluxo de templates e dirty flags no workspace."""
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


class WorkspaceTemplateFlowMixin:

    def _populate_template_combo(self, templates: list[dict]) -> None:
        session = self._app_state.project_session
        document = self._app_state.active_document
        slot = session.active_slot if session is not None else None
        # Em lote misto, o layout exibido é o da aba ativa — não o template da sessão.
        current_id = (
            (document.template_id if document is not None else None)
            or (slot.template_id if slot is not None else None)
            or (session.template_id if session is not None else None)
            or "default"
        )
        self._template_combo.blockSignals(True)
        self._template_combo.clear()
        for template in templates:
            self._template_combo.addItem(template["name"], template["id"])
        index = self._template_combo.findData(current_id)
        if index >= 0:
            self._template_combo.setCurrentIndex(index)
        self._template_combo.blockSignals(False)


    def _on_template_changed(self, index: int) -> None:
        if index < 0:
            return
        template_id = self._template_combo.itemData(index)
        session = self._app_state.project_session
        document = self._app_state.active_document
        current_id = (
            (document.template_id if document is not None else None)
            or (session.template_id if session is not None else None)
        )
        if session is None or document is None or template_id == current_id:
            return
        if self._vm.is_layout_dirty():
            if not confirm_action(
                self,
                "Alterar template?",
                "Há alterações no layout atual. Trocar o template vai substituí-las pelos defaults salvos.",
            ):
                self._populate_template_combo(self._vm.list_templates())
                return
        self._vm.change_template(template_id)


    def _on_layout_dirty_changed(self, dirty: bool) -> None:
        suffix = " ●" if dirty else ""
        self._save_layout_action.setEnabled(dirty)
        self._save_layout_action.setText(f"Salvar layout…{suffix}")
        self._template_selector.set_layout_dirty(dirty)


    def _on_data_dirty_changed(self, dirty: bool) -> None:
        self._data_dirty_label.setText("● Medições alteradas" if dirty else "")


    def _focus_template_combo(self) -> None:
        self._template_combo.setFocus()
        self._template_combo.showPopup()


    def _on_save_template_clicked(self) -> None:
        document = self._app_state.active_document
        session = self._app_state.project_session
        if document is None or session is None:
            return
        dialog = SaveTemplateDialog(
            self._vm.list_templates(),
            document.template_id,
            self,
        )
        if present_modal_dialog(self, dialog) != dialog.DialogCode.Accepted:
            return
        template_id = self._vm.save_current_as_template(
            dialog.template_name,
            dialog.create_new,
        )
        if template_id:
            show_info(self, "Template salvo", f"Layout salvo como “{dialog.template_name}”.")
            self._populate_template_combo(self._vm.list_templates())

