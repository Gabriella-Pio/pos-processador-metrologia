"""Diálogo simples para título de seção personalizada (uso opcional / templates)."""
from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout

from src.ui.components.app_dialog import AppDialog
from src.ui.components.buttons import PrimaryButton, SecondaryButton
from src.ui.components.inputs import LabeledLineEdit
from src.ui.styles import SPACING


class CustomSectionDialog(AppDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent, window_title="Nova seção personalizada", minimum_width=420)

        layout = self.create_root_layout()
        self.add_dialog_header(
            layout,
            "Adicionar seção",
            "Informe o título da seção personalizada.",
        )
        self._title_field = LabeledLineEdit("Título da seção", required=True)
        layout.addWidget(self._title_field)

        self.add_dialog_divider(layout)
        footer = QHBoxLayout()
        footer.setSpacing(SPACING.sm)
        cancel = SecondaryButton("Cancelar")
        cancel.clicked.connect(self.reject)
        confirm = PrimaryButton("Adicionar")
        confirm.clicked.connect(self._on_confirm)
        footer.addStretch(1)
        footer.addWidget(cancel)
        footer.addWidget(confirm)
        layout.addLayout(footer)

    def _on_confirm(self) -> None:
        self._title_field.mark_touched()
        if not self._title_field.is_valid():
            return
        self.accept()

    def get_title(self) -> str:
        return self._title_field.text().strip()
