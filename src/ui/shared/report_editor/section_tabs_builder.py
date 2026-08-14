"""Montagem dinâmica de abas do editor de seção."""
from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtWidgets import QScrollArea, QTabWidget, QVBoxLayout, QWidget

from src.core.application.template_media import (
    sanitize_workspace_media_kinds,
    workspace_addable_media_kinds,
)
from src.core.domain.report_field_registry import effective_media_kinds, get_media_blocks
from src.core.domain.section_schema import is_custom_section_id
from src.core.domain.table_row_registry import TABLE_SECTIONS, uses_table_rows_editor
from src.ui.components.icons import icon_chart, icon_edit, icon_image, icon_table
from src.ui.shared.report_editor.template_layout_panel import TemplateLayoutPanel


@dataclass
class SectionTabPages:
    content_scroll: QScrollArea
    layout_panel: TemplateLayoutPanel
    photos_page: QWidget
    graphics_page: QWidget
    tables_page: QWidget
    tables_layout: QVBoxLayout
    table_rows_editor: QWidget
    medicoes_editor: QWidget


class SectionTabsBuilder:
    def rebuild(
        self,
        tabs: QTabWidget,
        *,
        section_id: str,
        section_overrides: dict,
        defaults_mode: bool,
        pages: SectionTabPages,
        locked_media_kinds: list[str] | None = None,
    ) -> None:
        while tabs.count():
            tabs.removeTab(0)

        tabs.addTab(pages.content_scroll, "Conteúdo")
        tabs.setTabIcon(0, icon_edit())

        available_media = get_media_blocks(section_id)
        if defaults_mode:
            pages.layout_panel.set_workspace_mode(False)
            pages.layout_panel.set_locked_kinds([])
            pages.layout_panel.set_kinds(
                effective_media_kinds(section_id, section_overrides)
            )
            if section_id in TABLE_SECTIONS and "tables" in pages.layout_panel.current_kinds():
                pages.layout_panel.set_table_widget(pages.table_rows_editor)
            else:
                pages.layout_panel.set_table_widget(None)
            layout_index = tabs.addTab(pages.layout_panel, "Layout")
            tabs.setTabIcon(layout_index, icon_image())
            tabs.tabBar().setVisible(True)
            return

        locked = list(locked_media_kinds or [])
        effective_kinds = effective_media_kinds(section_id, section_overrides)
        if not defaults_mode:
            effective_kinds = sanitize_workspace_media_kinds(section_id, locked, effective_kinds)

        if available_media or (not defaults_mode and not is_custom_section_id(section_id)):
            pages.layout_panel.set_workspace_mode(not defaults_mode)
            pages.layout_panel.set_locked_kinds([] if defaults_mode else locked)
            pages.layout_panel.set_addable_kinds(
                ["photos", "graphics", "tables"] if defaults_mode
                else workspace_addable_media_kinds(section_id)
            )
            pages.layout_panel.set_kinds(effective_kinds)
            pages.layout_panel.set_table_widget(None)
            layout_index = tabs.addTab(pages.layout_panel, "Layout")
            tabs.setTabIcon(layout_index, icon_image())

        media_blocks = get_media_blocks(
            section_id,
            effective_kinds,
        )
        tab_defs: list[tuple[str, str, QWidget]] = []
        for media in media_blocks:
            if media.kind == "photos":
                tab_defs.append(("photos", "Fotografias", pages.photos_page))
            elif media.kind == "graphics":
                tab_defs.append(("graphics", "Gráficos", pages.graphics_page))
            elif media.kind == "tables":
                while pages.tables_layout.count():
                    item = pages.tables_layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.setParent(None)
                if section_id == "resultados":
                    pages.tables_layout.addWidget(pages.medicoes_editor, 0)
                elif uses_table_rows_editor(section_id):
                    pages.tables_layout.addWidget(pages.table_rows_editor, 0)
                pages.tables_layout.addStretch(1)
                tab_defs.append(("tables", "Tabela", pages.tables_page))

        icons = {"photos": icon_image, "graphics": icon_chart, "tables": icon_table}
        labels = {"photos": "Fotografias", "graphics": "Gráficos", "tables": "Tabela"}
        seen: set[str] = set()
        for kind, _label, page in tab_defs:
            if kind in seen:
                continue
            seen.add(kind)
            index = tabs.addTab(page, labels.get(kind, kind))
            tabs.setTabIcon(index, icons[kind]())

        tabs.tabBar().setVisible(tabs.count() > 1)
