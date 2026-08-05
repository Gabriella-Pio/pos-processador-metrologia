"""Assistente de criação de projeto de medição — tela única, múltiplos PDFs."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from src.core.domain.ports import ReportParser, TemplateRepository
from src.ui.components.buttons import PrimaryButton, SecondaryButton
from src.ui.components.inputs import LabeledLineEdit
from src.ui.features.home.dialogs.import_dialog import DropZone
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, heading_style


class ProjectSetupDialog(QDialog):
    """Modal único: Projeto + Arquivos + Template."""

    def __init__(
        self,
        parser: ReportParser,
        template_repo: TemplateRepository,
        parent=None,
        *,
        overlay: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._parser = parser
        self._template_repo = template_repo
        self._overlay = overlay
        self.setWindowTitle("Novo Projeto de Medição")
        self.setMinimumSize(640, 480)

        self._client_field = LabeledLineEdit("Cliente / Projeto", required=True)
        self._component_field = LabeledLineEdit("Componente avaliado", required=True)
        self._counter_label = QLabel("Nenhum arquivo selecionado")
        self._drop_zone = DropZone(self._counter_label)
        self._drop_zone.setMinimumHeight(120)
        self._files_error = QLabel("")
        self._files_error.hide()
        self._template_combo = QComboBox()
        self._mode_combo = QComboBox()
        self._mode_combo.addItem("Detectar automaticamente", "auto")
        self._mode_combo.addItem("Somente MMC (CALYPSO)", "mmc_only")
        self._mode_combo.addItem("Somente Tomografia (INSP ECT)", "tomo_only")
        self._mode_combo.addItem("Misto (MMC + Tomografia)", "mixed")
        self._confirm_btn = PrimaryButton("Abrir workspace")

        self._build_ui()
        self._load_templates()
        self._wire_signals()

    def set_overlay(self, overlay: QWidget | None) -> None:
        self._overlay = overlay

    def _build_ui(self) -> None:
        p = PALETTE
        self.setStyleSheet(f"QDialog {{ background-color: {p.bg_surface}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.lg)
        layout.setSpacing(SPACING.md)

        title = QLabel("Novo projeto de medição")
        title.setStyleSheet(heading_style(2))

        subtitle = QLabel(
            "Informe o projeto, selecione os PDFs brutos gerados pelos equipamentos ZEISS "
            "e escolha o template. Arraste arquivos ou use o botão abaixo."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(
            f"color: {p.text_secondary}; font-size: {TYPOGRAPHY.size_caption}px; background: transparent;"
        )

        form_row = QHBoxLayout()
        form_row.setSpacing(SPACING.md)
        form_row.addWidget(self._client_field, stretch=1)
        form_row.addWidget(self._component_field, stretch=1)

        browse_row = QHBoxLayout()
        browse_btn = SecondaryButton("Adicionar PDFs…")
        browse_btn.clicked.connect(self._browse_files)
        browse_row.addWidget(browse_btn)
        browse_row.addWidget(self._counter_label)
        browse_row.addStretch()

        self._files_error.setStyleSheet(
            f"color: {p.danger}; font-size: {TYPOGRAPHY.size_caption}px; background: transparent;"
        )

        tmpl_hint = QLabel(
            "Modo do lote e template. Em modo misto, cada PDF usa o template "
            "compatível com sua origem (MMC ou Tomografia)."
        )
        tmpl_hint.setWordWrap(True)
        tmpl_hint.setStyleSheet(f"color: {p.text_secondary}; background: transparent;")

        mode_label = QLabel("Modo do relatório")
        mode_label.setStyleSheet(f"color: {p.text_secondary}; background: transparent;")

        footer = QHBoxLayout()
        cancel_btn = SecondaryButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        self._confirm_btn.clicked.connect(self._on_confirm)
        footer.addStretch(1)
        footer.addWidget(cancel_btn)
        footer.addWidget(self._confirm_btn)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(form_row)
        layout.addWidget(self._drop_zone)
        layout.addLayout(browse_row)
        layout.addWidget(self._files_error)
        layout.addWidget(mode_label)
        layout.addWidget(self._mode_combo)
        layout.addWidget(tmpl_hint)
        layout.addWidget(self._template_combo)
        layout.addStretch()
        layout.addLayout(footer)

    def _wire_signals(self) -> None:
        model = self._drop_zone.model()
        model.rowsInserted.connect(self._on_files_changed)
        model.rowsRemoved.connect(self._on_files_changed)

    def _load_templates(self) -> None:
        self._template_combo.clear()
        for tmpl in self._template_repo.list_templates():
            self._template_combo.addItem(tmpl["name"], tmpl["id"])

    def _on_files_changed(self, *args) -> None:
        if self._drop_zone.count() > 0:
            self._files_error.hide()

    def _set_overlay_visible(self, visible: bool) -> None:
        if self._overlay is None:
            return
        self._overlay.setVisible(visible)
        if visible:
            self._overlay.raise_()
            self.raise_()
            self.activateWindow()

    def _browse_files(self) -> None:
        from PyQt6.QtWidgets import QFileDialog

        self._set_overlay_visible(False)
        paths, _ = QFileDialog.getOpenFileNames(self, "Selecionar PDFs", "", "PDF (*.pdf)")
        self._set_overlay_visible(True)
        for path in paths:
            self._drop_zone.add_path_string(path)

    def _on_confirm(self) -> None:
        valid = True
        if not self._client_field.is_valid():
            self._client_field.show_validation_error()
            valid = False
        else:
            self._client_field.clear_validation_error()

        if not self._component_field.is_valid():
            self._component_field.show_validation_error()
            valid = False
        else:
            self._component_field.clear_validation_error()

        if self._drop_zone.count() == 0:
            self._files_error.setText("Selecione ao menos um arquivo PDF.")
            self._files_error.show()
            valid = False
        else:
            self._files_error.hide()

        if not valid:
            return
        self.accept()

    def get_result(self) -> dict:
        default_component = self._component_field.text().strip()
        pdf_entries = [
            (path, default_component or path.stem)
            for path in self._drop_zone.selected_paths()
        ]

        return {
            "client_project": self._client_field.text(),
            "template_id": self._template_combo.currentData() or "default",
            "report_mode": self._mode_combo.currentData() or "auto",
            "pdf_entries": pdf_entries,
        }
