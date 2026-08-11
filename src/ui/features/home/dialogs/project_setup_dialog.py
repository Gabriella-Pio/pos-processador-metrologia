"""Assistente de criação de projeto de medição — tela única, múltiplos PDFs."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from src.core.domain.ports import ReportParser, TemplateRepository
from src.ui.components.app_dialog import AppDialog
from src.ui.components.buttons import PrimaryButton, SecondaryButton
from src.ui.components.inputs import LabeledLineEdit, ThemedComboBox
from src.ui.features.home.dialogs.import_dialog import DropZone
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, caption_style


class ProjectSetupDialog(AppDialog):
    """Modal único: Projeto + Arquivos + Template."""

    def __init__(
        self,
        parser: ReportParser,
        template_repo: TemplateRepository,
        parent=None,
        *,
        overlay: QWidget | None = None,
    ) -> None:
        super().__init__(parent, window_title="Novo Projeto de Medição", minimum_width=640)
        self.setMinimumHeight(480)
        self._parser = parser
        self._template_repo = template_repo
        self._overlay = overlay

        self._client_field = LabeledLineEdit("Cliente / Projeto", required=True)
        self._component_field = LabeledLineEdit("Componente avaliado", required=True)
        self._counter_label = QLabel("Nenhum arquivo selecionado")
        self._warning_label = QLabel("")
        self._warning_label.setWordWrap(True)
        self._warning_label.hide()
        self._drop_zone = DropZone(self._counter_label, self._warning_label)
        self._drop_zone.setMinimumHeight(120)
        self._files_error = QLabel("")
        self._files_error.hide()
        self._template_combo = ThemedComboBox()
        self._mode_combo = ThemedComboBox()
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
        layout = self.create_root_layout()
        self.add_dialog_header(
            layout,
            "Novo projeto de medição",
            "Informe o projeto, selecione os PDFs brutos gerados pelos equipamentos ZEISS "
            "e escolha o template. Arraste arquivos ou use o botão abaixo.",
        )

        form_row = QHBoxLayout()
        form_row.setSpacing(SPACING.md)
        form_row.addWidget(self._client_field, stretch=1)
        form_row.addWidget(self._component_field, stretch=1)

        browse_row = QHBoxLayout()
        browse_btn = SecondaryButton("Adicionar PDFs…")
        browse_btn.clicked.connect(self._browse_files)
        remove_btn = SecondaryButton("Remover selecionados")
        remove_btn.setToolTip("Remove os PDFs marcados na lista (também Delete/Backspace)")
        remove_btn.clicked.connect(self._drop_zone.remove_selected)
        browse_row.addWidget(browse_btn)
        browse_row.addWidget(remove_btn)
        browse_row.addWidget(self._counter_label)
        browse_row.addStretch()

        self._warning_label.setStyleSheet(
            f"color: {p.warning}; font-size: {TYPOGRAPHY.size_caption}px; background: transparent;"
        )
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

        layout.addLayout(form_row)
        layout.addWidget(self._drop_zone)
        layout.addLayout(browse_row)
        layout.addWidget(self._warning_label)
        layout.addWidget(self._files_error)
        layout.addWidget(mode_label)
        layout.addWidget(self._mode_combo)
        layout.addWidget(tmpl_hint)
        layout.addWidget(self._template_combo)
        layout.addStretch()
        self.add_dialog_divider(layout)
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

    def set_overlay_visible(self, visible: bool) -> None:
        self._set_overlay_visible(visible)

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
        self.set_overlay_visible(True)
        duplicates: list[str] = []
        for path in paths:
            if not self._drop_zone.add_path_string(path):
                duplicates.append(Path(path).name)
        if duplicates:
            self._drop_zone.warn_duplicates(duplicates)

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
            mode = self._mode_combo.currentData()
            if mode != "tomo_only":
                self._files_error.setText("Selecione ao menos um arquivo PDF.")
                self._files_error.show()
                valid = False
            else:
                self._files_error.hide()
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
            "default_component": default_component,
        }
