"""Diálogo para adicionar seção personalizada ao sumário."""
from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout

from src.ui.components.buttons import PrimaryButton, SecondaryButton
from src.ui.components.inputs import LabeledLineEdit
from src.ui.styles import PALETTE, SPACING, heading_style


class CustomSectionDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nova seção personalizada")
        self.setMinimumWidth(420)
        self.setStyleSheet(f"QDialog {{ background-color: {PALETTE.bg_surface}; }}")

        title = QLabel("Adicionar seção")
        title.setStyleSheet(heading_style(3))
        self._title_field = LabeledLineEdit("Título da seção", required=True)

        footer = QHBoxLayout()
        cancel = SecondaryButton("Cancelar")
        cancel.clicked.connect(self.reject)
        confirm = PrimaryButton("Adicionar")
        confirm.clicked.connect(self._on_confirm)
        footer.addStretch(1)
        footer.addWidget(cancel)
        footer.addWidget(confirm)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.lg)
        layout.setSpacing(SPACING.md)
        layout.addWidget(title)
        layout.addWidget(self._title_field)
        layout.addLayout(footer)

    def _on_confirm(self) -> None:
        self._title_field.mark_touched()
        if not self._title_field.is_valid():
            return
        self.accept()

    def get_title(self) -> str:
        return self._title_field.text()
