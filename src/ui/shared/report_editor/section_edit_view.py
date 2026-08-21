"""Formulário de edição de seção — fachada sobre abas Conteúdo / Layout / Fotos / Gráficos / Tabela."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QWidget,
    QTabWidget,
)

from src.core.domain.chart_figure_defs import chart_figure_defs
from src.core.domain.report_field_registry import get_media_blocks
from src.core.application.interpretacao_edit import interpretacao_field_defs
from src.core.domain.ports import ReportImage, VersionEntry
from src.core.domain.table_row_registry import TABLE_SECTIONS, uses_table_rows_editor
from src.ui.components.buttons import IconButton
from src.ui.components.modal_presentation import present_modal_dialog
from src.ui.components.icons import icon_close, icon_help
from src.ui.shared.report_editor.sidebar_chrome import editor_panel_header
from src.ui.styles import SPACING, sidebar_panel_style
from src.ui.shared.report_editor.section_help_dialog import SectionHelpDialog
from src.ui.shared.report_editor.draggable_table_rows_editor import DraggableTableRowsEditor
from src.ui.shared.report_editor.section_tabs_builder import SectionTabPages, SectionTabsBuilder
from src.ui.shared.report_editor.template_layout_panel import TemplateLayoutPanel
from src.ui.shared.report_editor.section_content_tab import SectionContentTab
from src.ui.shared.report_editor.section_graphics_tab import SectionGraphicsTab
from src.ui.shared.report_editor.section_photos_tab import SectionPhotosTab
from src.ui.features.workspace.components.edit_help import build_help_text
from src.ui.features.workspace.components.medicoes_table_editor import MedicoesTableEditor


class SectionEditView(QFrame):
    back_requested = pyqtSignal()
    section_field_changed = pyqtSignal(str, str, str)
    section_field_restore_requested = pyqtSignal(str, str)
    table_rows_changed = pyqtSignal(str, list)
    table_rows_restore_requested = pyqtSignal(str)
    itens_medicao_changed = pyqtSignal(list)
    itens_medicao_restore_requested = pyqtSignal()
    image_dropped = pyqtSignal(Path)
    image_remove_requested = pyqtSignal(object)
    image_caption_changed = pyqtSignal(object, str)
    image_selected = pyqtSignal(object)
    image_edits_changed = pyqtSignal(object)
    bosello_picker_requested = pyqtSignal()
    tool_selected = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    section_restore_requested = pyqtSignal(str)
    media_kinds_changed = pyqtSignal(str, list)
    disabled_chart_ids_changed = pyqtSignal(str, list)
    manage_versions_requested = pyqtSignal()
    catalog_section_chosen = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("WorkspaceEditorView")
        self._section_id: str | None = None
        self._loading = False
        self._defaults_mode = False
        self._section_overrides: dict = {}
        self._locked_media_kinds: list[str] = []

        header, self._header_title, actions_host = editor_panel_header()
        actions_layout = actions_host.layout()

        self._close_btn = IconButton(icon_close(), "Fechar edição")
        self._close_btn.clicked.connect(self.back_requested.emit)
        self._help_btn = IconButton(icon_help(), "Ajuda desta seção")
        self._help_btn.clicked.connect(self._show_help)
        actions_layout.addWidget(self._help_btn)
        actions_layout.addWidget(self._close_btn)

        self._content_tab = SectionContentTab()
        self._content_tab.section_field_changed.connect(self.section_field_changed.emit)
        self._content_tab.section_field_restore_requested.connect(
            self.section_field_restore_requested.emit
        )
        self._content_tab.section_restore_requested.connect(self.section_restore_requested.emit)
        self._content_tab.delete_requested.connect(self.delete_requested.emit)
        self._content_tab.catalog_section_chosen.connect(self.catalog_section_chosen.emit)
        self._content_tab.manage_versions_requested.connect(self.manage_versions_requested.emit)

        self._photos_tab = SectionPhotosTab()
        self._photos_tab.image_dropped.connect(self.image_dropped.emit)
        self._photos_tab.image_remove_requested.connect(self.image_remove_requested.emit)
        self._photos_tab.image_caption_changed.connect(self.image_caption_changed.emit)
        self._photos_tab.image_selected.connect(self.image_selected.emit)
        self._photos_tab.image_edits_changed.connect(self.image_edits_changed.emit)
        self._photos_tab.bosello_picker_requested.connect(self.bosello_picker_requested.emit)

        self._graphics_tab = SectionGraphicsTab()
        self._graphics_tab.disabled_chart_ids_changed.connect(self._on_disabled_chart_ids)

        self._table_rows_editor = DraggableTableRowsEditor(
            "Linhas da tabela (como no preview)",
            allow_add_remove=True,
        )
        self._table_rows_editor.rows_changed.connect(self._on_table_rows_changed)
        self._table_rows_editor.restore_requested.connect(self._on_table_rows_restore)

        self._medicoes_editor = MedicoesTableEditor()
        self._medicoes_editor.rows_changed.connect(self.itens_medicao_changed.emit)
        self._medicoes_editor.restore_requested.connect(self.itens_medicao_restore_requested.emit)

        self._tables_page = QWidget()
        self._tables_layout = QVBoxLayout(self._tables_page)
        self._tables_layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        self._tables_layout.setSpacing(SPACING.sm)
        self._tables_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._layout_panel = TemplateLayoutPanel()
        self._layout_panel.kinds_changed.connect(self._on_template_media_kinds_changed)
        self._layout_panel.blocked_action.connect(self._on_layout_blocked)
        self._tabs_builder = SectionTabsBuilder()

        self._tabs = QTabWidget()
        self._tabs.setObjectName("SectionEditorTabs")
        self._tabs.currentChanged.connect(self._on_editor_tab_changed)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(header)
        outer.addWidget(self._tabs, stretch=1)

    def set_defaults_mode(self, enabled: bool) -> None:
        self._defaults_mode = enabled
        self._content_tab.set_defaults_mode(enabled)
        self._graphics_tab.set_defaults_mode(enabled)
        self._close_btn.setToolTip("Fechar edição" if not enabled else "Voltar ao sumário")

    def set_catalog_origin_options(self, options: list[dict[str, str]]) -> None:
        self._content_tab.set_catalog_origin_options(options)

    def reset_breadcrumb(self) -> None:
        self._header_title.setText("EDITAR SEÇÃO")

    def has_focused_editor(self) -> bool:
        if self._content_tab.has_focused_editor():
            return True
        if self._photos_tab.is_caption_editing():
            return True
        if self._table_rows_editor.has_focused_editor():
            return True
        if self._medicoes_editor.has_focused_editor():
            return True
        return False

    def has_pending_textarea(self) -> bool:
        return (
            self._content_tab.has_pending_textarea()
            or self._table_rows_editor.has_pending_emit()
            or self._medicoes_editor.has_pending_emit()
        )

    def should_force_patch(self) -> bool:
        return self._content_tab.should_force_patch()

    def refresh_appearance(self) -> None:
        self.setStyleSheet(sidebar_panel_style())
        self._close_btn.refresh_appearance()
        self._help_btn.refresh_appearance()
        self._content_tab.refresh_action_buttons()
        self._photos_tab.refresh_appearance()

    def open_section(
        self,
        section_id: str,
        section: dict,
        overrides: dict,
        table_rows: list[dict[str, str]] | None = None,
        itens_medicao: list[dict[str, str]] | None = None,
        version_entries: list[VersionEntry] | None = None,
        locked_media_kinds: list[str] | None = None,
    ) -> None:
        if (
            self._section_id == section_id
            and self._content_tab.field_widgets
            and not self._needs_field_rebuild(section_id, overrides)
        ):
            self.patch_section(overrides, table_rows, itens_medicao, section)
            return
        self._loading = True
        self._content_tab.set_loading(True)
        self._graphics_tab.set_loading(True)
        self._section_id = section_id
        self._section_overrides = dict(overrides)
        if version_entries is not None:
            self._content_tab.set_version_entries(version_entries)
        if locked_media_kinds is not None:
            self._locked_media_kinds = list(locked_media_kinds)

        self._photos_tab.set_section_id(section_id)
        self._photos_tab.clear_images()
        is_custom = section.get("custom", False) or section_id.startswith("custom_")
        scroll_pos = self._content_tab.open_content(section_id, overrides, is_custom=is_custom)
        self._rebuild_table_rows(section_id, table_rows or [])
        self._rebuild_editor_tabs(section_id)
        self._photos_tab.update_hint(section)
        self._graphics_tab.rebuild(section_id, overrides)

        if section_id == "resultados" and itens_medicao is not None:
            self._medicoes_editor.set_rows(itens_medicao)
        self._loading = False
        self._content_tab.set_loading(False)
        self._graphics_tab.set_loading(False)
        self._content_tab.restore_scroll(scroll_pos)
        self._update_breadcrumb(section)

    def _needs_field_rebuild(self, section_id: str, overrides: dict) -> bool:
        if section_id == "interpretacao":
            expected = {f.key for f in interpretacao_field_defs(overrides)}
            current = set(self._content_tab.field_widgets.keys())
            return expected != current
        return False

    def patch_section(
        self,
        overrides: dict,
        table_rows: list[dict[str, str]] | None = None,
        itens_medicao: list[dict[str, str]] | None = None,
        section: dict | None = None,
    ) -> None:
        if self._section_id is None:
            return
        force = self._content_tab.consume_force_patch()
        if self._needs_field_rebuild(self._section_id, overrides):
            self.open_section(
                self._section_id,
                section or {"id": self._section_id},
                overrides,
                table_rows,
                itens_medicao,
            )
            return
        self._loading = True
        self._content_tab.set_loading(True)
        self._graphics_tab.set_loading(True)
        scroll_pos = self._content_tab.scroll_position()
        section_id = self._section_id
        prev_disabled = set(self._section_overrides.get("disabled_chart_ids") or [])
        prev_media = list(self._section_overrides.get("media_kinds") or [])
        self._section_overrides = dict(overrides)
        self._content_tab.patch_fields(section_id, overrides, force=force)

        if uses_table_rows_editor(section_id) and table_rows is not None:
            from src.core.application.statistical_aggregator import (
                ESTAT_EDITOR_VALUE_COLUMNS,
                tipo_from_estat_section_id,
            )

            if tipo_from_estat_section_id(section_id):
                self._table_rows_editor.set_value_columns(ESTAT_EDITOR_VALUE_COLUMNS)
            else:
                self._table_rows_editor.set_value_columns(())
            self._table_rows_editor.set_rows(table_rows)
        if section_id == "resultados" and itens_medicao is not None:
            self._medicoes_editor.set_rows(itens_medicao)

        if section is not None:
            self._update_breadcrumb(section)
        if chart_figure_defs(section_id):
            new_disabled = set(self._section_overrides.get("disabled_chart_ids") or [])
            new_media = list(self._section_overrides.get("media_kinds") or prev_media)
            if new_disabled != prev_disabled or new_media != prev_media:
                self._graphics_tab.rebuild(section_id, self._section_overrides)
        self._loading = False
        self._content_tab.set_loading(False)
        self._graphics_tab.set_loading(False)
        self._content_tab.restore_scroll(scroll_pos)

    def _update_breadcrumb(self, section: dict) -> None:
        _ = section
        self._header_title.setText("EDITAR SEÇÃO")

    def set_itens_medicao(self, rows: list[dict[str, str]]) -> None:
        if self._section_id == "resultados":
            self._medicoes_editor.set_rows(rows)

    def _rebuild_table_rows(self, section_id: str, rows: list[dict[str, str]]) -> None:
        if not uses_table_rows_editor(section_id):
            self._table_rows_editor.set_value_columns(())
            self._table_rows_editor.set_rows([])
            return
        from src.core.application.statistical_aggregator import (
            ESTAT_EDITOR_VALUE_COLUMNS,
            tipo_from_estat_section_id,
        )

        if tipo_from_estat_section_id(section_id):
            self._table_rows_editor.set_value_columns(ESTAT_EDITOR_VALUE_COLUMNS)
        else:
            self._table_rows_editor.set_value_columns(())
        self._table_rows_editor.set_rows(rows)

    def set_locked_media_kinds(self, kinds: list[str]) -> None:
        self._locked_media_kinds = list(kinds)
        if self._section_id is not None:
            self._rebuild_editor_tabs(self._section_id)

    def set_version_entries(self, entries: list[VersionEntry]) -> None:
        self._content_tab.set_version_entries(entries)
        self._content_tab.set_section_overrides(self._section_overrides)
        if self._section_id == "historico_versoes" and not self._defaults_mode:
            self._content_tab.rebuild_version_history_fields()

    def _rebuild_editor_tabs(self, section_id: str) -> None:
        self._tabs_builder.rebuild(
            self._tabs,
            section_id=section_id,
            section_overrides=self._section_overrides,
            defaults_mode=self._defaults_mode,
            pages=SectionTabPages(
                content_scroll=self._content_tab.scroll_area,
                layout_panel=self._layout_panel,
                photos_page=self._photos_tab,
                graphics_page=self._graphics_tab,
                tables_page=self._tables_page,
                tables_layout=self._tables_layout,
                table_rows_editor=self._table_rows_editor,
                medicoes_editor=self._medicoes_editor,
            ),
            locked_media_kinds=self._locked_media_kinds,
        )

    def _on_layout_blocked(self, message: str) -> None:
        self._layout_panel.show_blocked_notice(message)

    def _on_template_media_kinds_changed(self, kinds: list[str]) -> None:
        if self._section_id is None:
            return
        if self._defaults_mode and self._section_id in TABLE_SECTIONS:
            if "tables" in kinds:
                self._layout_panel.set_table_widget(self._table_rows_editor)
            else:
                self._layout_panel.set_table_widget(None)
        if not self._defaults_mode:
            removed_locked = set(self._locked_media_kinds) - set(kinds)
            if removed_locked:
                self._layout_panel.show_blocked_notice(
                    "Este bloco faz parte do layout padrão da seção e não pode ser desativado aqui. "
                    "Para um relatório diferente, crie uma seção personalizada."
                )
                kinds = list(dict.fromkeys([*self._locked_media_kinds, *kinds]))
        self.media_kinds_changed.emit(self._section_id, kinds)
        if not self._defaults_mode:
            merged = list(dict.fromkeys([*self._locked_media_kinds, *kinds]))
            self._section_overrides = dict(self._section_overrides)
            self._section_overrides["media_kinds"] = merged
            self._rebuild_editor_tabs(self._section_id)

    def _on_disabled_chart_ids(self, section_id: str, disabled: list) -> None:
        self.disabled_chart_ids_changed.emit(section_id, disabled)
        self._section_overrides = dict(self._section_overrides)
        self._section_overrides["disabled_chart_ids"] = list(disabled)

    def _show_help(self) -> None:
        section_id = self._section_id or ""
        blocks = get_media_blocks(section_id)
        text = build_help_text(
            section_id,
            has_table=any(b.kind == "tables" for b in blocks),
            has_media=any(b.kind in ("photos", "graphics") for b in blocks),
        )
        dialog = SectionHelpDialog(text, self)
        present_modal_dialog(self, dialog)

    def current_section_id(self) -> str | None:
        return self._section_id

    def focus_tab_for_kind(self, kind: str) -> None:
        targets = {
            "content": self._content_tab.scroll_area,
            "layout": self._layout_panel,
            "photos": self._photos_tab,
            "graphics": self._graphics_tab,
            "tables": self._tables_page,
        }
        widget = targets.get(kind)
        if widget is None:
            return
        index = self._tabs.indexOf(widget)
        if index >= 0:
            self._tabs.setCurrentIndex(index)

    def _on_editor_tab_changed(self, index: int) -> None:
        if index < 0:
            return
        if self._tabs.widget(index) is self._photos_tab:
            self._photos_tab.schedule_list_layout_sync()

    def focus_section_title(self) -> None:
        content_index = self._tabs.indexOf(self._content_tab.scroll_area)
        if content_index >= 0:
            self._tabs.setCurrentIndex(content_index)
        QTimer.singleShot(80, self._content_tab.focus_section_title_editor)

    def render_images(self, images: list[ReportImage]) -> None:
        self._photos_tab.set_section_id(self._section_id)
        self._photos_tab.render_images(images)

    def set_bosello_captures_available(self, available: bool) -> None:
        self._photos_tab.set_bosello_captures_available(available)

    def _on_table_rows_changed(self, rows: list) -> None:
        if self._loading or self._section_id is None:
            return
        self.table_rows_changed.emit(self._section_id, rows)

    def _on_table_rows_restore(self) -> None:
        if self._section_id is not None:
            self.table_rows_restore_requested.emit(self._section_id)
