"""Highlight laranja sobre o título da seção clicada na preview."""
from __future__ import annotations

from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QLabel


class PreviewPageLabel(QLabel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._highlight_rect: QRect | None = None

    def set_highlight_rect(self, rect: QRect | None) -> None:
        self._highlight_rect = QRect(rect) if rect is not None else None
        self.update()

    def clear_highlight(self) -> None:
        self.set_highlight_rect(None)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        if self._highlight_rect is None or self._highlight_rect.isNull():
            return
        painter = QPainter(self)
        pen = QPen(QColor("#F0431E"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self._highlight_rect)
        painter.end()
