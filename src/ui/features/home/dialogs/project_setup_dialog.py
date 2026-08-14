"""Assistente de criação de projeto de medição — tela única, múltiplos PDFs."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.core.application.batch_processing import infer_report_mode
from src.core.domain.ports import ReportParser, TemplateRepository
from src.core.parser.source_kind import detect_source_kind
from src.ui.components.app_dialog import AppDialog
from src.ui.components.buttons import PrimaryButton, SecondaryButton
from src.ui.components.inputs import LabeledLineEdit, ThemedComboBox
from src.ui.features.home.dialogs.import_dialog import DropZone
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY


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
        super().__init__(parent, window_title="Novo Projeto de Medição", minimum_width=680)
        self.setMinimumHeight(640)
        self.setMaximumHeight(900)
        self._surface.setMinimumHeight(600)
        self._parser = parser
        self._template_repo = template_repo
        self._overlay = overlay
        self._syncing_template = False

        self._client_field = LabeledLineEdit("Cliente / Projeto", required=True)
        self._component_field = LabeledLineEdit("Componente avaliado", required=True)
        self._counter_label = QLabel("Nenhum arquivo selecionado")
        self._warning_label = QLabel("")
        self._warning_label.setWordWrap(True)
        self._warning_label.hide()
        self._drop_zone = DropZone(self._counter_label, self._warning_label)
        self._files_error = QLabel("")
        self._files_error.hide()
        self._template_combo = ThemedComboBox()
        self._mode_combo = ThemedComboBox()
        self._mode_combo.addItem("Detectar automaticamente", "auto")
        self._mode_combo.addItem("Somente MMC (CALYPSO)", "mmc_only")
        self._mode_combo.addItem("Somente Tomografia (INSP ECT / Bosello)", "tomo_only")
        self._mode_combo.addItem("Misto (MMC + Tomografia)", "mixed")
        self._mode_hint = QLabel("")
        self._mode_hint.setWordWrap(True)
        self._template_hint = QLabel("")
        self._template_hint.setWordWrap(True)
        self._confirm_btn = PrimaryButton("Abrir workspace")

        self._build_ui()
        self._load_templates()
        self._wire_signals()
        self._sync_mode_and_template()

    def set_overlay(self, overlay: QWidget | None) -> None:
        self._overlay = overlay

    def _build_ui(self) -> None:
        p = PALETTE
        layout = self.create_root_layout()
        self.add_dialog_header(
            layout,
            "Novo projeto de medição",
            "Informe o projeto, adicione os PDFs brutos e confirme o modo/template.",
        )

        body = QWidget()
        body.setObjectName("ProjectSetupBody")
        body.setStyleSheet("QWidget#ProjectSetupBody { background: transparent; }")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 4, 0)
        body_layout.setSpacing(SPACING.md)

        form_row = QHBoxLayout()
        form_row.setSpacing(SPACING.md)
        form_row.addWidget(self._client_field, stretch=1)
        form_row.addWidget(self._component_field, stretch=1)
        body_layout.addLayout(form_row)

        browse_row = QHBoxLayout()
        browse_row.setContentsMargins(0, 0, 0, 0)
        browse_row.setSpacing(SPACING.sm)
        browse_btn = SecondaryButton("Adicionar PDFs…")
        browse_btn.clicked.connect(self._browse_files)
        remove_btn = SecondaryButton("Remover selecionados")
        remove_btn.setToolTip("Remove os PDFs marcados na lista (também Delete/Backspace)")
        remove_btn.clicked.connect(self._drop_zone.remove_selected)
        browse_row.addWidget(browse_btn)
        browse_row.addWidget(remove_btn)
        browse_row.addWidget(self._counter_label, stretch=1)

        files_block = QVBoxLayout()
        files_block.setContentsMargins(0, 0, 0, 0)
        files_block.setSpacing(SPACING.sm)
        files_block.addLayout(browse_row)
        files_block.addWidget(self._drop_zone)
        body_layout.addLayout(files_block)

        self._warning_label.setStyleSheet(
            f"color: {p.warning}; font-size: {TYPOGRAPHY.size_caption}px; background: transparent;"
        )
        self._files_error.setStyleSheet(
            f"color: {p.danger}; font-size: {TYPOGRAPHY.size_caption}px; background: transparent;"
        )
        hint_style = f"color: {p.text_secondary}; background: transparent;"
        self._mode_hint.setStyleSheet(hint_style)
        self._template_hint.setStyleSheet(hint_style)

        mode_label = QLabel("Modo do relatório")
        mode_label.setStyleSheet(f"color: {p.text_secondary}; background: transparent;")
        template_label = QLabel("Template do relatório")
        template_label.setStyleSheet(f"color: {p.text_secondary}; background: transparent;")

        body_layout.addWidget(self._warning_label)
        body_layout.addWidget(self._files_error)
        body_layout.addSpacing(SPACING.xs)
        body_layout.addWidget(mode_label)
        body_layout.addWidget(self._mode_combo)
        body_layout.addWidget(self._mode_hint)
        body_layout.addWidget(template_label)
        body_layout.addWidget(self._template_combo)
        body_layout.addWidget(self._template_hint)
        body_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setObjectName("AppDialogInfoScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(body)
        scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(scroll, stretch=1)

        footer = QHBoxLayout()
        cancel_btn = SecondaryButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        self._confirm_btn.clicked.connect(self._on_confirm)
        footer.addStretch(1)
        footer.addWidget(cancel_btn)
        footer.addWidget(self._confirm_btn)

        self.add_dialog_divider(layout)
        layout.addLayout(footer)

    def _wire_signals(self) -> None:
        model = self._drop_zone.model()
        assert model is not None
        model.rowsInserted.connect(self._on_files_changed)
        model.rowsRemoved.connect(self._on_files_changed)
        self._mode_combo.currentIndexChanged.connect(self._sync_mode_and_template)

    def _load_templates(self) -> None:
        self._template_combo.clear()
        for tmpl in self._template_repo.list_templates():
            self._template_combo.addItem(tmpl["name"], tmpl["id"])

    def _detected_kinds(self) -> list[str]:
        kinds: list[str] = []
        for path in self._drop_zone.selected_paths():
            try:
                kinds.append(detect_source_kind(path))
            except Exception:
                kinds.append("calypso")
        return kinds

    def _select_template_id(self, template_id: str) -> None:
        index = self._template_combo.findData(template_id)
        if index < 0 and template_id == "tomografia":
            index = self._template_combo.findData("tomo")
        if index >= 0:
            self._syncing_template = True
            self._template_combo.setCurrentIndex(index)
            self._syncing_template = False

    def _sync_mode_and_template(self, *_args) -> None:
        """Alinha combo de template e dicas ao modo + PDFs selecionados."""
        mode = self._mode_combo.currentData() or "auto"
        kinds = self._detected_kinds()
        inferred = infer_report_mode(kinds) if kinds else None  # type: ignore[arg-type]
        effective = inferred if mode == "auto" and inferred else mode

        if mode == "auto":
            if not kinds:
                self._mode_hint.setText(
                    "Sem PDFs ainda: ao adicionar, o modo será inferido (MMC, Tomografia ou Misto)."
                )
            elif inferred == "tomo_only":
                self._mode_hint.setText(
                    "Detectado: somente Tomografia / Bosello → template Tomografia."
                )
            elif inferred == "mmc_only":
                self._mode_hint.setText(
                    "Detectado: somente MMC / CALYPSO → use o template dimensional abaixo."
                )
            else:
                self._mode_hint.setText(
                    "Detectado: lote misto. Cada PDF usará o template da sua origem "
                    "(MMC ou Tomografia)."
                )
        elif mode == "tomo_only":
            self._mode_hint.setText(
                "Força o fluxo e o template de Tomografia (INSP ECT / Bosello)."
            )
        elif mode == "mmc_only":
            self._mode_hint.setText(
                "Força o fluxo dimensional MMC. PDFs Bosello não combinam com este modo."
            )
        else:
            self._mode_hint.setText(
                "Lote misto: cada PDF usa o template compatível com a origem. "
                "O combo abaixo é só fallback/preferência MMC."
            )

        lock_tomo = effective == "tomo_only" or (
            mode == "auto" and inferred == "tomo_only"
        )
        if lock_tomo:
            self._select_template_id("tomografia")
            self._template_combo.setEnabled(False)
            self._template_hint.setText(
                "Template travado em Tomografia SENAI/Bosello para este modo/detecção."
            )
            return

        self._template_combo.setEnabled(True)
        current = self._template_combo.currentData() or "default"
        # Se o lote virou misto depois de ter travado Tomografia, volta o combo MMC.
        if (
            mode in {"auto", "mixed"}
            and inferred == "mixed"
            and current in {"tomografia", "tomo"}
        ):
            self._select_template_id("default")
            current = "default"
        if mode == "mmc_only" and current in {"tomografia", "tomo"}:
            self._select_template_id("default")
            current = "default"
        if mode == "auto" and inferred == "mmc_only" and current in {"tomografia", "tomo"}:
            self._select_template_id("default")
        if mode == "mixed" or (mode == "auto" and inferred == "mixed"):
            labels = []
            if "calypso" in kinds:
                labels.append("MMC → Template Padrão / custom")
            if "insp_ect" in kinds:
                labels.append("Bosello → Tomografia")
            self._template_hint.setText(
                "Por arquivo: "
                + ("; ".join(labels) if labels else "conforme a origem")
                + ". O combo abaixo é a preferência da parte MMC."
            )
        else:
            self._template_hint.setText(
                "Escolha o layout dimensional (padrão SENAI/ZEISS ou um template seu)."
            )

    def _on_files_changed(self, *args) -> None:
        if self._drop_zone.count() > 0:
            self._files_error.hide()
        self._sync_mode_and_template()

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
        # Garante template coerente no momento do OK.
        self._sync_mode_and_template()
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
