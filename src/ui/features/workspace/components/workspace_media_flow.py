"""Fluxo de mídia e Bosello no workspace."""
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


class WorkspaceMediaFlowMixin:

    def _on_image_dropped(self, image_path: Path) -> None:
        # Preferir a seção em edição — evita gravar foto na seção errada.
        section_id = self._section_editor.editing_section_id() or self._active_section_id
        if section_id is None:
            show_friendly_error(
                self,
                "Selecione uma seção",
                "Abra a edição de uma seção antes de associar uma fotografia.",
            )
            return
        self._active_section_id = section_id
        self._vm.add_image_to_section(image_path, section_id)


    def _on_image_remove(self, image) -> None:
        self._vm.remove_image(image)


    def _on_image_caption_changed(self, image, caption: str) -> None:
        self._vm.update_image_caption(image, caption)


    def _on_image_edits_changed(self, _image) -> None:
        self._vm.notify_image_edits_changed()


    def _on_image_selected(self, image) -> None:
        self._active_annotation_image = image


    def _on_tool_selected(self, tool_id: str) -> None:
        self._active_annotation_tool = tool_id


    def _refresh_images(self) -> None:
        images = self._vm.images_for_workspace_ui()
        self._section_editor.render_images(images)
        if self._vm.export_mode_unified:
            has_bosello = any(img.bosello_import or img.section_id == "tomografia" for img in images)
            if not has_bosello:
                session = self._app_state.project_session
                if session is not None:
                    for slot in session.documents:
                        doc = slot.document
                        if doc is not None and doc.bosello_captured_paths:
                            has_bosello = True
                            break
            self._section_editor.set_bosello_captures_available(has_bosello)
            return
        document = self._app_state.active_document
        if document is not None:
            self._section_editor.set_bosello_captures_available(
                len(document.bosello_captured_paths) > 0
            )


    def _on_bosello_picker_requested(self) -> None:
        section_id = self._section_editor.editing_section_id() or self._active_section_id
        if section_id is None:
            show_friendly_error(
                self,
                "Selecione uma seção",
                "Abra a edição de uma seção antes de adicionar capturas Bosello.",
            )
            return

        session = self._app_state.project_session
        document = self._app_state.active_document
        captures: list[Path] = []
        if self._vm.export_mode_unified and session is not None:
            seen: set[str] = set()
            for slot in session.documents:
                doc = slot.document
                if doc is None:
                    continue
                for path in doc.bosello_captured_paths:
                    key = str(path)
                    if key in seen or not path.is_file():
                        continue
                    seen.add(key)
                    captures.append(path)
            paths_in_section = [
                img.image_path
                for img in session.unified_images
                if img.section_id == section_id
            ]
        else:
            if document is None:
                show_friendly_error(
                    self,
                    "Selecione uma seção",
                    "Abra a edição de uma seção antes de adicionar capturas Bosello.",
                )
                return
            captures = [path for path in document.bosello_captured_paths if path.is_file()]
            from src.core.application.bosello_image_import import section_image_paths

            paths_in_section = section_image_paths(document, section_id)

        if not captures:
            show_friendly_error(
                self,
                "Sem capturas Bosello",
                "Não há imagens capturadas do PDF Bosello neste projeto.",
            )
            return

        from src.ui.features.workspace.dialogs.bosello_capture_picker_dialog import (
            BoselloCapturePickerDialog,
        )

        dialog = BoselloCapturePickerDialog(
            captures,
            section_id=section_id,
            paths_in_section=paths_in_section,
            parent=self,
        )
        if present_modal_dialog(self, dialog) != dialog.DialogCode.Accepted:
            return
        selected = dialog.selected_paths()
        if not selected:
            return
        added = self._vm.add_bosello_captures_to_section(selected, section_id)
        if added:
            show_info(
                self,
                "Fotos adicionadas",
                f"{added} captura(s) Bosello adicionada(s) à seção.",
            )

