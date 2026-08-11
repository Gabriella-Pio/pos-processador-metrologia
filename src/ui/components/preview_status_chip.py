"""Chip de status do preview — idle (versão) ou busy (gerando), na barra de chrome."""
from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QWidget

from src.ui.components.icons import app_icon
from src.ui.styles import PALETTE, SPACING


class PreviewStatusChip(QWidget):
    """Status planejado na barra: texto muted em idle; chip laranja com ícone em busy."""

    _ICON_SIZE = 14
    _SPIN_MS = 40
    _SPIN_STEP_DEG = 12

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("PreviewStatusChip")
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self._idle_text = ""
        self._busy = False
        self._angle = 0
        self._base_icon = QPixmap()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.xs)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._icon = QLabel()
        self._icon.setObjectName("PreviewStatusChipIcon")
        self._icon.setFixedSize(self._ICON_SIZE, self._ICON_SIZE)
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon.hide()

        self._label = QLabel("")
        self._label.setObjectName("PreviewStatusChipLabel")
        self._label.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self._icon)
        layout.addWidget(self._label)
        self.hide()

        self._spin_timer = QTimer(self)
        self._spin_timer.setInterval(self._SPIN_MS)
        self._spin_timer.timeout.connect(self._tick_spin)

    def set_idle_text(self, text: str) -> None:
        self._idle_text = str(text or "").strip()
        if not self._busy:
            self._apply_idle()

    def set_busy(self, busy: bool, message: str = "Atualizando preview…") -> None:
        self._busy = bool(busy)
        if self._busy:
            self.setProperty("busy", "true")
            self._base_icon = app_icon(
                "sync-alt", color=PALETTE.senai_orange, scale=0.85
            ).pixmap(self._ICON_SIZE, self._ICON_SIZE)
            self._angle = 0
            self._paint_rotated_icon()
            self._icon.show()
            self._label.setText(message or "Atualizando preview…")
            self.show()
            if not self._spin_timer.isActive():
                self._spin_timer.start()
        else:
            self._spin_timer.stop()
            self.setProperty("busy", "false")
            self._icon.hide()
            self._apply_idle()
        self.style().unpolish(self)
        self.style().polish(self)
        self._label.style().unpolish(self._label)
        self._label.style().polish(self._label)

    def _tick_spin(self) -> None:
        if not self._busy or self._base_icon.isNull():
            self._spin_timer.stop()
            return
        self._angle = (self._angle + self._SPIN_STEP_DEG) % 360
        self._paint_rotated_icon()

    def _paint_rotated_icon(self) -> None:
        if self._base_icon.isNull():
            return
        size = self._ICON_SIZE
        canvas = QPixmap(size, size)
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.translate(size / 2, size / 2)
        painter.rotate(self._angle)
        painter.translate(-size / 2, -size / 2)
        painter.drawPixmap(0, 0, self._base_icon)
        painter.end()
        self._icon.setPixmap(canvas)

    def _apply_idle(self) -> None:
        if self._idle_text:
            self._label.setText(self._idle_text)
            self.show()
        else:
            self._label.setText("")
            self.hide()
