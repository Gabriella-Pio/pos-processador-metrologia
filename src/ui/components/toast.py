"""
Sistema de notificações toast — mensagens flutuantes contidas no widget pai.

Uso:
    from src.ui.components.toast import show_toast
    show_toast(sidebar_panel, "Mensagem curta", level="info")
"""
from __future__ import annotations

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, Qt
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QHBoxLayout, QLabel, QWidget

from src.ui.components.buttons import IconButton
from src.ui.components.icons import icon_close
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY

_LEVELS = {
    "success": ("✓", PALETTE.success, PALETTE.success_bg),
    "error": ("✕", PALETTE.danger, PALETTE.danger_bg),
    "info": ("ℹ", PALETTE.info, PALETTE.info_bg),
    "warning": ("⚠", PALETTE.warning, PALETTE.warning_bg),
}


class Toast(QWidget):
    """Widget flutuante de notificação — mesmo visual elevado dos modais."""

    def __init__(
        self,
        parent: QWidget,
        message: str,
        level: str = "success",
        duration: int = 3000,
        *,
        max_width: int | None = None,
        position: str = "top",
    ) -> None:
        super().__init__(parent)
        self._position = position
        self._duration = duration
        self.setObjectName("AppToast")
        icon, color, bg = _LEVELS.get(level, _LEVELS["info"])

        self.setStyleSheet(f"""
            QWidget#AppToast {{
                background: {PALETTE.bg_elevated};
                border: 1px solid {PALETTE.border_strong};
                border-radius: {SPACING.radius_md}px;
            }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(SPACING.md, SPACING.sm, SPACING.sm, SPACING.sm)
        lay.setSpacing(SPACING.sm)

        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
        icon_lbl.setFixedSize(28, 28)
        icon_lbl.setStyleSheet(
            f"color:{color}; background:{bg}; border-radius:14px; "
            f"font-size:14px; font-weight:{TYPOGRAPHY.weight_bold}; border:none;"
        )

        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        bounded_width = max_width or self._default_max_width(parent)
        msg_lbl.setMaximumWidth(bounded_width)
        msg_lbl.setStyleSheet(
            f"color:{PALETTE.text_primary}; font-size:{TYPOGRAPHY.size_caption}px; "
            f"background:transparent; border:none;"
        )

        close_btn = IconButton(icon_close(), "Fechar")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.dismiss)

        lay.addWidget(icon_lbl, 0, Qt.AlignmentFlag.AlignTop)
        lay.addWidget(msg_lbl, stretch=1)
        lay.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignTop)

        self.adjustSize()
        self._reposition()
        self.show()
        self.raise_()

        if duration > 0:
            QTimer.singleShot(duration, self.fade_out)

    @staticmethod
    def _default_max_width(parent: QWidget) -> int:
        return max(200, parent.width() - 24)

    def _reposition(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            return
        margin = 10
        available = max(160, parent.width() - 2 * margin)
        if self.width() > available:
            self.setMaximumWidth(available)
            self.adjustSize()
        x = margin
        x = min(x, max(margin, parent.width() - self.width() - margin))
        if self._position == "bottom":
            y = max(margin, parent.height() - self.height() - margin)
        else:
            y = margin
        self.move(x, y)

    def resizeEvent(self, event) -> None:  # noqa: N802
        self._reposition()
        super().resizeEvent(event)

    def fade_out(self) -> None:
        if self.graphicsEffect() is not None:
            return
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(700)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
        anim.finished.connect(self.deleteLater)
        anim.start()
        self._anim = anim

    def dismiss(self) -> None:
        self.fade_out()


def show_toast(
    parent: QWidget,
    message: str,
    level: str = "success",
    duration: int = 3000,
    *,
    max_width: int | None = None,
    position: str = "top",
) -> None:
    """Exibe um toast contido no widget pai (preferir sidebar/painel, não a janela inteira)."""
    host = parent
    while host is not None and host.width() < 180:
        host = host.parentWidget()
    if host is None:
        host = parent
    if max_width is None and host.width() >= 400:
        max_width = min(host.width() - 32, 520)
    Toast(host, message, level, duration, max_width=max_width, position=position)
