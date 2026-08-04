"""
Sistema de notificações toast — exibe mensagens flutuantes no bottom-center da janela.

Uso:
    from src.ui.components.toast import show_toast
    show_toast(parent_window, "Relatório exportado!", level="success")
    show_toast(self, "Erro ao carregar arquivo", level="error")
"""
from __future__ import annotations

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, Qt
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QHBoxLayout, QLabel, QWidget

_LEVELS = {
    "success": ("✓", "#22c55e", "rgba(34,197,94,0.15)", "rgba(34,197,94,0.35)"),
    "error":   ("✗", "#f0431e", "rgba(240,67,30,0.15)", "rgba(240,67,30,0.35)"),
    "info":    ("ℹ", "#4a6fd4", "rgba(74,111,212,0.15)", "rgba(74,111,212,0.35)"),
    "warning": ("⚠", "#f59e0b", "rgba(245,158,11,0.15)", "rgba(245,158,11,0.35)"),
}


class Toast(QWidget):
    """Widget flutuante de notificação — aparece na janela pai e some automaticamente."""

    def __init__(self, parent: QWidget, message: str,
                 level: str = "success", duration: int = 3000) -> None:
        super().__init__(parent)
        icon, color, bg, border = _LEVELS.get(level, _LEVELS["info"])

        self.setStyleSheet(f"""
            QWidget {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 10px;
            }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 18, 10)
        lay.setSpacing(10)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(
            f"color:{color}; font-size:15px; background:transparent; border:none;"
        )

        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet(
            "color:#E6EDF3; font-size:13px; background:transparent; border:none;"
        )

        lay.addWidget(icon_lbl)
        lay.addWidget(msg_lbl)

        self.adjustSize()
        self._reposition()
        self.show()
        self.raise_()

        # Fade-out via QGraphicsOpacityEffect
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)

        self._anim = QPropertyAnimation(effect, b"opacity")
        self._anim.setDuration(700)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._anim.finished.connect(self.deleteLater)

        QTimer.singleShot(duration, self._anim.start)

    def _reposition(self) -> None:
        if self.parent():
            pr = self.parent().rect()
            self.move(
                (pr.width() - self.width()) // 2,
                pr.height() - self.height() - 32,
            )

    def resizeEvent(self, event) -> None:
        self._reposition()
        super().resizeEvent(event)


def show_toast(parent: QWidget, message: str, level: str = "success",
               duration: int = 3000) -> None:
    """Exibe um toast centralizado na janela pai."""
    Toast(parent, message, level, duration)
