"""Abas do projeto, título e modo de exportação."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QPoint, Qt, QTimer
from PyQt6.QtGui import QCursor, QFontMetrics, QPixmap
from PyQt6.QtWidgets import (
    QFileDialog,
    QTabBar,
    QToolButton,
    QWidget,
)

from src.core.application.project_serializer import resolved_display_name
from src.core.domain.ports import ReportDocument
from src.ui.components.feedback import FeedbackLevel, confirm_action, show_friendly_error, show_info
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


class WorkspaceProjectTabsMixin:

    def _rebuild_project_tabs(self, session) -> None:
        self._project_tabs.blockSignals(True)
        while self._project_tabs.count():
            self._project_tabs.removeTab(0)

        unified = self._vm.export_mode_unified and len(session.documents) > 1
        self._add_pdf_btn.setVisible(not unified)

        if unified:
            n = len(session.documents)
            self._project_tabs.addTab(f"Relatório unificado ({n} arquivos)")
            self._project_tabs.setTabToolTip(
                0,
                "PDF consolidado do lote.\n"
                "Volte para “Exportar PDFs individuais” no menu ⋯ para ver as abas por arquivo.",
            )
            self._project_tabs.setCurrentIndex(0)
            self._project_tabs.setVisible(True)
            self._project_tabs.blockSignals(False)
            self._project_tabs.updateGeometry()
            return

        multi = len(session.documents) > 1
        for index, slot in enumerate(session.documents):
            label = document_tab_label(slot)
            self._project_tabs.addTab(label)
            tip = document_tab_tooltip(slot)
            if multi:
                tip += "\n\nClique em × para remover do projeto (o arquivo no disco não é apagado)."
                close_btn = QToolButton(self._project_tabs)
                close_btn.setObjectName("WorkspaceProjectTabClose")
                close_btn.setIcon(icon_close())
                close_btn.setAutoRaise(True)
                close_btn.setFixedSize(18, 18)
                close_btn.setIconSize(close_btn.iconSize())
                close_btn.setToolTip("Remover do projeto")
                close_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                close_btn.clicked.connect(
                    lambda _checked=False, idx=index: self._on_project_tab_close_requested(idx)
                )
                self._project_tabs.setTabButton(
                    index,
                    QTabBar.ButtonPosition.RightSide,
                    close_btn,
                )
            self._project_tabs.setTabToolTip(index, tip)
        if session.documents:
            self._project_tabs.setCurrentIndex(
                min(max(session.active_index, 0), len(session.documents) - 1)
            )
        self._project_tabs.setVisible(bool(session.documents))
        self._project_tabs.blockSignals(False)
        self._project_tabs.updateGeometry()


    def _on_project_loaded(self, session) -> None:
        self._project_title_block = True
        self._project_title_edit.setText(resolved_display_name(session))
        self._project_title_block = False
        self._sync_project_title_width()
        self._rebuild_project_tabs(session)
        self._update_export_options_visibility()
        self._refresh_versions()


    def _on_project_changed(self, session) -> None:
        if session is None:
            self._project_title_block = True
            self._project_title_edit.clear()
            self._project_title_block = False
            while self._project_tabs.count():
                self._project_tabs.removeTab(0)
            self._project_tabs.setVisible(False)
        self._update_export_options_visibility()


    def _sync_project_title_width(self) -> None:
        metrics = QFontMetrics(self._project_title_edit.font())
        text = self._project_title_edit.text() or self._project_title_edit.placeholderText() or " "
        width = metrics.horizontalAdvance(text) + 36
        self._project_title_edit.setFixedWidth(min(max(180, width), 560))


    def _focus_project_title(self) -> None:
        self._project_title_edit.setFocus(Qt.FocusReason.MouseFocusReason)
        self._project_title_edit.selectAll()


    def _on_project_title_edited(self) -> None:
        if self._project_title_block:
            return
        self._vm.set_display_name(self._project_title_edit.text())


    def _on_project_display_name_changed(self, display_name: str) -> None:
        if self._project_title_edit.text() == display_name:
            return
        self._project_title_block = True
        self._project_title_edit.setText(display_name)
        self._project_title_block = False
        self._sync_project_title_width()


    def _on_project_tab_changed(self, index: int) -> None:
        if index < 0:
            return
        if self._vm.export_mode_unified:
            return
        self._vm.switch_document(index)


    def _on_add_pdf_clicked(self) -> None:
        document = self._app_state.active_document
        default_component = document.evaluated_component if document else "Componente"
        paths, _ = QFileDialog.getOpenFileNames(self, "Adicionar PDFs ao projeto", "", "PDF (*.pdf)")
        if paths:
            self._vm.append_pdfs_to_project([Path(p) for p in paths], default_component)


    def _on_project_tab_close_requested(self, index: int) -> None:
        self._confirm_remove_document(index)


    def _confirm_remove_document(self, index: int) -> None:
        session = self._app_state.project_session
        if session is None or not (0 <= index < len(session.documents)):
            return
        slot = session.documents[index]
        label = slot.source_pdf_path.name or slot.evaluated_component or "Relatório"
        if not confirm_action(
            self,
            "Remover relatório do projeto?",
            f"“{label}” será removido deste projeto.\n\nO arquivo PDF no disco não será apagado.",
        ):
            return
        self._vm.remove_document_from_project(index)


    def _update_export_options_visibility(self) -> None:
        session = self._app_state.project_session
        multi = session is not None and len(session.documents) > 1
        self._export_individual_action.setVisible(multi)
        self._export_merged_action.setVisible(multi)
        if not multi:
            self._export_individual_action.setChecked(True)
            self._vm.set_export_mode_unified(False)
        else:
            self._vm.set_export_mode_unified(self._export_merged_action.isChecked())
        if session is not None:
            self._rebuild_project_tabs(session)


    def _on_export_mode_toggled(self, checked: bool) -> None:
        if not checked:
            return
        sync_export_mode_menu_icons(
            self._export_individual_action,
            self._export_merged_action,
        )
        unified = self._export_merged_action.isChecked()
        self._vm.set_export_mode_unified(unified)
        session = self._app_state.project_session
        if session is not None:
            self._rebuild_project_tabs(session)
        if unified:
            self._banner.set_level(FeedbackLevel.INFO)
            self._banner.set_message(
                "Modo unificado — preview e export usam o PDF consolidado do lote."
            )
        else:
            self._banner.set_message("")
            self._banner.sync_visibility()


    def _show_preview_menu(self) -> None:
        self._preview_menu.popup(
            self._more_btn.mapToGlobal(QPoint(0, self._more_btn.height()))
        )

