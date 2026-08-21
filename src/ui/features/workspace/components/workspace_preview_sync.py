"""Sincronização preview ↔ seções."""
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
from src.core.domain.section_schema import is_sidebar_section
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


class WorkspacePreviewSyncMixin:

    def _on_preview_generating(self, generating: bool) -> None:
        # Status só no chrome — sem overlay flutuando sobre o PDF.
        self._preview_status.set_busy(generating, "Atualizando preview…")
        if not generating:
            self._on_version_status_changed(self._vm.version_status_text())


    def _on_version_status_changed(self, text: str) -> None:
        self._preview_status.set_idle_text(text)


    def _on_sections_summary_ready(self, sections: list[dict]) -> None:
        self._section_anchor_map = {s["id"]: s for s in sections}
        self._preview_panel.set_anchor_map(self._section_anchor_map)
        for section in sections:
            section.setdefault("subtitle", "")
            section.setdefault("body", "")
        self._section_editor.render_sections(sections)
        if self._active_section_id:
            self._section_editor.set_active_section(self._active_section_id)
            # Só destaca — rolar de novo puxava a folha para o título a cada
            # regeneração do preview enquanto o usuário editava.
            self._preview_panel.highlight_section(self._active_section_id)


    def _on_preview_page_clicked(self, page_number: int) -> None:
        section_id = self._preview_panel.section_id_for_page(page_number)
        if section_id:
            self._on_preview_section_clicked(section_id)


    def _on_preview_section_clicked(
        self,
        section_id: str,
        focus_target: str = "section_title",
        image_path: str = "",
    ) -> None:
        if not is_sidebar_section(section_id):
            return
        self._active_section_id = section_id
        self._preview_panel.pin_vertical_scroll()
        self._section_editor.open_edit_for_section(section_id)
        anchor = self._section_anchor_map.get(section_id, {})
        title = anchor.get("title", section_id) if isinstance(anchor, dict) else section_id
        self._active_section_label.setText(f"Seção: {title}")
        self._sync_section_meta_row()
        self._preview_panel.highlight_section(section_id)
        if focus_target == "section_title":
            QTimer.singleShot(0, self._section_editor.focus_section_title)


    def _on_preview_metadata(self, metadata: dict) -> None:
        sections = metadata.get("sections", metadata)
        photo_anchors = metadata.get("photo_anchors", [])
        self._preview_panel.set_photo_anchors(photo_anchors)
        self._preview_panel.update_anchor_map(sections)
        for section_id, info in sections.items():
            if section_id in self._section_anchor_map:
                self._section_anchor_map[section_id]["page_start"] = info.get("page")
                self._section_anchor_map[section_id]["anchor_rect"] = info


    def _clear_preview_pages(self) -> None:
        self._preview_panel.clear()


    def _focus_preview_section(self, section_id: str) -> None:
        self._preview_panel.focus_section(section_id)

