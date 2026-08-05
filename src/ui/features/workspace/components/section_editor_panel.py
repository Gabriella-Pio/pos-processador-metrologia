"""Sidebar esquerda do workspace — sumário, dados globais e histórico."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QTabWidget, QVBoxLayout

from src.core.domain.ports import ReportDocument, ReportImage
from src.ui.components.panels import VersionHistoryPanel
from src.ui.features.workspace.components.dados_relatorio_panel import DadosRelatorioPanel
from src.ui.features.workspace.components.section_edit_view import SectionEditView
from src.ui.features.workspace.components.sections_panel import SectionsPanel


class SectionEditorPanel(QFrame):
    """Navegação lateral; edição de seção fica na coluna central do workspace."""

    section_selected = pyqtSignal(str)
    section_delete_requested = pyqtSignal(str)
    add_custom_section_requested = pyqtSignal()
    sections_reordered = pyqtSignal(list)
    new_version_requested = pyqtSignal()
    image_dropped = pyqtSignal(Path)
    image_remove_requested = pyqtSignal(object)
    image_caption_changed = pyqtSignal(object, str)
    image_selected = pyqtSignal(object)
    tool_selected = pyqtSignal(str)
    edit_visibility_changed = pyqtSignal(bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("WorkspaceSidebar")
        self._vm = None
        self._sections_map: dict[str, dict] = {}
        self._active_section_id: str | None = None
        self._itens_medicao: list[dict[str, str]] = []
        self._edit_open = False
        self._document_images: list[ReportImage] = []

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

        self._dados_panel = DadosRelatorioPanel()

        self._version_panel = VersionHistoryPanel()
        self._version_panel.new_version_requested.connect(self.new_version_requested.emit)

        self._sidebar_tabs = QTabWidget()
        self._sidebar_tabs.setObjectName("WorkspaceSidebarTabs")
        self._sidebar_tabs.addTab(self._sections_panel, "Sumário")
        self._sidebar_tabs.addTab(self._dados_panel, "Dados")
        self._sidebar_tabs.addTab(self._version_panel, "Histórico")
        self._sidebar_tabs.currentChanged.connect(self._on_sidebar_tab_changed)

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
        self._edit_view.section_field_changed.connect(view_model.update_section_field)
        self._edit_view.section_field_restore_requested.connect(view_model.restore_section_field)
        self._edit_view.table_rows_changed.connect(view_model.update_section_table_rows)
        self._edit_view.table_rows_restore_requested.connect(view_model.restore_section_table_rows)
        self._edit_view.image_dropped.connect(self.image_dropped.emit)
        self._edit_view.image_remove_requested.connect(self.image_remove_requested.emit)
        self._edit_view.image_caption_changed.connect(self.image_caption_changed.emit)
        self._edit_view.image_selected.connect(self.image_selected.emit)
        self._edit_view.tool_selected.connect(self.tool_selected.emit)
        self._edit_view.itens_medicao_changed.connect(view_model.update_itens_medicao)
        self._edit_view.section_restore_requested.connect(view_model.restore_section)
        self._dados_panel.field_changed.connect(view_model.update_parsed_field)
        self._dados_panel.restore_field_requested.connect(view_model.restore_parsed_field)

    def refresh_appearance(self) -> None:
        self._sections_panel.refresh_appearance()
        self._edit_view.refresh_appearance()
        self._dados_panel.refresh_appearance()
        self._version_panel.refresh_appearance()

    def render_sections(self, sections: list[dict]) -> None:
        self._sections_map = {s["id"]: s for s in sections}
        self._sections_panel.render_sections(sections)
        if self._edit_open and self._active_section_id:
            if self._active_section_id in self._sections_map:
                self._refresh_edit_if_open()
            else:
                self._close_edit()

    def render_global_fields(self, values: dict[str, str], overridden: set[str]) -> None:
        self._dados_panel.render_fields(values, overridden)
        if self._edit_open and self._active_section_id:
            if self._edit_view.has_pending_textarea():
                return
            self._refresh_edit_if_open()

    def set_itens_medicao(self, rows: list[dict[str, str]]) -> None:
        self._itens_medicao = rows
        if self._edit_open:
            self._edit_view.set_itens_medicao(rows)

    def set_active_section(self, section_id: str) -> None:
        self._active_section_id = section_id
        self._sections_panel.set_active_section(section_id)

    def _on_section_navigated(self, section_id: str) -> None:
        self._close_edit()
        self._active_section_id = section_id
        self._sections_panel.set_active_section(section_id)
        self.section_selected.emit(section_id)

    def _on_section_edit_requested(self, section_id: str) -> None:
        if self._sidebar_tabs.currentIndex() != 0:
            self._sidebar_tabs.setCurrentIndex(0)
        self._active_section_id = section_id
        self._sections_panel.set_active_section(section_id)
        section = self._sections_map.get(section_id, {"id": section_id, "title": section_id})
        overrides = dict(section.get("fields") or {})
        self._edit_view.open_section(
            section_id,
            section,
            overrides,
            section.get("table_rows"),
            self._itens_medicao,
        )
        # Reaplica filtro de fotos da seção aberta (evita lista da seção anterior).
        self._edit_view.render_images(self._document_images)
        self._edit_open = True
        self._show_sumario_tab()
        self.edit_visibility_changed.emit(True)
        self.section_selected.emit(section_id)

    def _refresh_edit_if_open(self) -> None:
        if not self._edit_open or self._active_section_id is None:
            return
        # Não sobrescreve campos enquanto o usuário digita (preview/summary refresh).
        if self._edit_view.has_pending_textarea() or self._edit_view.has_focused_editor():
            return
        section = self._sections_map.get(self._active_section_id, {})
        self._edit_view.patch_section(
            dict(section.get("fields") or {}),
            section.get("table_rows"),
            self._itens_medicao,
            section,
        )

    def navigate_to_section(self, section_id: str) -> None:
        """Seleção no preview — navega sem abrir o editor."""
        self._on_section_navigated(section_id)

    def open_edit_for_section(self, section_id: str) -> None:
        self._on_section_edit_requested(section_id)

    def _close_edit(self) -> None:
        if not self._edit_open:
            return
        self._edit_open = False
        self._edit_view.reset_breadcrumb()
        self.edit_visibility_changed.emit(False)

    def _show_sumario_tab(self) -> None:
        self._sidebar_tabs.setCurrentIndex(0)

    def _on_sidebar_tab_changed(self, index: int) -> None:
        if index != 0:
            self._close_edit()

    def render_images(self, images: list[ReportImage]) -> None:
        self._document_images = list(images)
        self._sections_panel.set_section_images(images)
        self._edit_view.render_images(images)

    def editing_section_id(self) -> str | None:
        """Seção cujo editor está aberto (fonte de verdade para associar fotos)."""
        if not self._edit_open:
            return None
        return self._edit_view.current_section_id()

    def render_versions(self, entries) -> None:
        self._version_panel.render_history(entries)

    def set_source_attachments(self, paths: list[Path]) -> None:
        """Recebe os PDFs de origem do projeto (seção Anexos usa o documento ativo)."""
        self._source_attachment_paths = list(paths or [])

    def update_document_context(self, document: ReportDocument | None) -> None:
        self._close_edit()
        self._show_sumario_tab()
