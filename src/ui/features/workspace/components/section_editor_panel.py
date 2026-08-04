"""Sidebar esquerda do workspace — sumário compacto + edição sob demanda."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QStackedWidget, QTabWidget, QVBoxLayout, QWidget

from src.core.domain.ports import ReportDocument, ReportImage
from src.ui.components.buttons import SecondaryButton
from src.ui.components.panels import VersionHistoryPanel
from src.ui.styles import SPACING
from src.ui.features.workspace.components.dados_relatorio_panel import DadosRelatorioPanel
from src.ui.features.workspace.components.section_edit_view import SectionEditView
from src.ui.features.workspace.components.sections_panel import SectionsPanel

_INDEX_SUMARIO = 0
_INDEX_DADOS = 1


class SectionEditorPanel(QFrame):
    """Sumário enxuto; edição aparece abaixo da lista sem trocar de tela."""

    section_selected = pyqtSignal(str)
    section_delete_requested = pyqtSignal(str)
    add_custom_section_requested = pyqtSignal()
    sections_reordered = pyqtSignal(list)
    section_field_changed = pyqtSignal(str, str, str)
    section_field_restore_requested = pyqtSignal(str, str)
    section_block_restore_requested = pyqtSignal(str, str, str)
    table_rows_changed = pyqtSignal(str, list)
    table_rows_restore_requested = pyqtSignal(str)
    parsed_field_changed = pyqtSignal(str, str)
    parsed_field_restore_requested = pyqtSignal(str)
    itens_medicao_changed = pyqtSignal(list)
    itens_medicao_restore_requested = pyqtSignal()
    new_version_requested = pyqtSignal()
    image_dropped = pyqtSignal(Path)
    tool_selected = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("WorkspaceSidebar")
        self._vm = None
        self._sections_map: dict[str, dict] = {}
        self._active_section_id: str | None = None
        self._global_values: dict[str, str] = {}
        self._itens_medicao: list[dict[str, str]] = []

        self._nav_dados_btn = SecondaryButton("Dados do relatório")
        self._nav_dados_btn.clicked.connect(self._show_dados)

        self._sections_panel = SectionsPanel()
        self._sections_panel.section_navigated.connect(self._on_section_navigated)
        self._sections_panel.section_edit_requested.connect(self._on_section_edit_requested)
        self._sections_panel.section_delete_requested.connect(self.section_delete_requested.emit)
        self._sections_panel.add_custom_section_requested.connect(
            self.add_custom_section_requested.emit
        )
        self._sections_panel.sections_reordered.connect(self.sections_reordered.emit)

        self._edit_view = SectionEditView()
        self._edit_view.back_requested.connect(self._close_edit)
        self._edit_view.delete_requested.connect(self.section_delete_requested.emit)
        self._edit_view.setVisible(False)

        self._sumario_work = QWidget()
        sumario_work_layout = QVBoxLayout(self._sumario_work)
        sumario_work_layout.setContentsMargins(0, 0, 0, 0)
        sumario_work_layout.setSpacing(SPACING.sm)
        sumario_work_layout.addWidget(self._sections_panel, stretch=2)
        sumario_work_layout.addWidget(self._edit_view, stretch=3)

        self._dados_panel = DadosRelatorioPanel()
        self._dados_panel.back_requested.connect(self._show_sumario)

        self._sumario_stack = QStackedWidget()
        self._sumario_stack.addWidget(self._sumario_work)
        self._sumario_stack.addWidget(self._dados_panel)

        sumario_container = QFrame()
        sumario_layout = QVBoxLayout(sumario_container)
        sumario_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, 0)
        sumario_layout.setSpacing(SPACING.sm)
        sumario_layout.addWidget(self._nav_dados_btn)
        sumario_layout.addWidget(self._sumario_stack, stretch=1)

        self._version_panel = VersionHistoryPanel()
        self._version_panel.new_version_requested.connect(self.new_version_requested.emit)

        self._sidebar_tabs = QTabWidget()
        self._sidebar_tabs.setObjectName("WorkspaceSidebarTabs")
        self._sidebar_tabs.addTab(sumario_container, "Sumário")
        self._sidebar_tabs.addTab(self._version_panel, "Histórico")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._sidebar_tabs)

    def bind_view_model(self, view_model) -> None:
        self._vm = view_model
        self._edit_view.section_field_changed.connect(view_model.update_section_field)
        self._edit_view.section_field_restore_requested.connect(view_model.restore_section_field)
        self._edit_view.section_block_restore_requested.connect(view_model.restore_section_block)
        self._edit_view.table_rows_changed.connect(view_model.update_section_table_rows)
        self._edit_view.table_rows_restore_requested.connect(view_model.restore_section_table_rows)
        self._edit_view.image_dropped.connect(self.image_dropped.emit)
        self._edit_view.tool_selected.connect(self.tool_selected.emit)
        self._edit_view.itens_medicao_changed.connect(view_model.update_itens_medicao)
        self._edit_view.section_restore_requested.connect(view_model.restore_section)
        self._dados_panel.field_changed.connect(view_model.update_parsed_field)
        self._dados_panel.restore_field_requested.connect(view_model.restore_parsed_field)

    def refresh_appearance(self) -> None:
        self._nav_dados_btn.refresh_appearance()
        self._sections_panel.refresh_appearance()
        self._edit_view.refresh_appearance()
        if hasattr(self._dados_panel, "refresh_appearance"):
            self._dados_panel.refresh_appearance()
        self._version_panel.refresh_appearance()

    def render_sections(self, sections: list[dict]) -> None:
        self._sections_map = {s["id"]: s for s in sections}
        self._sections_panel.render_sections(sections)
        if self._edit_view.isVisible() and self._active_section_id:
            if self._active_section_id in self._sections_map:
                self._refresh_edit_if_open()
            else:
                self._close_edit()

    def render_global_fields(self, values: dict[str, str], overridden: set[str]) -> None:
        self._global_values = values
        self._dados_panel.render_fields(values, overridden)
        if self._edit_view.isVisible() and self._active_section_id:
            if self._edit_view.has_pending_textarea():
                return
            self._refresh_edit_if_open()

    def set_itens_medicao(self, rows: list[dict[str, str]]) -> None:
        self._itens_medicao = rows
        if self._edit_view.isVisible():
            self._edit_view.set_itens_medicao(rows)

    def set_active_section(self, section_id: str) -> None:
        self._active_section_id = section_id
        self._sections_panel.set_active_section(section_id)

    def _on_section_navigated(self, section_id: str) -> None:
        self._active_section_id = section_id
        self._sections_panel.set_active_section(section_id)
        self.section_selected.emit(section_id)

    def _on_section_edit_requested(self, section_id: str) -> None:
        self._active_section_id = section_id
        self._sections_panel.set_active_section(section_id)
        section = self._sections_map.get(section_id, {"id": section_id, "title": section_id})
        overrides = self._collect_overrides(section)
        table_rows = section.get("table_rows")
        self._edit_view.open_section(
            section_id, section, overrides, table_rows, self._itens_medicao
        )
        self._edit_view.setVisible(True)
        self._show_sumario()
        self.section_selected.emit(section_id)

    def _collect_overrides(self, section: dict) -> dict[str, str]:
        return dict(section.get("fields") or {})

    def _refresh_edit_if_open(self) -> None:
        if not self._edit_view.isVisible() or self._active_section_id is None:
            return
        if self._edit_view.has_pending_textarea():
            return
        section = self._sections_map.get(self._active_section_id, {})
        self._edit_view.patch_section(
            self._collect_overrides(section),
            section.get("table_rows"),
            self._itens_medicao,
            section,
        )

    def open_edit_for_section(self, section_id: str) -> None:
        self._on_section_edit_requested(section_id)

    def _close_edit(self) -> None:
        self._edit_view.setVisible(False)
        self._edit_view.reset_breadcrumb()

    def _show_sumario(self) -> None:
        self._sumario_stack.setCurrentIndex(_INDEX_SUMARIO)

    def _show_dados(self) -> None:
        self._close_edit()
        self._sumario_stack.setCurrentIndex(_INDEX_DADOS)

    def render_images(self, images: list[ReportImage]) -> None:
        self._sections_panel.set_section_images(images)
        self._edit_view.render_images(images)

    def render_versions(self, entries) -> None:
        self._version_panel.render_history(entries)

    def set_source_attachments(self, paths: list[Path]) -> None:
        pass

    def update_document_context(self, document: ReportDocument | None) -> None:
        self._close_edit()
        if self._sumario_stack.currentIndex() == _INDEX_DADOS:
            self._show_sumario()
