"""Miniatura de como a foto renderizada aparecerá no PDF."""
from __future__ import annotations

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout

from src.core.application.image_edit_compositor import render_edited_image
from src.core.domain.ports import ReportImage
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, caption_style


class PhotoPdfPreviewPanel(QFrame):
    """Preview local (sem esperar debounce do PDF completo)."""

    _PREVIEW_W = 132
    _PREVIEW_H = 100

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("PhotoPdfPreviewPanel")
        self._image: ReportImage | None = None
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(280)
        self._debounce.timeout.connect(self._render)

        self._title = QLabel("No PDF")
        self._title.setObjectName("GlobalFieldLabel")
        self._thumb = QLabel("—")
        self._thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumb.setFixedSize(self._PREVIEW_W, self._PREVIEW_H)
        self._thumb.setStyleSheet(
            f"background: {PALETTE.bg_surface_alt}; border: 1px solid {PALETTE.border_subtle}; "
            f"border-radius: 6px;"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.xs, SPACING.sm, SPACING.xs)
        layout.setSpacing(SPACING.xs)
        layout.addWidget(self._title)
        layout.addWidget(self._thumb, alignment=Qt.AlignmentFlag.AlignHCenter)
        self._title.setStyleSheet(
            f"color: {PALETTE.text_primary}; font-size: {TYPOGRAPHY.size_caption}px; "
            f"font-weight: {TYPOGRAPHY.weight_semibold}; background: transparent;"
        )

    def set_image(self, image: ReportImage | None) -> None:
        self._image = image
        if image is None:
            self._thumb.setPixmap(QPixmap())
            self._thumb.setText("—")
            return
        self.schedule_refresh()

    def schedule_refresh(self) -> None:
        self._debounce.start()

    def _render(self) -> None:
        if self._image is None or not self._image.image_path.is_file():
            self._thumb.setText("—")
            return
        rendered = render_edited_image(
            self._image.image_path,
            crop=self._image.crop,
            annotations=self._image.annotations,
        )
        if rendered is None:
            self._thumb.setText("—")
            return
        pixmap = QPixmap(str(rendered))
        if pixmap.isNull():
            self._thumb.setText("—")
            return
        scaled = pixmap.scaled(
            self._PREVIEW_W - 4,
            self._PREVIEW_H - 4,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._thumb.setPixmap(scaled)
        self._thumb.setText("")
