"""Modal de importação em lote de PDFs brutos, com suporte a Drag-and-Drop."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QVBoxLayout,
)

from src.ui.components.buttons import PrimaryButton, SecondaryButton
from src.ui.components.inputs import LabeledLineEdit
from src.ui.styles import PALETTE, SPACING, heading_style


class DropZone(QListWidget):
    """Área de arrastar-e-soltar reutilizável, restrita a arquivos .pdf."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        p = PALETTE
        self.setStyleSheet(f"""
            QListWidget {{
                border: 2px dashed {p.border_strong};
                border-radius: {SPACING.radius_md}px;
                background-color: {p.surface_alt};
                padding: {SPACING.md}px;
            }}
        """)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        pdf_paths = [
            Path(url.toLocalFile())
            for url in event.mimeData().urls()
            if url.toLocalFile().lower().endswith(".pdf")
        ]
        for path in pdf_paths:
            self.addItem(str(path))
        event.acceptProposedAction()

    def selected_paths(self) -> list[Path]:
        return [Path(self.item(i).text()) for i in range(self.count())]


class ImportDialog(QDialog):
    """Fluxo de importação em lote ('Novo PDF').

    Não contém lógica de parsing — apenas coleta arquivos e metadados
    obrigatórios (Cliente/Projeto, Componente Avaliado) e devolve tudo
    através de ``get_result()`` para o chamador (``MainWindow``) decidir
    o que fazer, mantendo esta classe focada só em UI.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Novo PDF / Processar Lote")
        self.setMinimumSize(520, 480)
        self._client_field = LabeledLineEdit("Cliente / Projeto", required=True)
        self._component_field = LabeledLineEdit("Componente Avaliado", required=True)
        self._drop_zone = DropZone()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.md)

        title = QLabel("Importar relatórios PDF")
        title.setStyleSheet(heading_style(2))
        subtitle = QLabel("Arraste um ou mais PDFs brutos gerados pelos equipamentos ZEISS.")
        subtitle.setWordWrap(True)

        browse_btn = SecondaryButton("Selecionar arquivos...")
        browse_btn.clicked.connect(self._browse_files)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self._drop_zone, stretch=1)
        layout.addWidget(browse_btn)
        layout.addWidget(self._client_field)
        layout.addWidget(self._component_field)
        layout.addLayout(self._build_footer())

    def _build_footer(self) -> QHBoxLayout:
        row = QHBoxLayout()
        cancel_btn = SecondaryButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)

        confirm_btn = PrimaryButton("Importar e continuar")
        confirm_btn.clicked.connect(self._on_confirm)

        row.addStretch(1)
        row.addWidget(cancel_btn)
        row.addWidget(confirm_btn)
        return row

    def _browse_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Selecionar PDFs", "", "PDF (*.pdf)")
        for path in paths:
            self._drop_zone.addItem(path)

    def _on_confirm(self) -> None:
        self._client_field.mark_touched()
        self._component_field.mark_touched()
        if not self._client_field.is_valid() or not self._component_field.is_valid():
            return
        if self._drop_zone.count() == 0:
            return
        self.accept()

    def get_result(self) -> dict:
        """Retorna os dados coletados após ``exec()`` ter sido aceito."""
        return {
            "pdf_paths": self._drop_zone.selected_paths(),
            "client_project": self._client_field.text(),
            "evaluated_component": self._component_field.text(),
        }
