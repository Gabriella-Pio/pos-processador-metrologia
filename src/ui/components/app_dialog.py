"""Diálogos modais alinhados ao design system dark da aplicação."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.ui.components.buttons import DangerButton, PrimaryButton, SecondaryButton
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, caption_style, heading_style


class DialogKind(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"


_KIND_META = {
    DialogKind.INFO: ("ℹ", PALETTE.info, PALETTE.info_bg),
    DialogKind.SUCCESS: ("✓", PALETTE.success, PALETTE.success_bg),
    DialogKind.WARNING: ("⚠", PALETTE.warning, PALETTE.warning_bg),
    DialogKind.DANGER: ("✕", PALETTE.danger, PALETTE.danger_bg),
}


class AppMessageDialog(QDialog):
    def __init__(
        self,
        parent: Optional[QWidget],
        title: str,
        message: str,
        *,
        kind: DialogKind = DialogKind.INFO,
        details: str | None = None,
        primary_label: str = "Entendi",
        secondary_label: str | None = None,
        danger_primary: bool = False,
    ) -> None:
        super().__init__(parent)
        self._confirmed = False
        self.setWindowTitle(title)
        self.setMinimumWidth(440)
        self.setMaximumWidth(520)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background-color: {PALETTE.bg_surface}; }}")

        icon_char, accent, accent_bg = _KIND_META[kind]

        icon = QLabel(icon_char)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFixedSize(40, 40)
        icon.setStyleSheet(
            f"color: {accent}; background-color: {accent_bg}; "
            f"border-radius: 20px; font-size: 18px; font-weight: {TYPOGRAPHY.weight_bold};"
        )

        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet(heading_style(3))

        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setObjectName("SidebarHint")
        message_label.setStyleSheet(caption_style())

        header = QHBoxLayout()
        header.setSpacing(SPACING.md)
        header.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)
        text_col = QVBoxLayout()
        text_col.setSpacing(SPACING.xs)
        text_col.addWidget(title_label)
        text_col.addWidget(message_label)
        header.addLayout(text_col, stretch=1)

        body = QVBoxLayout()
        body.setSpacing(SPACING.md)
        body.addLayout(header)

        if details:
            details_box = QFrame()
            details_box.setObjectName("GlobalFieldCard")
            details_layout = QVBoxLayout(details_box)
            details_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
            details_view = QTextEdit()
            details_view.setReadOnly(True)
            details_view.setPlainText(details)
            details_view.setMinimumHeight(100)
            details_layout.addWidget(details_view)
            body.addWidget(details_box)

        footer = QHBoxLayout()
        footer.addStretch(1)
        if secondary_label:
            cancel = SecondaryButton(secondary_label)
            cancel.clicked.connect(self.reject)
            footer.addWidget(cancel)
        primary_cls = DangerButton if danger_primary else PrimaryButton
        primary = primary_cls(primary_label)
        primary.clicked.connect(self._accept)
        footer.addWidget(primary)
        body.addLayout(footer)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.lg)
        outer.setSpacing(0)
        outer.addLayout(body)

    def _accept(self) -> None:
        self._confirmed = True
        self.accept()

    @property
    def confirmed(self) -> bool:
        return self._confirmed

    @classmethod
    def inform(
        cls,
        parent: Optional[QWidget],
        title: str,
        message: str,
        *,
        kind: DialogKind = DialogKind.INFO,
        details: str | None = None,
    ) -> None:
        dialog = cls(parent, title, message, kind=kind, details=details)
        dialog.exec()

    @classmethod
    def confirm(
        cls,
        parent: Optional[QWidget],
        title: str,
        message: str,
        *,
        confirm_label: str = "Confirmar",
        cancel_label: str = "Cancelar",
        danger: bool = False,
    ) -> bool:
        dialog = cls(
            parent,
            title,
            message,
            kind=DialogKind.DANGER if danger else DialogKind.WARNING,
            primary_label=confirm_label,
            secondary_label=cancel_label,
            danger_primary=danger,
        )
        dialog.exec()
        return dialog.confirmed
