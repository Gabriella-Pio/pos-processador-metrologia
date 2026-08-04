"""Diálogo para registrar nova versão do relatório."""
from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout

from src.ui.components.buttons import PrimaryButton, SecondaryButton
from src.ui.components.inputs import LabeledLineEdit
from src.ui.styles import PALETTE, SPACING, heading_style


class VersionRegisterDialog(QDialog):
    def __init__(self, responsible_default: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nova versão")
        self.setMinimumWidth(440)
        self.setStyleSheet(f"QDialog {{ background-color: {PALETTE.bg_surface}; }}")

        title = QLabel("Registrar nova versão")
        title.setStyleSheet(heading_style(3))

        self._responsible_field = LabeledLineEdit("Responsável", required=True)
        self._responsible_field.set_text(responsible_default)
        self._message_field = LabeledLineEdit("Descreva as alterações", required=True)
        self._message_field.field.setPlaceholderText("Ex.: Ajuste na conclusão e novas fotos da seção resultados")

        footer = QHBoxLayout()
        cancel = SecondaryButton("Cancelar")
        cancel.clicked.connect(self.reject)
        confirm = PrimaryButton("Registrar")
        confirm.clicked.connect(self._on_confirm)
        footer.addStretch(1)
        footer.addWidget(cancel)
        footer.addWidget(confirm)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.lg)
        layout.setSpacing(SPACING.md)
        layout.addWidget(title)
        layout.addWidget(self._responsible_field)
        layout.addWidget(self._message_field)
        layout.addLayout(footer)

    def _on_confirm(self) -> None:
        self._responsible_field.mark_touched()
        self._message_field.mark_touched()
        if not self._responsible_field.is_valid() or not self._message_field.is_valid():
            return
        self.accept()

    def get_values(self) -> tuple[str, str]:
        return self._responsible_field.text(), self._message_field.text()
