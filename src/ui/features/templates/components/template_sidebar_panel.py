"""Sidebar do editor de templates — sumário e dados globais."""
from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QTabWidget, QVBoxLayout

from src.ui.shared.report_editor.base_sidebar_panel import BaseSidebarPanel
from src.ui.shared.report_editor.global_fields_panel import GlobalFieldsPanel
from src.ui.shared.report_editor.section_edit_view import SectionEditView
from src.ui.shared.report_editor.sections_list_panel import SectionsListPanel


class TemplateSidebarPanel(BaseSidebarPanel):
    section_edit_requested = pyqtSignal(str)
    section_enabled_changed = pyqtSignal(str, bool)
    section_delete_requested = pyqtSignal(str)
    add_custom_section_requested = pyqtSignal()
    sections_reordered = pyqtSignal(list)

    def __init__(self, parent=None) -> None:
        edit_view = SectionEditView()
        edit_view.set_defaults_mode(True)
        super().__init__(edit_view=edit_view, parent=parent)

        self._sections_panel = SectionsListPanel(mode="template")
        self._sections_panel.section_edit_requested.connect(self._on_section_edit_requested)
        self._sections_panel.section_enabled_changed.connect(self.section_enabled_changed.emit)
        self._sections_panel.sections_reordered.connect(self.sections_reordered.emit)
        self._sections_panel.add_custom_section_requested.connect(self.add_custom_section_requested.emit)
        self._sections_panel.section_delete_requested.connect(self.section_delete_requested.emit)

        self._edit_view.back_requested.connect(self._close_edit)
        self._global_fields = GlobalFieldsPanel()

        self._sidebar_tabs = QTabWidget()
        self._sidebar_tabs.setObjectName("WorkspaceSidebarTabs")
        self._sidebar_tabs.addTab(self._sections_panel, "Sumário")
        self._sidebar_tabs.addTab(self._global_fields, "Dados")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._sidebar_tabs)

    def bind_view_model(self, view_model) -> None:
        super().bind_view_model(view_model)
        self._edit_view.section_field_changed.connect(self._on_section_field_changed)
        self._edit_view.table_rows_changed.connect(view_model.update_section_table_rows)
        self._edit_view.media_kinds_changed.connect(view_model.update_section_media_kinds)
        self._global_fields.field_changed.connect(view_model.update_global_field)

    def refresh_appearance(self) -> None:
        self._sections_panel.refresh_appearance()
        self._edit_view.refresh_appearance()
        self._global_fields.refresh_appearance()

    def _render_sections_list(self, sections: list[dict]) -> None:
        self._sections_panel.render_sections(sections)

    def _set_sections_panel_active(self, section_id: str | None) -> None:
        self._sections_panel.set_active_section(section_id)

    def render_global_fields(self, values: dict[str, str], overridden: set[str]) -> None:
        self._global_fields.render_fields(values, overridden, show_restore=False)

    def _on_section_edit_requested(self, section_id: str) -> None:
        if self._sidebar_tabs.currentIndex() != 0:
            self._sidebar_tabs.setCurrentIndex(0)
        self.open_edit_for_section(section_id)
        self.section_edit_requested.emit(section_id)

    def _on_section_field_changed(self, section_id: str, field_key: str, value: str) -> None:
        if self._vm is not None:
            self._vm.update_section_field(section_id, field_key, value)

    def open_edit_for_section(
        self,
        section_id: str,
        *,
        itens_medicao: list[dict[str, str]] | None = None,
    ) -> None:
        super().open_edit_for_section(section_id, itens_medicao=itens_medicao)
        self.section_edit_requested.emit(section_id)
