"""Empty state da Home — mensagem centralizada com CTA opcional."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, empty_state_cta_style


class EmptyState(QWidget):
    action_requested = pyqtSignal()

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        cta: str = "",
        icon: QIcon | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop
        )
        layout.setSpacing(0)

        self._title_label: QLabel | None = None
        self._subtitle_label: QLabel | None = None
        self._cta_button: QPushButton | None = None

        if icon is not None:
            icon_label = QLabel()
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setFixedSize(56, 56)
            icon_label.setPixmap(
                icon.pixmap(QSize(48, 48), QIcon.Mode.Normal, QIcon.State.Off)
            )
            icon_label.setStyleSheet("background: transparent; border: none;")
            layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignHCenter)
            layout.addSpacing(14)

        self._title_label = QLabel(title)
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._title_label)

        if subtitle:
            self._subtitle_label = QLabel(subtitle)
            self._subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._subtitle_label.setWordWrap(True)
            self._subtitle_label.setMaximumWidth(380)
            layout.addSpacing(6)
            layout.addWidget(self._subtitle_label, 0, Qt.AlignmentFlag.AlignHCenter)

        if cta:
            layout.addSpacing(24)
            self._cta_button = QPushButton(cta)
            self._cta_button.setFixedHeight(36)
            self._cta_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self._cta_button.clicked.connect(self.action_requested.emit)
            layout.addWidget(self._cta_button, 0, Qt.AlignmentFlag.AlignHCenter)

        layout.setContentsMargins(0, SPACING.md, 0, SPACING.md)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )
        self.refresh_appearance()

    def refresh_appearance(self) -> None:
        p = PALETTE
        t = TYPOGRAPHY
        if self._title_label is not None:
            self._title_label.setStyleSheet(
                f"color:{p.text_secondary}; font-size:{t.size_h3}px; "
                f"font-weight:{t.weight_semibold}; "
                f"background:transparent; border:none;"
            )
        if self._subtitle_label is not None:
            self._subtitle_label.setStyleSheet(
                f"color:{p.text_muted}; font-size:{t.size_body}px; "
                f"background:transparent; border:none;"
            )
        if self._cta_button is not None:
            self._cta_button.setStyleSheet(empty_state_cta_style())
