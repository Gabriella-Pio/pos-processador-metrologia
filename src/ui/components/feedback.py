"""
Componentes de feedback ao usuário: alertas inline e diálogos de erro
amigáveis. Usado para que falhas (ex.: PDF corrompido) nunca travem a
aplicação ou exponham stack traces cruas ao operador.
"""
from __future__ import annotations

from enum import Enum, auto
from typing import Optional

from PyQt6.QtWidgets import QLabel, QMessageBox, QVBoxLayout, QWidget

from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY


class FeedbackLevel(Enum):
    INFO = auto()
    SUCCESS = auto()
    WARNING = auto()
    DANGER = auto()


_LEVEL_COLORS = {
    FeedbackLevel.INFO: (PALETTE.info, PALETTE.info_bg),
    FeedbackLevel.SUCCESS: (PALETTE.success, PALETTE.success_bg),
    FeedbackLevel.WARNING: (PALETTE.warning, PALETTE.warning_bg),
    FeedbackLevel.DANGER: (PALETTE.danger, PALETTE.danger_bg),
}

_LEVEL_ICONS = {
    FeedbackLevel.INFO: "ℹ️",
    FeedbackLevel.SUCCESS: "✅",
    FeedbackLevel.WARNING: "⚠️",
    FeedbackLevel.DANGER: "⛔",
}


class InlineBanner(QWidget):
    """Faixa de aviso inline (não bloqueante), usada dentro das views
    — por exemplo no topo do Workspace ao detectar uma seção com dados
    faltando no relatório importado.
    """

    def __init__(
        self,
        message: str,
        level: FeedbackLevel = FeedbackLevel.INFO,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        color, bg = _LEVEL_COLORS[level]
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)

        label = QLabel(f"{_LEVEL_ICONS[level]}  {message}")
        label.setWordWrap(True)
        label.setStyleSheet(f"color: {color}; font-weight: {TYPOGRAPHY.weight_medium};")
        layout.addWidget(label)

        self.setStyleSheet(f"background-color: {bg}; border-radius: {SPACING.radius_md}px;")


def show_friendly_error(
    parent: Optional[QWidget],
    title: str,
    message: str,
    details: Optional[str] = None,
) -> None:
    """Exibe um erro de forma amigável, sem travar a aplicação.

    ``details`` (ex.: exceção técnica original) fica disponível apenas
    no botão "Detalhes" do QMessageBox — o operador de metrologia não
    precisa ver stack traces por padrão.
    """
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Warning)
    box.setWindowTitle(title)
    box.setText(message)
    if details:
        box.setDetailedText(details)
    box.setStandardButtons(QMessageBox.StandardButton.Ok)
    box.exec()


def show_info(parent: Optional[QWidget], title: str, message: str) -> None:
    """Exibe uma confirmação neutra/positiva (ex.: exportação concluída)."""
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Icon.Information)
    box.setWindowTitle(title)
    box.setText(message)
    box.setStandardButtons(QMessageBox.StandardButton.Ok)
    box.exec()


def confirm_action(parent: Optional[QWidget], title: str, message: str) -> bool:
    """Diálogo de confirmação padrão (ex.: excluir template, descartar edição)."""
    reply = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return reply == QMessageBox.StandardButton.Yes
