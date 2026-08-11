"""Diálogo para registrar nova versão do relatório."""
from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout

from src.ui.components.app_dialog import AppDialog
from src.ui.components.buttons import PrimaryButton, SecondaryButton
from src.ui.components.inputs import LabeledLineEdit
from src.ui.styles import SPACING


class VersionRegisterDialog(AppDialog):
    def __init__(self, responsible_default: str = "", parent=None) -> None:
        super().__init__(parent, window_title="Nova versão", minimum_width=480)

        layout = self.create_root_layout()
        self.add_dialog_header(
            layout,
            "Registrar nova versão",
            "Informe o responsável e descreva as alterações desta revisão.",
        )

        self._responsible_field = LabeledLineEdit("Responsável", required=True)
        self._responsible_field.set_text(responsible_default)
        self._message_field = LabeledLineEdit("Descreva as alterações", required=True)
        self._message_field.field.setPlaceholderText(
            "Ex.: Ajuste na conclusão e novas fotos da seção resultados"
        )
        layout.addWidget(self._responsible_field)
        layout.addWidget(self._message_field)

        self.add_dialog_divider(layout)
        footer = QHBoxLayout()
        footer.setSpacing(SPACING.sm)
        cancel = SecondaryButton("Cancelar")
        cancel.clicked.connect(self.reject)
        confirm = PrimaryButton("Registrar")
        confirm.clicked.connect(self._on_confirm)
        footer.addStretch(1)
        footer.addWidget(cancel)
        footer.addWidget(confirm)
        layout.addLayout(footer)

    def _on_confirm(self) -> None:
        self._responsible_field.mark_touched()
        self._message_field.mark_touched()
        if not self._responsible_field.is_valid() or not self._message_field.is_valid():
            return
        self.accept()

    def get_values(self) -> tuple[str, str]:
        return self._responsible_field.text(), self._message_field.text()
