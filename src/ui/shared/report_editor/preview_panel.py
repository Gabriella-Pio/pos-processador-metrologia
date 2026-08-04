"""Preview PDF rasterizado — compartilhado entre workspace e editor de templates."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QFrame, QLabel, QScrollArea, QVBoxLayout, QWidget

from src.ui.styles import SPACING, caption_style


class PreviewPanel(QFrame):
    """Renderiza páginas PNG do preview e emite clique para navegação por seção."""

    page_clicked = pyqtSignal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("WorkspacePreviewPanel")
        self._anchor_map: dict[str, dict] = {}
        self._page_items: list[dict] = []

        self._status_label = QLabel("")
        self._status_label.setObjectName("WorkspacePreviewStatus")

        self._scroll = QScrollArea()
        self._scroll.setObjectName("WorkspacePreviewScroll")
        self._pages_host = QWidget()
        self._pages_layout = QVBoxLayout(self._pages_host)
        self._pages_layout.setContentsMargins(0, 0, 0, 0)
        self._pages_layout.setSpacing(SPACING.lg)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setWidget(self._pages_host)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.sm)
        layout.addWidget(self._status_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._scroll, stretch=1)

    def scroll_area(self) -> QScrollArea:
        return self._scroll

    def refresh_appearance(self) -> None:
        for item in self._page_items:
            page_label = item.get("page_label")
            image_label = item.get("image_label")
            if page_label is not None:
                page_label.setStyleSheet("")
            if image_label is not None:
                image_label.setStyleSheet("")

    def set_status_text(self, text: str) -> None:
        self._status_label.setText(text)

    def set_anchor_map(self, anchor_map: dict[str, dict]) -> None:
        self._anchor_map = dict(anchor_map)

    def update_anchor_map(self, anchor_map: dict[str, dict]) -> None:
        for section_id, info in anchor_map.items():
            if section_id in self._anchor_map:
                self._anchor_map[section_id]["page_start"] = info.get("page")
                self._anchor_map[section_id]["anchor_rect"] = info

    def render_pages(self, pages_png: list[bytes]) -> None:
        scroll_pos = self._scroll.verticalScrollBar().value()
        prev_count = len(self._page_items)
        self.clear()
        if not pages_png:
            empty = QLabel("Nenhuma página disponível para preview.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setObjectName("SidebarHint")
            empty.setStyleSheet(caption_style())
            self._pages_layout.addWidget(empty)
            return

        self._page_items = []
        for index, page_png in enumerate(pages_png, start=1):
            page_container = QWidget()
            page_layout = QVBoxLayout(page_container)
            page_layout.setContentsMargins(0, 0, 0, 0)

            page_label = QLabel(f"Página {index}")
            page_label.setObjectName("WorkspacePageLabel")
            page_label.setCursor(Qt.CursorShape.PointingHandCursor)
            page_label.mousePressEvent = lambda event, pn=index: self.page_clicked.emit(pn)  # type: ignore[method-assign]

            image_label = QLabel()
            image_label.setObjectName("WorkspacePreviewPage")
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pixmap = QPixmap()
            pixmap.loadFromData(page_png)
            image_label.setPixmap(pixmap)

            page_layout.addWidget(page_label)
            page_layout.addWidget(image_label)
            self._pages_layout.addWidget(page_container)
            self._page_items.append(
                {
                    "page_number": index,
                    "container": page_container,
                    "page_label": page_label,
                    "image_label": image_label,
                    "base_pixmap": pixmap,
                }
            )

        self._pages_layout.addStretch(1)
        if abs(len(pages_png) - prev_count) <= 1:
            self._scroll.verticalScrollBar().setValue(scroll_pos)

    def clear(self) -> None:
        while self._pages_layout.count():
            item = self._pages_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._page_items = []

    def focus_section(self, section_id: str) -> None:
        section = self._anchor_map.get(section_id) or {}
        anchor = section.get("anchor_rect") if isinstance(section.get("anchor_rect"), dict) else section
        page_number = section.get("page_start") or (anchor or {}).get("page")
        if page_number is None or page_number < 1 or page_number > len(self._page_items):
            return
        item = self._page_items[page_number - 1]
        self._scroll.ensureWidgetVisible(item["container"], 24, 24)

    def section_id_for_page(self, page_number: int) -> str | None:
        for section_id, info in self._anchor_map.items():
            page = (info or {}).get("page_start") or (info or {}).get("page")
            if page == page_number:
                return section_id
        return None
