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
        self._tree.itemClicked.connect(
            lambda item, _col: self.section_selected.emit(item.data(0, Qt.ItemDataRole.UserRole))
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)
        title = QLabel("Sumário")
        title.setStyleSheet(heading_style(3))
        layout.addWidget(title)
        layout.addWidget(self._tree)
        self.setStyleSheet(f"background-color: {PALETTE.surface_sidebar};")

    def render_sections(self, sections: list[dict]) -> None:
        """``sections``: lista de {"id": str, "title": str, "children": [...]}"""
        self._tree.clear()
        for section in sections:
            self._add_section_item(self._tree.invisibleRootItem(), section)
        self._tree.expandAll()

    def _add_section_item(self, parent_item, section: dict) -> None:
        item = QTreeWidgetItem(parent_item, [section["title"]])
        item.setData(0, Qt.ItemDataRole.UserRole, section["id"])
        for child in section.get("children", []):
            self._add_section_item(item, child)


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
