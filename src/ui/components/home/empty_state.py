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
        p = PALETTE
        layout = QVBoxLayout(self)
        layout.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop
        )
        layout.setSpacing(0)

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

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(
            f"color:{p.text_secondary}; font-size:16px; "
            f"font-weight:{TYPOGRAPHY.weight_semibold}; "
            f"background:transparent; border:none;"
        )
        layout.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            subtitle_label.setWordWrap(True)
            subtitle_label.setMaximumWidth(380)
            subtitle_label.setStyleSheet(
                f"color:{p.text_muted}; font-size:13px; "
                f"background:transparent; border:none;"
            )
            layout.addSpacing(6)
            layout.addWidget(subtitle_label, 0, Qt.AlignmentFlag.AlignHCenter)

        if cta:
            layout.addSpacing(24)
            button = QPushButton(cta)
            button.setFixedHeight(36)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setStyleSheet(empty_state_cta_style())
            button.clicked.connect(self.action_requested.emit)
            layout.addWidget(button, 0, Qt.AlignmentFlag.AlignHCenter)

        layout.setContentsMargins(0, SPACING.md, 0, SPACING.md)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )
