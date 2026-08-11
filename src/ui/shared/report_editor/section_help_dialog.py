"""Ajuda contextual da edição de seção."""
from __future__ import annotations

from src.ui.components.app_dialog import AppDialog
from src.ui.features.workspace.components.edit_help import build_help_content_widget


class SectionHelpDialog(AppDialog):
    def __init__(self, markdown_text: str, parent=None) -> None:
        super().__init__(parent, window_title="Ajuda — edição de seção", minimum_width=520)
        self.setMinimumHeight(400)

        layout = self.create_root_layout()
        self.add_dialog_header(
            layout,
            "Ajuda da seção",
            "Referência rápida para campos, mídia e tabelas desta seção.",
        )
        self.add_dialog_scroll_content(layout, build_help_content_widget(markdown_text))
        self.add_dialog_footer(layout, primary_label="Fechar")
