"""
Painéis reutilizáveis das sidebars do Workspace — dark edition.

BookmarksPanel      → sumário interativo com árvore estilizada
ImageManagerPanel   → drop zone animada com lista de imagens
AnnotationToolbar   → ferramentas de marcação com botões toggle
VersionHistoryPanel → histórico com timeline visual (border-left colorida)
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.domain.ports import ReportImage, VersionEntry
from src.ui.components.icons import app_icon
from src.ui.shared.report_editor.sidebar_chrome import sidebar_section_header
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, sidebar_panel_style
from src.ui.styles.helpers import (
    caption_style,
    workspace_annotation_button_style,
    workspace_annotation_toolbar_style,
    workspace_bookmark_search_style,
    workspace_bookmark_tree_style,
    workspace_drop_hint_style,
    workspace_image_list_style,
    workspace_version_entry_style,
)


def _section_header(title: str) -> QWidget:
    return sidebar_section_header(title)


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
        layout.addWidget(_section_header("Sumário"))

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


class ImageManagerPanel(QFrame):
    """Gerenciador de imagens por drag-and-drop (sidebar direita, topo)."""

    image_dropped = pyqtSignal(Path)
    image_selected = pyqtSignal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._drop_active = False

        self._list = QListWidget()
        self._list.itemClicked.connect(
            lambda item: self.image_selected.emit(item.data(Qt.ItemDataRole.UserRole))
        )

        self._drop_hint = QLabel("Arraste imagens PNG/JPG\npara associar à seção ativa")
        self._drop_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._drop_hint.setWordWrap(True)

        self._hint = QLabel("Arraste imagens aqui ou clique na lista para selecionar.")
        self._hint.setObjectName("SidebarHint")
        self._hint.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(_section_header("Fotografias"))

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(SPACING.sm, SPACING.xs, SPACING.sm, SPACING.sm)
        inner_layout.setSpacing(SPACING.sm)
        inner_layout.addWidget(self._hint)
        inner_layout.addWidget(self._drop_hint)
        inner_layout.addWidget(self._list, stretch=1)
        layout.addWidget(inner, stretch=1)

        self.refresh_appearance()

    def refresh_appearance(self) -> None:
        self.setStyleSheet(sidebar_panel_style())
        self._list.setStyleSheet(workspace_image_list_style())
        self._hint.setStyleSheet(caption_style())
        self._apply_drop_hint_style()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            self._drop_active = True
            self._apply_drop_hint_style()
            event.acceptProposedAction()

    def dragLeaveEvent(self, event) -> None:
        self._drop_active = False
        self._apply_drop_hint_style()

    def dropEvent(self, event: QDropEvent) -> None:
        self._drop_active = False
        self._apply_drop_hint_style()
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() in (".png", ".jpg", ".jpeg"):
                self.image_dropped.emit(path)
        event.acceptProposedAction()

    def _apply_drop_hint_style(self) -> None:
        self._drop_hint.setStyleSheet(workspace_drop_hint_style(active=self._drop_active))

    def render_images(self, images: list[ReportImage]) -> None:
        self._list.clear()
        self._drop_hint.setVisible(len(images) == 0)
        self._list.setVisible(len(images) > 0)
        for image in images:
            item = QListWidgetItem(f"  {image.image_path.name}")
            item.setData(Qt.ItemDataRole.UserRole, image)
            self._list.addItem(item)


class AnnotationToolbar(QFrame):
    """Barra de ferramentas de anotação: seta, círculo, caixa de texto, numeração."""

    tool_selected = pyqtSignal(str)

    _TOOLS = (
        ("arrow", "arrow-right", "Seta direcional"),
        ("circle", "circle", "Círculo de destaque"),
        ("text_box", "square", "Caixa de texto"),
        ("number", "list-ol", "Numeração sequencial"),
    )

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.sm)

        self._title = QLabel("Marcações:")
        layout.addWidget(self._title)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._tool_buttons: list[QPushButton] = []
        self._build_tool_buttons(layout)
        layout.addStretch(1)

        self.refresh_appearance()

    def _build_tool_buttons(self, layout: QHBoxLayout) -> None:
        for tool_id, icon_name, tooltip in self._TOOLS:
            button = QPushButton()
            button.setCheckable(True)
            button.setToolTip(tooltip)
            button.setFixedSize(32, 32)
            button.setProperty("tool_id", tool_id)
            button.setProperty("icon_name", icon_name)
            button.clicked.connect(lambda _checked, t=tool_id: self.tool_selected.emit(t))
            self._group.addButton(button)
            self._tool_buttons.append(button)
            layout.addWidget(button)

    def refresh_appearance(self) -> None:
        p = PALETTE
        self.setStyleSheet(workspace_annotation_toolbar_style())
        self._title.setStyleSheet(
            f"color: {p.text_muted}; font-size: {TYPOGRAPHY.size_caption}px; "
            f"font-weight: {TYPOGRAPHY.weight_semibold}; letter-spacing: 0.5px; background: transparent;"
        )
        button_style = workspace_annotation_button_style()
        for button in self._tool_buttons:
            icon_name = button.property("icon_name")
            button.setIcon(app_icon(str(icon_name), color=p.text_secondary))
            button.setStyleSheet(button_style)


class _VersionEntryWidget(QWidget):
    """Mini-card de versão com timeline visual (border-left colorida)."""

    def __init__(self, entry: VersionEntry, is_latest: bool = False, parent=None) -> None:
        super().__init__(parent)
        self._entry = entry
        self._is_latest = is_latest

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.sm)

        self._line = QFrame()
        self._line.setFixedWidth(3)
        self._line.setMinimumHeight(32)
        layout.addWidget(self._line, 0, Qt.AlignmentFlag.AlignTop)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)
        content_layout.setContentsMargins(0, 0, 0, 0)

        header_row = QHBoxLayout()
        self._version_label = QLabel(f"v{entry.version_number}")
        self._responsible_label = QLabel(f"  {entry.responsible_name}")
        header_row.addWidget(self._version_label)
        header_row.addWidget(self._responsible_label)
        header_row.addStretch()
        content_layout.addLayout(header_row)

        self._meta = QLabel(
            f"{entry.timestamp.strftime('%d/%m/%Y %H:%M')}  ·  {entry.description}"
        )
        self._meta.setWordWrap(True)
        content_layout.addWidget(self._meta)

        layout.addLayout(content_layout, stretch=1)
        self.refresh_appearance()

    def refresh_appearance(self) -> None:
        p = PALETTE
        accent_color = p.senai_orange if self._is_latest else p.senai_blue_light
        self._line.setStyleSheet(
            f"background-color: {accent_color}; border-radius: 2px;"
        )
        self._version_label.setStyleSheet(
            f"color: {accent_color}; font-size: {TYPOGRAPHY.size_caption}px; "
            f"font-weight: {TYPOGRAPHY.weight_bold}; background: transparent;"
        )
        self._responsible_label.setStyleSheet(
            f"color: {p.text_primary}; font-size: {TYPOGRAPHY.size_caption}px; "
            f"font-weight: {TYPOGRAPHY.weight_medium}; background: transparent;"
        )
        self._meta.setStyleSheet(
            f"color: {p.text_muted}; font-size: 10px; background: transparent;"
        )
        self.setStyleSheet(workspace_version_entry_style(is_latest=self._is_latest))


class VersionHistoryPanel(QFrame):
    """Histórico de versões com timeline visual em tempo real."""

    new_version_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._entries: list[VersionEntry] = []

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._content = QWidget()
        self._layout = QVBoxLayout(self._content)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addStretch()
        self._scroll.setWidget(self._content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(_section_header("Histórico de Versões"))
        outer.addWidget(self._scroll, stretch=1)

        from src.ui.components.buttons import PrimaryButton

        self._new_version_btn = PrimaryButton("Nova versão")
        self._new_version_btn.clicked.connect(self.new_version_requested.emit)
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        btn_row.addStretch(1)
        btn_row.addWidget(self._new_version_btn)
        outer.addLayout(btn_row)

        self.refresh_appearance()

    def refresh_appearance(self) -> None:
        self.setStyleSheet(sidebar_panel_style())
        self._scroll.setStyleSheet("background: transparent;")
        self._content.setStyleSheet("background: transparent;")
        if hasattr(self, "_new_version_btn"):
            self._new_version_btn.refresh_appearance()
        for index in range(self._layout.count() - 1):
            widget = self._layout.itemAt(index).widget()
            if widget is not None and hasattr(widget, "refresh_appearance"):
                widget.refresh_appearance()

    def render_history(self, entries: list[VersionEntry]) -> None:
        self._entries = list(entries)
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for i, entry in enumerate(reversed(entries)):
            is_latest = i == 0
            widget = _VersionEntryWidget(entry, is_latest=is_latest)
            self._layout.insertWidget(self._layout.count() - 1, widget)
