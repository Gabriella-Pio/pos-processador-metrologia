"""
Modal de gestão de templates — seções alinhadas ao generator via section_schema.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from src.core.domain.ports import TemplateRepository
from src.core.domain.section_schema import default_template_sections, merge_saved_template_config
from src.ui.components.buttons import PrimaryButton, SecondaryButton
from src.ui.components.feedback import show_friendly_error, show_info
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, caption_style, heading_style


class TemplateView(QDialog):
    """Modal de edição de template: liga/desliga e reordena seções."""

    def __init__(
        self,
        template_repository: TemplateRepository,
        template_id: str = "default",
        parent=None,
    ) -> None:
        super().__init__(parent)
        p = PALETTE
        self._repo = template_repository
        self._template_id = template_id
        self.setWindowTitle("Gerenciar Template")
        self.setMinimumSize(480, 520)
        self.setStyleSheet(f"QDialog {{ background-color: {p.bg_surface}; }}")

        self._sections_list = QListWidget()
        self._sections_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._sections_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {p.bg_base};
                border: 1px solid {p.border};
                border-radius: {SPACING.radius_md}px;
                color: {p.text_primary};
                outline: none;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 10px 12px;
                border-radius: {SPACING.radius_sm}px;
                border-bottom: 1px solid {p.border_subtle};
                font-size: {TYPOGRAPHY.size_body}px;
            }}
            QListWidget::item:hover {{ background-color: {p.bg_surface_alt}; }}
            QListWidget::item:selected {{
                background-color: rgba(74, 111, 212, 0.20);
                color: {p.senai_blue_light};
            }}
        """)

        self._build_ui()
        saved = self._repo.get_template_config(template_id)
        sections = merge_saved_template_config(saved)
        self._load_sections(sections)

    def _build_ui(self) -> None:
        p = PALETTE
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.lg)
        layout.setSpacing(SPACING.md)

        title = QLabel("Seções do relatório")
        title.setStyleSheet(heading_style(2))
        hint = QLabel("Marque as seções desejadas e arraste para reordenar.")
        hint.setStyleSheet(caption_style())
        drag_hint = QLabel("Arraste os itens para reordenar as seções no PDF final")
        drag_hint.setStyleSheet(
            f"color: {p.text_muted}; font-size: 10px; background: transparent; font-style: italic;"
        )

        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addWidget(self._sections_list, stretch=1)
        layout.addWidget(drag_hint)
        layout.addSpacing(SPACING.sm)
        layout.addLayout(self._build_footer())

    def _build_footer(self) -> QHBoxLayout:
        row = QHBoxLayout()
        cancel_btn = SecondaryButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        save_btn = PrimaryButton("Salvar template")
        save_btn.clicked.connect(self._on_save)
        row.addStretch(1)
        row.addWidget(cancel_btn)
        row.addWidget(save_btn)
        return row

    def _load_sections(self, sections: list[dict]) -> None:
        self._sections_list.clear()
        for section in sections:
            item = QListWidgetItem(section["label"])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if section["enabled"] else Qt.CheckState.Unchecked
            )
            item.setData(Qt.ItemDataRole.UserRole, section["id"])
            self._sections_list.addItem(item)

    def _collect_config(self) -> dict:
        sections_config = {}
        for index in range(self._sections_list.count()):
            item = self._sections_list.item(index)
            section_id = item.data(Qt.ItemDataRole.UserRole)
            sections_config[section_id] = {
                "enabled": item.checkState() == Qt.CheckState.Checked,
                "order": index,
            }
        return sections_config

    def _on_save(self) -> None:
        config = self._collect_config()
        try:
            self._repo.save_template(self._template_id, config)
        except Exception:
            show_friendly_error(
                self,
                "Não foi possível salvar o template",
                "Verifique as permissões de escrita do arquivo de configuração.",
            )
            return
        show_info(self, "Template salvo", "As alterações foram salvas com sucesso.")
        self.accept()
