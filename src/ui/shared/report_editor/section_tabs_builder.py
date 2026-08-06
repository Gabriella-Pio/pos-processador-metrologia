"""Montagem dinâmica de abas do editor de seção."""
from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtWidgets import QScrollArea, QTabWidget, QVBoxLayout, QWidget

from src.core.domain.report_field_registry import effective_media_kinds, get_media_blocks
from src.core.domain.table_row_registry import TABLE_SECTIONS
from src.core.domain.section_schema import is_custom_section_id
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
    annotation_toolbar: QWidget


class SectionTabsBuilder:
    def rebuild(
        self,
        tabs: QTabWidget,
        *,
        section_id: str,
        section_overrides: dict,
        defaults_mode: bool,
        pages: SectionTabPages,
    ) -> None:
        while tabs.count():
            tabs.removeTab(0)

        tabs.addTab(pages.content_scroll, "Conteúdo")
        tabs.setTabIcon(0, icon_edit())

        if defaults_mode:
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

        media_blocks = get_media_blocks(
            section_id,
            effective_media_kinds(section_id, section_overrides),
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
                if section_id in TABLE_SECTIONS or is_custom_section_id(section_id):
                    pages.tables_layout.addWidget(pages.table_rows_editor, 0)
                else:
                    pages.tables_layout.addWidget(pages.medicoes_editor, 0)
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

        has_photos = any(b.kind == "photos" for b in media_blocks)
        pages.annotation_toolbar.setVisible(has_photos)
        tabs.tabBar().setVisible(tabs.count() > 1)
