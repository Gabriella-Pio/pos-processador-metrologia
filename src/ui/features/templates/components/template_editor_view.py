"""
Editor de templates — estrutura, placeholders [VARIABLE] e textos padrão por seção.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.core.domain.ports import TemplateRepository
from src.core.domain.section_schema import (
    TEMPLATE_VARIABLES,
    merge_saved_template_config,
)
from src.ui.components.buttons import PrimaryButton, SecondaryButton
from src.ui.components.feedback import show_friendly_error, show_info
from src.ui.components.inputs import LabeledLineEdit
from src.ui.components.placeholder_field import PlaceholderTextEdit
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, caption_style, heading_style

_DEFAULT_PROSE_KEY = "default_prose"


class TemplateEditorView(QDialog):
    """Editor visual de template com placeholders institucionais."""

    saved = pyqtSignal(str)

    def __init__(
        self,
        template_repo: TemplateRepository,
        template_id: str = "new",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._repo = template_repo
        self._template_id = template_id if template_id != "new" else self._new_template_id()
        self._is_new = template_id == "new"
        self._content_defaults: dict[str, dict] = {}
        self._active_section_id: str | None = None
        self._loading_defaults = False

        self.setWindowTitle("Editor de Template")
        self.setMinimumSize(1100, 700)

        self._name_field = LabeledLineEdit("Nome do template", required=True)
        if not self._is_new:
            for t in self._repo.list_templates():
                if t["id"] == self._template_id:
                    self._name_field.set_text(t["name"])
                    break

        self._sections_list = QListWidget()
        self._sections_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self._sections_list.currentItemChanged.connect(self._on_section_selected)

        self._defaults_label = QLabel("Texto padrão da seção")
        self._defaults_label.setStyleSheet(heading_style(4))
        self._defaults_hint = QLabel(
            "Use placeholders como {componente} e {operador}. Salvo junto com o template."
        )
        self._defaults_hint.setWordWrap(True)
        self._defaults_hint.setStyleSheet(caption_style())
        self._defaults_editor = PlaceholderTextEdit(multiline=True)
        self._defaults_editor.text_changed.connect(self._on_default_text_changed)

        self._preview = QTextEdit()
        self._preview.setReadOnly(True)

        self._build_ui()
        saved_cfg = self._repo.get_template_config(self._template_id)
        self._content_defaults = {
            section_id: dict(values)
            for section_id, values in self._repo.get_content_defaults(self._template_id).items()
            if isinstance(values, dict)
        }
        self._load_sections(merge_saved_template_config(saved_cfg))
        self._refresh_preview()

    def _new_template_id(self) -> str:
        existing = {t["id"] for t in self._repo.list_templates()}
        index = 1
        while f"custom_{index}" in existing:
            index += 1
        return f"custom_{index}"

    def _build_ui(self) -> None:
        p = PALETTE
        self.setStyleSheet(f"QDialog {{ background-color: {p.bg_surface}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.lg)
        layout.setSpacing(SPACING.md)

        title = QLabel("Estrutura do template")
        title.setStyleSheet(heading_style(2))
        layout.addWidget(title)
        layout.addWidget(self._name_field)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_hint = QLabel("Seções — marque, reordene e selecione para editar o texto padrão")
        left_hint.setStyleSheet(caption_style())
        left_layout.addWidget(left_hint)
        left_layout.addWidget(self._sections_list)

        var_row = QHBoxLayout()
        for var in TEMPLATE_VARIABLES:
            chip = QLabel(f"[{var['key']}]")
            chip.setStyleSheet(
                f"color: {p.senai_blue_light}; background: rgba(74,111,212,0.15); "
                f"border-radius: 6px; padding: 4px 8px; font-size: 11px;"
            )
            chip.setToolTip(var["label"])
            var_row.addWidget(chip)
        var_row.addStretch(1)
        left_layout.addLayout(var_row)

        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(SPACING.md, 0, 0, 0)
        center_layout.setSpacing(SPACING.sm)
        center_layout.addWidget(self._defaults_label)
        center_layout.addWidget(self._defaults_hint)
        center_layout.addWidget(self._defaults_editor, stretch=1)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(SPACING.md, 0, 0, 0)
        preview_label = QLabel("Preview esqueleto")
        preview_label.setStyleSheet(caption_style())
        right_layout.addWidget(preview_label)
        right_layout.addWidget(self._preview)

        splitter.addWidget(left)
        splitter.addWidget(center)
        splitter.addWidget(right)
        splitter.setSizes([320, 420, 360])
        layout.addWidget(splitter, stretch=1)

        footer = QHBoxLayout()
        cancel = SecondaryButton("Cancelar")
        cancel.clicked.connect(self.reject)
        save = PrimaryButton("Salvar template")
        save.clicked.connect(self._on_save)
        footer.addStretch(1)
        footer.addWidget(cancel)
        footer.addWidget(save)
        layout.addLayout(footer)

        self._sections_list.itemChanged.connect(lambda: self._refresh_preview())

    def _load_sections(self, sections: list[dict]) -> None:
        self._sections_list.blockSignals(True)
        self._sections_list.clear()
        for section in sections:
            item = QListWidgetItem(section["label"])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsDragEnabled)
            item.setCheckState(
                Qt.CheckState.Checked if section["enabled"] else Qt.CheckState.Unchecked
            )
            item.setData(Qt.ItemDataRole.UserRole, section["id"])
            self._sections_list.addItem(item)
        self._sections_list.blockSignals(False)
        if self._sections_list.count() > 0:
            self._sections_list.setCurrentRow(0)

    def _on_section_selected(self, current: QListWidgetItem | None, _previous: QListWidgetItem | None) -> None:
        if current is None:
            self._active_section_id = None
            self._defaults_editor.setEnabled(False)
            self._defaults_editor.set_text("")
            self._defaults_label.setText("Texto padrão da seção")
            return
        section_id = current.data(Qt.ItemDataRole.UserRole)
        self._active_section_id = section_id
        self._defaults_editor.setEnabled(True)
        self._defaults_label.setText(f"Texto padrão — {current.text()}")
        self._loading_defaults = True
        section_defaults = self._content_defaults.setdefault(section_id, {})
        prose = section_defaults.get(_DEFAULT_PROSE_KEY, "")
        if not prose and section_defaults:
            prose = "\n".join(
                f"{key}: {value}" for key, value in section_defaults.items() if key != _DEFAULT_PROSE_KEY
            )
        self._defaults_editor.set_text(prose)
        self._loading_defaults = False

    def _on_default_text_changed(self, text: str) -> None:
        if self._loading_defaults or not self._active_section_id:
            return
        section_defaults = self._content_defaults.setdefault(self._active_section_id, {})
        section_defaults[_DEFAULT_PROSE_KEY] = text
        self._refresh_preview()

    def _collect_config(self) -> dict:
        config = {}
        for index in range(self._sections_list.count()):
            item = self._sections_list.item(index)
            section_id = item.data(Qt.ItemDataRole.UserRole)
            config[section_id] = {
                "enabled": item.checkState() == Qt.CheckState.Checked,
                "order": index,
            }
        return config

    def _refresh_preview(self) -> None:
        lines = ["# Preview do template\n"]
        for index in range(self._sections_list.count()):
            item = self._sections_list.item(index)
            if item.checkState() != Qt.CheckState.Checked:
                continue
            title = item.text()
            section_id = item.data(Qt.ItemDataRole.UserRole)
            lines.append(f"\n## {title}")
            prose = self._content_defaults.get(section_id, {}).get(_DEFAULT_PROSE_KEY, "").strip()
            if prose:
                lines.append(prose)
            else:
                lines.append("Texto com placeholders: [CLIENTE] — [COMPONENTE]")
                lines.append("Responsável: [RESPONSAVEL] | Data: [DATA] | Versão: [VERSAO]")
        self._preview.setPlainText("\n".join(lines))

    def _on_save(self) -> None:
        self._name_field.mark_touched()
        if not self._name_field.is_valid():
            return
        config = self._collect_config()
        name = self._name_field.text()
        try:
            self._repo.save_full_template(
                self._template_id,
                config,
                self._content_defaults,
                name.strip(),
            )
        except Exception:
            show_friendly_error(self, "Erro", "Não foi possível salvar o template.")
            return
        show_info(self, "Template salvo", "Estrutura e textos padrão atualizados com sucesso.")
        self.saved.emit(self._template_id)
        self.accept()
