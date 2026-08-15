"""
Cards primitivos reutilizáveis — sem dependência de features.

ActionCard     → card base (ícone + título + subtítulo)
ElidingLabel   → texto com reticências
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.ui.styles import (
    PALETTE,
    SPACING,
    TYPOGRAPHY,
    action_card_hover_style,
    action_card_icon_style,
    action_card_idle_style,
    action_card_subtitle_style,
    action_card_title_style,
    dashboard_card_media_style,
    scaled_dashboard_card_size,
)

__all__ = [
    "ActionCard",
    "ElidingLabel",
]


class ElidingLabel(QLabel):
    """Rótulo que trunca texto longo com reticências conforme a largura."""

    def __init__(self, text: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._full_text = text
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._refresh()

    def set_full_text(self, text: str) -> None:
        self._full_text = text
        self._refresh()

    def resizeEvent(self, event) -> None:  # noqa: N802
        self._refresh()
        super().resizeEvent(event)

    def _refresh(self) -> None:
        width = self.width()
        if width <= 0:
            self.setText(self._full_text)
            return
        self.setText(
            self.fontMetrics().elidedText(
                self._full_text,
                Qt.TextElideMode.ElideRight,
                width,
            )
        )


class ActionCard(QFrame):
    """Card base da grade — faixa de mídia + corpo tipográfico."""

    clicked = pyqtSignal()

    def __init__(
        self,
        icon: str,
        title: str,
        subtitle: str = "",
        accent_color: str = "",
        accent_bg: str = "",
        card_width: int | None = None,
        card_height: int | None = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        p = PALETTE
        resolved_accent = accent_color or p.senai_blue_light
        resolved_bg = accent_bg or "rgba(74, 111, 212, 0.18)"
        scaled_w, scaled_h = scaled_dashboard_card_size()
        width = card_width if card_width is not None else scaled_w
        height = card_height if card_height is not None else scaled_h
        orange = resolved_accent.lower() in {p.senai_orange.lower(), "#f0431e"}

        if card_width is not None:
            self.setFixedWidth(width)
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        else:
            self.setMinimumWidth(width)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._idle_style = action_card_idle_style()
        self._hover_style = action_card_hover_style(resolved_accent)
        self.setStyleSheet(self._idle_style)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        media = QFrame()
        media.setObjectName("DashboardCardMedia")
        media.setFixedHeight(max(72, round(78 * TYPOGRAPHY.size_body / 13)))
        media.setStyleSheet(dashboard_card_media_style(orange=orange))
        media_layout = QVBoxLayout(media)
        media_layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.sm)
        media_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_size = max(40, round(44 * TYPOGRAPHY.size_body / 13))
        icon_label = QLabel(icon)
        icon_label.setFixedSize(icon_size, icon_size)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(
            action_card_icon_style(
                accent_color=resolved_accent,
                accent_bg=resolved_bg,
                icon=icon,
            )
        )
        media_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignCenter)
        root.addWidget(media)

        body = QVBoxLayout()
        body.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        body.setSpacing(4)

        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        title_label.setMaximumHeight(max(40, TYPOGRAPHY.size_body * 3 + 4))
        title_label.setStyleSheet(action_card_title_style())
        body.addWidget(title_label)

        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setWordWrap(True)
            sub_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            sub_label.setMaximumHeight(max(30, TYPOGRAPHY.size_caption * 3))
            sub_label.setStyleSheet(action_card_subtitle_style())
            body.addWidget(sub_label)

        body.addStretch(1)
        root.addLayout(body)

    def enterEvent(self, event) -> None:  # noqa: N802
        self.setStyleSheet(self._hover_style)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.setStyleSheet(self._idle_style)
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self.clicked.emit()
        super().mousePressEvent(event)
