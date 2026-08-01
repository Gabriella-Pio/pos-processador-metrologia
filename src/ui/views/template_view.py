"""
Tela/Modal de gestão de templates customizados: ativar, desativar e
reordenar seções do relatório. Persistência via ``TemplateRepository``
(JSON), injetada — nenhuma leitura/escrita de arquivo acontece aqui.
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

from src.core.ports import TemplateRepository
from src.ui.components.buttons import PrimaryButton, SecondaryButton
from src.ui.components.feedback import show_friendly_error, show_info
from src.ui.styles import PALETTE, SPACING, caption_style, heading_style

DEFAULT_SECTIONS = [
    {"id": "cover", "label": "Capa", "enabled": True},
    {"id": "control", "label": "Página de Controle Técnico", "enabled": True},
    {"id": "measurements", "label": "Medições", "enabled": True},
    {"id": "tomography", "label": "Tomografia", "enabled": True},
    {"id": "extra_notes", "label": "Notas extras", "enabled": False},
    {"id": "version_history", "label": "Histórico de Versões", "enabled": True},
]


class TemplateView(QDialog):
    """Modal de edição de um template: liga/desliga e reordena seções.

    A reordenação usa o suporte nativo de drag-and-drop do QListWidget
    (``InternalMove``), sem necessidade de lógica manual de índices.
    """

    def __init__(self, template_repository: TemplateRepository, template_id: str = "default", parent=None) -> None:
        super().__init__(parent)
        self._repo = template_repository
        self._template_id = template_id
        self.setWindowTitle("Gerenciar Template")
        self.setMinimumSize(480, 520)

        self._sections_list = QListWidget()
        self._sections_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

        self._build_ui()
        self._load_sections(DEFAULT_SECTIONS)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.md)

        title = QLabel("Seções do relatório")
        title.setStyleSheet(heading_style(2))
        hint = QLabel("Marque as seções desejadas e arraste para reordenar.")
        hint.setStyleSheet(caption_style())

        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addWidget(self._sections_list, stretch=1)
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
        except Exception:  # noqa: BLE001
            show_friendly_error(
                self,
                "Não foi possível salvar o template",
                "Verifique as permissões de escrita do arquivo de configuração.",
            )
            return
        show_info(self, "Template salvo", "As alterações foram salvas com sucesso.")
        self.accept()
