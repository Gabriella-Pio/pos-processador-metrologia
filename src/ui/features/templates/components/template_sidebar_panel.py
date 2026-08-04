"""Sidebar do editor de templates — sumário e dados globais."""
from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QTabWidget, QVBoxLayout

from src.ui.features.workspace.components.section_edit_view import SectionEditView
from src.ui.shared.report_editor.global_fields_panel import GlobalFieldsPanel
from src.ui.shared.report_editor.sections_list_panel import SectionsListPanel


class TemplateSidebarPanel(QFrame):
    section_edit_requested = pyqtSignal(str)
    section_enabled_changed = pyqtSignal(str, bool)
    section_delete_requested = pyqtSignal(str)
    add_custom_section_requested = pyqtSignal()
    sections_reordered = pyqtSignal(list)
    edit_visibility_changed = pyqtSignal(bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("WorkspaceSidebar")
        self._sections_map: dict[str, dict] = {}
        self._active_section_id: str | None = None
        self._edit_open = False
        self._vm = None

        self._sections_panel = SectionsListPanel(mode="template")
        self._sections_panel.section_edit_requested.connect(self._on_section_edit_requested)
        self._sections_panel.section_enabled_changed.connect(self.section_enabled_changed.emit)
        self._sections_panel.sections_reordered.connect(self.sections_reordered.emit)
        self._sections_panel.add_custom_section_requested.connect(self.add_custom_section_requested.emit)
        self._sections_panel.section_delete_requested.connect(self.section_delete_requested.emit)

        self._edit_view = SectionEditView()
        self._edit_view.set_defaults_mode(True)
        self._edit_view.back_requested.connect(self._close_edit)

        self._global_fields = GlobalFieldsPanel()

        self._sidebar_tabs = QTabWidget()
        self._sidebar_tabs.setObjectName("WorkspaceSidebarTabs")
        self._sidebar_tabs.addTab(self._sections_panel, "Sumário")
        self._sidebar_tabs.addTab(self._global_fields, "Dados")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._sidebar_tabs)

    @property
    def edit_view(self) -> SectionEditView:
        return self._edit_view

    @property
    def is_editing(self) -> bool:
        return self._edit_open

    def bind_view_model(self, view_model) -> None:
        self._vm = view_model
        self._edit_view.section_field_changed.connect(self._on_section_field_changed)
        self._edit_view.table_rows_changed.connect(view_model.update_section_table_rows)
        self._edit_view.media_kinds_changed.connect(view_model.update_section_media_kinds)
        self._global_fields.field_changed.connect(view_model.update_global_field)

    def refresh_appearance(self) -> None:
        self._sections_panel.refresh_appearance()
        self._edit_view.refresh_appearance()
        self._global_fields.refresh_appearance()

    def render_sections(self, sections: list[dict]) -> None:
        self._sections_map = {s["id"]: s for s in sections}
        self._sections_panel.render_sections(sections)
        if self._edit_open and self._active_section_id:
            if self._active_section_id in self._sections_map:
                self._refresh_edit_if_open()
            else:
                self._close_edit()

    def render_global_fields(self, values: dict[str, str], overridden: set[str]) -> None:
        self._global_fields.render_fields(values, overridden, show_restore=False)

    def set_active_section(self, section_id: str | None) -> None:
        self._active_section_id = section_id
        self._sections_panel.set_active_section(section_id)

    def open_edit_for_section(self, section_id: str) -> None:
        self._active_section_id = section_id
        self._sections_panel.set_active_section(section_id)
        section = self._sections_map.get(section_id, {"id": section_id, "title": section_id})
        overrides = dict(section.get("fields") or {})
        self._edit_view.open_section(
            section_id,
            section,
            overrides,
            section.get("table_rows"),
            None,
        )
        self._edit_open = True
        self.edit_visibility_changed.emit(True)
        self.section_edit_requested.emit(section_id)

    def _on_section_edit_requested(self, section_id: str) -> None:
        if self._sidebar_tabs.currentIndex() != 0:
            self._sidebar_tabs.setCurrentIndex(0)
        self.open_edit_for_section(section_id)

    def _on_section_field_changed(self, section_id: str, field_key: str, value: str) -> None:
        if self._vm is not None:
            self._vm.update_section_field(section_id, field_key, value)

    def _refresh_edit_if_open(self) -> None:
        if not self._edit_open or self._active_section_id is None:
            return
        if self._edit_view.has_pending_textarea():
            return
        section = self._sections_map.get(self._active_section_id, {})
        self._edit_view.patch_section(
            dict(section.get("fields") or {}),
            section.get("table_rows"),
            None,
            section,
        )

    def _close_edit(self) -> None:
        if not self._edit_open:
            return
        self._edit_open = False
        self.edit_visibility_changed.emit(False)

    def close_edit(self) -> None:
        self._close_edit()
