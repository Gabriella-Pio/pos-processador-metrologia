"""Preview PDF rasterizado — compartilhado entre workspace e editor de templates."""
from __future__ import annotations

from PyQt6.QtCore import QPoint, QEasingCurve, QPropertyAnimation, Qt, QTimer, pyqtSignal, QRect
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QFrame, QLabel, QScrollArea, QVBoxLayout, QWidget

from src.ui.shared.report_editor.preview_constants import PREVIEW_ZOOM
from src.ui.shared.report_editor.preview_highlight_overlay import PreviewPageLabel
from src.ui.shared.report_editor.preview_hit_tester import (
    anchor_bounds,
    anchor_page_number,
    anchor_widget_rect,
    hit_test_at_click,
)
from src.ui.components.widget_lifecycle import clear_layout
from src.ui.styles import SPACING, caption_style


class PreviewPanel(QFrame):
    """Renderiza páginas PNG do preview e emite clique para navegação por seção."""

    page_clicked = pyqtSignal(int)
    section_clicked = pyqtSignal(str, str, str)  # section_id, focus_target, image_path

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("WorkspacePreviewPanel")
        self._anchor_map: dict[str, dict] = {}
        self._photo_anchors: list[dict] = []
        self._page_items: list[dict] = []
        self._highlighted_section_id: str | None = None
        self._zoom = PREVIEW_ZOOM
        self._scroll_animation: QPropertyAnimation | None = None
        self._center_h_timer = QTimer(self)
        self._center_h_timer.setSingleShot(True)
        self._center_h_timer.timeout.connect(self._apply_center_horizontal_scroll)
        self._pending_vscroll_ratio: float | None = None

        self._status_label = QLabel("", self)
        self._status_label.setObjectName("WorkspacePreviewStatus")
        self._status_label.hide()

        self._scroll = QScrollArea(self)
        self._scroll.setObjectName("WorkspacePreviewScroll")
        self._pages_host = QWidget(self._scroll)
        self._pages_layout = QVBoxLayout(self._pages_host)
        self._pages_layout.setContentsMargins(0, 0, 0, 0)
        self._pages_layout.setSpacing(SPACING.lg)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setWidget(self._pages_host)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.sm)
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
        self._status_label.setVisible(bool(text.strip()))

    def set_busy(self, busy: bool, message: str = "Atualizando preview…") -> None:
        """Compat: o feedback de busy fica no chrome do workspace/templates.

        Mantém a API para callers legados; o preview permanece legível enquanto regenera.
        """
        _ = (busy, message)

    def set_anchor_map(self, anchor_map: dict[str, dict]) -> None:
        merged: dict[str, dict] = {}
        for section_id, info in dict(anchor_map).items():
            item = dict(info)
            previous = self._anchor_map.get(section_id, {})
            if not item.get("anchor_rect") and previous.get("anchor_rect"):
                item["anchor_rect"] = previous["anchor_rect"]
            if item.get("page_start") is None and previous.get("page_start") is not None:
                item["page_start"] = previous["page_start"]
            merged[section_id] = item
        self._anchor_map = merged
        self._apply_highlight()

    def set_photo_anchors(self, photo_anchors: list[dict]) -> None:
        self._photo_anchors = list(photo_anchors or [])

    def update_anchor_map(self, anchor_map: dict[str, dict]) -> None:
        for section_id, info in (anchor_map or {}).items():
            current = self._anchor_map.setdefault(section_id, {})
            rect = info.get("anchor_rect") if isinstance(info.get("anchor_rect"), dict) else info
            if isinstance(rect, dict) and any(key in rect for key in ("x", "y", "width", "page")):
                current["anchor_rect"] = rect
            page = info.get("page") or info.get("page_start")
            if page is None and isinstance(rect, dict):
                page = rect.get("page")
            if page is not None:
                current["page_start"] = page
        self._apply_highlight()

    def render_pages(self, pages_png: list[bytes]) -> None:
        self._pending_vscroll_ratio = self._vertical_scroll_ratio()
        highlighted = self._highlighted_section_id
        self.clear()
        if not pages_png:
            empty = QLabel("Nenhuma página disponível para preview.", self._pages_host)
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setObjectName("SidebarHint")
            empty.setStyleSheet(caption_style())
            self._pages_layout.addWidget(empty)
            return

        self._page_items = []
        for index, page_png in enumerate(pages_png, start=1):
            page_container = QWidget(self._pages_host)
            page_layout = QVBoxLayout(page_container)
            page_layout.setContentsMargins(0, 0, 0, 0)

            page_label = QLabel(f"Página {index}", page_container)
            page_label.setObjectName("WorkspacePageLabel")
            page_label.setCursor(Qt.CursorShape.PointingHandCursor)
            page_label.mousePressEvent = lambda event, pn=index: self.page_clicked.emit(pn)  # type: ignore[method-assign]

            image_label = PreviewPageLabel(page_container)
            image_label.setObjectName("WorkspacePreviewPage")
            image_label.setCursor(Qt.CursorShape.PointingHandCursor)
            pixmap = QPixmap()
            pixmap.loadFromData(page_png)
            image_label.setPixmap(pixmap)
            image_label.mousePressEvent = lambda event, pn=index, label=image_label: self._on_page_image_clicked(  # type: ignore[method-assign]
                event, pn, label
            )

            page_layout.addWidget(page_label)
            page_layout.addWidget(image_label)
            self._pages_layout.addWidget(page_container)
            page_height_pts = pixmap.height() / self._zoom
            self._page_items.append(
                {
                    "page_number": index,
                    "container": page_container,
                    "page_label": page_label,
                    "image_label": image_label,
                    "base_pixmap": pixmap,
                    "page_height_pts": page_height_pts,
                }
            )

        self._pages_layout.addStretch(1)
        if highlighted:
            self.highlight_section(highlighted)
        QTimer.singleShot(0, self._after_pages_laid_out)

    def _vertical_scroll_ratio(self) -> float | None:
        bar = self._scroll.verticalScrollBar()
        maximum = bar.maximum()
        if maximum <= 0:
            return None
        return bar.value() / maximum

    def _restore_vertical_scroll(self) -> None:
        ratio = self._pending_vscroll_ratio
        self._pending_vscroll_ratio = None
        if ratio is None:
            return
        if self._scroll_animation is not None:
            self._scroll_animation.stop()
            self._scroll_animation = None
        bar = self._scroll.verticalScrollBar()
        bar.setValue(round(ratio * bar.maximum()))

    def _after_pages_laid_out(self) -> None:
        self._restore_vertical_scroll()
        self.center_horizontal_scroll()

    def center_horizontal_scroll(self) -> None:
        """Centraliza a folha na preview quando há overflow horizontal."""
        self._center_h_timer.start(40)

    def _apply_center_horizontal_scroll(self) -> None:
        hbar = self._scroll.horizontalScrollBar()
        maximum = hbar.maximum()
        if maximum <= 0:
            hbar.setValue(0)
            return
        hbar.setValue(maximum // 2)

    def clear(self) -> None:
        clear_layout(self._pages_layout, discard=True)
        self._page_items = []
        # Mantém o destaque da seção ativa; clear() só derruba os widgets.

    def focus_section(self, section_id: str) -> None:
        self.highlight_section(section_id)
        QTimer.singleShot(0, lambda sid=section_id: self._scroll_to_section_anchor(sid))

    def _scroll_to_section_anchor(self, section_id: str) -> None:
        section = self._anchor_map.get(section_id) or {}
        rect = anchor_bounds(section)
        if rect is None:
            self._scroll_to_section_page(section)
            return

        page_number = anchor_page_number(section, rect)
        if page_number is None or page_number < 1 or page_number > len(self._page_items):
            return

        page_item = self._page_items[page_number - 1]
        image_label = page_item.get("image_label")
        pixmap = page_item.get("base_pixmap")
        if not isinstance(image_label, PreviewPageLabel) or pixmap is None or pixmap.isNull():
            self._scroll_to_section_page(section)
            return

        label_w = image_label.width() or pixmap.width()
        label_h = image_label.height() or pixmap.height()
        x, y, _, _ = anchor_widget_rect(
            rect,
            page_height_pts=page_item["page_height_pts"],
            zoom=self._zoom,
            label_width=label_w,
            label_height=label_h,
            pixmap_width=pixmap.width(),
            pixmap_height=pixmap.height(),
        )
        anchor_point = image_label.mapTo(self._pages_host, QPoint(x, y))
        self._scroll_content_to_y(anchor_point.y())

    def _scroll_content_to_y(self, content_y: int, *, top_margin: int | None = None) -> None:
        """Posiciona content_y no topo visível da preview com rolagem suave."""
        margin = top_margin if top_margin is not None else SPACING.md
        scrollbar = self._scroll.verticalScrollBar()
        target = max(0, min(content_y - margin, scrollbar.maximum()))
        current = scrollbar.value()
        if abs(current - target) < 6:
            scrollbar.setValue(target)
            return
        if self._scroll_animation is not None:
            self._scroll_animation.stop()
        animation = QPropertyAnimation(scrollbar, b"value", self)
        animation.setDuration(320)
        animation.setStartValue(current)
        animation.setEndValue(target)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()
        self._scroll_animation = animation

    def _scroll_to_section_page(self, section: dict) -> None:
        anchor = section.get("anchor_rect") if isinstance(section.get("anchor_rect"), dict) else section
        page_number = section.get("page_start") or (anchor or {}).get("page")
        if page_number is None or page_number < 1 or page_number > len(self._page_items):
            return
        item = self._page_items[page_number - 1]
        page_top = item["container"].mapTo(self._pages_host, QPoint(0, 0)).y()
        self._scroll_content_to_y(page_top)

    def highlight_section(self, section_id: str | None) -> None:
        self._highlighted_section_id = section_id
        self._apply_highlight()

    def section_id_for_page(self, page_number: int) -> str | None:
        for section_id, info in self._anchor_map.items():
            page = (info or {}).get("page_start") or (info or {}).get("page")
            if page == page_number:
                return section_id
        return None

    def _apply_highlight(self) -> None:
        for item in self._page_items:
            image_label = item.get("image_label")
            if isinstance(image_label, PreviewPageLabel):
                image_label.clear_highlight()

        if not self._highlighted_section_id:
            return

        info = self._anchor_map.get(self._highlighted_section_id) or {}
        rect = anchor_bounds(info)
        if rect is None:
            return
        page_number = anchor_page_number(info, rect)
        if page_number is None or page_number < 1 or page_number > len(self._page_items):
            return

        page_item = self._page_items[page_number - 1]
        image_label = page_item.get("image_label")
        pixmap = page_item.get("base_pixmap")
        if not isinstance(image_label, PreviewPageLabel) or pixmap is None:
            return

        highlight = anchor_widget_rect(
            rect,
            page_height_pts=page_item["page_height_pts"],
            zoom=self._zoom,
            label_width=image_label.width() or pixmap.width(),
            label_height=image_label.height() or pixmap.height(),
            pixmap_width=pixmap.width(),
            pixmap_height=pixmap.height(),
        )
        if highlight is None:
            return
        x, y, w, h = highlight
        image_label.set_highlight_rect(QRect(x, y, w, h))

    def _on_page_image_clicked(self, event, page_number: int, image_label: PreviewPageLabel) -> None:
        pixmap = image_label.pixmap()
        if pixmap is None or pixmap.isNull():
            self.page_clicked.emit(page_number)
            return

        page_item = self._page_items[page_number - 1]
        hit = hit_test_at_click(
            page_number,
            event.position().x(),
            event.position().y(),
            label_width=image_label.width(),
            label_height=image_label.height(),
            pixmap_width=pixmap.width(),
            pixmap_height=pixmap.height(),
            page_height_pts=page_item["page_height_pts"],
            zoom=self._zoom,
            anchor_map=self._anchor_map,
            photo_anchors=self._photo_anchors,
        )
        if hit is None:
            self.page_clicked.emit(page_number)
            return
        self.highlight_section(hit.section_id)
        focus_target = hit.field_key or "section_title"
        self.section_clicked.emit(hit.section_id, focus_target, hit.image_path or "")

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._apply_highlight()
        if self._page_items and self._scroll.horizontalScrollBar().maximum() > 0:
            self.center_horizontal_scroll()
