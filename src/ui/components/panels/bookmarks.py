"""Sumário interativo do relatório (sidebar esquerda)."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QLabel, QLineEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from src.ui.components.panels._chrome import section_header
from src.ui.styles import SPACING, caption_style, sidebar_panel_style
from src.ui.styles.helpers import workspace_bookmark_search_style, workspace_bookmark_tree_style


class BookmarksPanel(QFrame):
    """Sumário interativo do relatório (sidebar esquerda)."""

    section_selected = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("WorkspaceSidebarPanel")

        self._sections: list[dict] = []
        self._active_section_id: str | None = None

        self._search = QLineEdit()
        self._search.setPlaceholderText("Filtrar seção…")
        self._search.textChanged.connect(self._apply_filter)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setColumnCount(1)
        self._tree.setIndentation(16)
        self._tree.setUniformRowHeights(True)
        self._tree.itemClicked.connect(
            lambda item, _col: self.section_selected.emit(item.data(0, Qt.ItemDataRole.UserRole))
        )

        self._hint = QLabel("Clique em uma seção para navegar e associar fotografias.")
        self._hint.setObjectName("SidebarHint")
        self._hint.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(section_header("Sumário"))

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(SPACING.md, SPACING.xs, SPACING.md, SPACING.md)
        inner_layout.setSpacing(SPACING.sm)
        inner_layout.addWidget(self._hint)
        inner_layout.addWidget(self._search)
        inner_layout.addWidget(self._tree)
        layout.addWidget(inner, stretch=1)

        self.refresh_appearance()

    def refresh_appearance(self) -> None:
        self.setStyleSheet(sidebar_panel_style())
        self._search.setStyleSheet(workspace_bookmark_search_style())
        self._tree.setStyleSheet(workspace_bookmark_tree_style())
        self._hint.setStyleSheet(caption_style())

    def render_sections(self, sections: list[dict]) -> None:
        self._sections = sections
        self._apply_filter(self._search.text())

    def set_active_section(self, section_id: str | None) -> None:
        self._active_section_id = section_id
        if section_id is None:
            self._tree.clearSelection()
            return
        item = self._find_item_by_id(self._tree.invisibleRootItem(), section_id)
        if item is not None:
            self._tree.setCurrentItem(item)
            self._tree.scrollToItem(item)

    def _apply_filter(self, text: str) -> None:
        filtro = text.strip().lower()
        self._tree.clear()
        for section in self._sections:
            item = self._build_section_item(section, filtro)
            if item is not None:
                self._tree.invisibleRootItem().addChild(item)
        self._tree.expandAll()
        self.set_active_section(self._active_section_id)

    def _build_section_item(self, section: dict, filtro: str) -> QTreeWidgetItem | None:
        children = section.get("children", [])
        child_items: list[QTreeWidgetItem] = []
        for child in children:
            child_item = self._build_section_item(child, filtro)
            if child_item is not None:
                child_items.append(child_item)

        title = section["title"]
        image_count = int(section.get("image_count", 0) or 0)
        count_text = f"  {image_count} foto{'s' if image_count != 1 else ''}" if image_count > 0 else "  —"
        section_text = f"{title}{count_text}"

        matches_self = filtro in title.lower() or filtro in section.get("id", "").lower()
        if filtro and not matches_self and not child_items:
            return None

        item = QTreeWidgetItem([section_text])
        item.setData(0, Qt.ItemDataRole.UserRole, section["id"])
        item.setToolTip(0, title)

        if section.get("id") == self._active_section_id:
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)

        for child_item in child_items:
            item.addChild(child_item)
        return item

    def _find_item_by_id(self, parent_item, section_id: str):
        for index in range(parent_item.childCount()):
            item = parent_item.child(index)
            if item.data(0, Qt.ItemDataRole.UserRole) == section_id:
                return item
            found = self._find_item_by_id(item, section_id)
            if found is not None:
                return found
        return None
