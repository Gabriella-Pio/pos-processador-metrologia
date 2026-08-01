"""
Painéis reutilizáveis das sidebars do Workspace: navegação por
bookmarks, gerenciador de imagens (drag-and-drop), toolbar de
anotação e histórico de versões em tempo real.

Cada painel é "burro" (dumb component): recebe dados via métodos
``set_*``/``render_*`` e emite sinais de intenção — quem decide o que
fazer é sempre o ViewModel, nunca o próprio painel.
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
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.ports import ReportImage, VersionEntry
from src.ui.styles import PALETTE, SPACING, caption_style, heading_style


class BookmarksPanel(QFrame):
    """Sumário interativo do relatório (sidebar esquerda)."""

    section_selected = pyqtSignal(str)  # section_id

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setColumnCount(2)
        self._tree.setIndentation(18)
        self._tree.setUniformRowHeights(True)
        self._tree.itemClicked.connect(
            lambda item, _col: self.section_selected.emit(item.data(0, Qt.ItemDataRole.UserRole))
        )
        self._search = QLineEdit()
        self._search.setPlaceholderText("Buscar seção")
        self._search.textChanged.connect(self._apply_filter)
        self._sections: list[dict] = []
        self._active_section_id: str | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)
        title = QLabel("Sumário")
        title.setStyleSheet(heading_style(3))
        subtitle = QLabel("Clique em uma seção para navegar e associar fotografias.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(caption_style())
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self._search)
        layout.addWidget(self._tree)
        self.setStyleSheet(f"background-color: {PALETTE.surface_sidebar};")

    def render_sections(self, sections: list[dict]) -> None:
        """``sections``: lista de {"id": str, "title": str, "children": [...], ...}"""
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
        if image_count > 0:
            section_text = f"{title}   ·   {image_count} foto{'s' if image_count != 1 else ''}"
        else:
            section_text = f"{title}   ·   sem fotos"

        matches_self = filtro in title.lower() or filtro in section.get("id", "").lower()
        if filtro and not matches_self and not child_items:
            return None

        item = QTreeWidgetItem([section_text, ""])
        item.setData(0, Qt.ItemDataRole.UserRole, section["id"])
        item.setToolTip(0, title)
        if section.get("id") == self._active_section_id:
            font_title = item.font(0)
            font_title.setBold(True)
            item.setFont(0, font_title)

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
    image_selected = pyqtSignal(object)  # ReportImage

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._list = QListWidget()
        self._list.itemClicked.connect(
            lambda item: self.image_selected.emit(item.data(Qt.ItemDataRole.UserRole))
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.sm)

        title = QLabel("Fotografias da peça")
        title.setStyleSheet(heading_style(3))
        hint = QLabel("Arraste imagens aqui para associá-las à seção selecionada.")
        hint.setWordWrap(True)
        hint.setStyleSheet(caption_style())

        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addWidget(self._list, stretch=1)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() in (".png", ".jpg", ".jpeg"):
                self.image_dropped.emit(path)
        event.acceptProposedAction()

    def render_images(self, images: list[ReportImage]) -> None:
        self._list.clear()
        for image in images:
            item = QListWidgetItem(image.image_path.name)
            item.setData(Qt.ItemDataRole.UserRole, image)
            self._list.addItem(item)


class AnnotationToolbar(QFrame):
    """Editor visual de marcações: seta, círculo, caixa de texto, numeração."""

    tool_selected = pyqtSignal(str)  # "arrow" | "circle" | "text_box" | "number"

    _TOOLS = (
        ("arrow", "↗", "Seta"),
        ("circle", "◯", "Círculo"),
        ("text_box", "▭", "Caixa de texto"),
        ("number", "①", "Numeração"),
    )

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)

        title = QLabel("Marcações:")
        title.setStyleSheet(caption_style())
        layout.addWidget(title)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._build_tool_buttons(layout)

    def _build_tool_buttons(self, layout: QHBoxLayout) -> None:
        from PyQt6.QtWidgets import QPushButton  # import local para evitar ciclo

        for tool_id, symbol, tooltip in self._TOOLS:
            button = QPushButton(symbol)
            button.setCheckable(True)
            button.setToolTip(tooltip)
            button.setFixedSize(36, 36)
            button.setStyleSheet(f"""
                QPushButton {{ border: 1px solid {PALETTE.border}; border-radius: {SPACING.radius_sm}px; }}
                QPushButton:checked {{ background-color: {PALETTE.info_bg}; border-color: {PALETTE.zeiss_blue}; }}
            """)
            button.clicked.connect(lambda _checked, t=tool_id: self.tool_selected.emit(t))
            self._group.addButton(button)
            layout.addWidget(button)
        layout.addStretch(1)


class VersionHistoryPanel(QFrame):
    """Histórico de versões em tempo real (sidebar direita, base)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._list = QListWidget()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        title = QLabel("Histórico de versões")
        title.setStyleSheet(heading_style(3))
        layout.addWidget(title)
        layout.addWidget(self._list)

    def render_history(self, entries: list[VersionEntry]) -> None:
        self._list.clear()
        for entry in reversed(entries):
            text = (
                f"v{entry.version_number} — {entry.responsible_name}\n"
                f"{entry.timestamp.strftime('%d/%m/%Y %H:%M')} · {entry.description}"
            )
            item = QListWidgetItem(text)
            self._list.addItem(item)
