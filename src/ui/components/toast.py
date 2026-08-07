"""
Sistema de notificações toast — mensagens flutuantes contidas no widget pai.

Uso:
    from src.ui.components.toast import show_toast
    show_toast(sidebar_panel, "Mensagem curta", level="info")
"""
from __future__ import annotations

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, Qt
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QHBoxLayout, QLabel, QWidget

_LEVELS = {
    "success": ("✓", "#22c55e", "rgba(34,197,94,0.15)", "rgba(34,197,94,0.35)"),
    "error": ("✗", "#f0431e", "rgba(240,67,30,0.15)", "rgba(240,67,30,0.35)"),
    "info": ("ℹ", "#4a6fd4", "rgba(74,111,212,0.15)", "rgba(74,111,212,0.35)"),
    "warning": ("⚠", "#f59e0b", "rgba(245,158,11,0.15)", "rgba(245,158,11,0.35)"),
}


class Toast(QWidget):
    """Widget flutuante de notificação — contido e com quebra de linha no pai."""

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
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        icon, color, bg, border = _LEVELS.get(level, _LEVELS["info"])

        self.setStyleSheet(f"""
            QWidget {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 10px;
            }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)

        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
        icon_lbl.setStyleSheet(
            f"color:{color}; font-size:14px; background:transparent; border:none;"
        )

        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        bounded_width = max_width or self._default_max_width(parent)
        msg_lbl.setMaximumWidth(bounded_width)
        msg_lbl.setStyleSheet(
            "color:#E6EDF3; font-size:12px; line-height: 1.35; "
            "background:transparent; border:none;"
        )

        lay.addWidget(icon_lbl, 0, Qt.AlignmentFlag.AlignTop)
        lay.addWidget(msg_lbl, stretch=1)

        self.adjustSize()
        self._reposition()
        self.show()
        self.raise_()

        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)

        self._anim = QPropertyAnimation(effect, b"opacity")
        self._anim.setDuration(700)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._anim.finished.connect(self.deleteLater)

        QTimer.singleShot(duration, self._anim.start)

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
