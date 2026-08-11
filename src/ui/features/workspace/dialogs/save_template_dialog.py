"""Diálogo para salvar layout atual como template."""
from __future__ import annotations

from PyQt6.QtWidgets import QButtonGroup, QHBoxLayout, QRadioButton, QVBoxLayout

from src.ui.components.app_dialog import AppDialog
from src.ui.components.buttons import PrimaryButton, SecondaryButton
from src.ui.components.inputs import LabeledLineEdit
from src.ui.styles import SPACING


class SaveTemplateDialog(AppDialog):
    def __init__(
        self,
        templates: list[dict],
        current_template_id: str,
        parent=None,
    ) -> None:
        super().__init__(parent, window_title="Salvar como template", minimum_width=460)

        layout = self.create_root_layout()
        self.add_dialog_header(
            layout,
            "Salvar layout como template",
            "Crie um novo template ou atualize o layout do template atual.",
        )

        self._name_field = LabeledLineEdit("Nome do template", required=True)
        current_name = next(
            (t["name"] for t in templates if t["id"] == current_template_id),
            "",
        )
        if current_template_id != "default":
            self._name_field.set_text(current_name)

        self._mode_new = QRadioButton("Criar novo template")
        self._mode_update = QRadioButton("Atualizar template atual")
        self._mode_new.setChecked(current_template_id == "default")
        self._mode_update.setChecked(current_template_id != "default")
        if current_template_id == "default":
            self._mode_update.setEnabled(False)

        group = QButtonGroup(self)
        group.addButton(self._mode_new)
        group.addButton(self._mode_update)

        layout.addWidget(self._name_field)
        layout.addWidget(self._mode_new)
        layout.addWidget(self._mode_update)

        self.add_dialog_divider(layout)
        buttons = QHBoxLayout()
        buttons.setSpacing(SPACING.sm)
        cancel_btn = SecondaryButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        save_btn = PrimaryButton("Salvar")
        save_btn.clicked.connect(self.accept)
        buttons.addStretch(1)
        buttons.addWidget(cancel_btn)
        buttons.addWidget(save_btn)
        layout.addLayout(buttons)

    @property
    def template_name(self) -> str:
        return self._name_field.text().strip()

    @property
    def create_new(self) -> bool:
        return self._mode_new.isChecked()
