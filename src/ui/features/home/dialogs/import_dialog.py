"""Modal de importação em lote de PDFs — dark edition com drop zone animada."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QResizeEvent
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from src.ui.components.buttons import PrimaryButton, SecondaryButton
from src.ui.components.icons import icon_file_pdf
from src.ui.components.inputs import LabeledLineEdit
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, heading_style


class DropZone(QListWidget):
    """Área de arrastar-e-soltar com animação de hover — restrita a arquivos .pdf."""

    def __init__(self, counter_label: QLabel, parent=None) -> None:
        super().__init__(parent)
        self._counter_label = counter_label
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.setDragEnabled(False)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._empty_hint = QLabel("Arraste PDFs aqui", self)
        self._empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_hint.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._empty_hint.setStyleSheet(
            f"color: {PALETTE.text_muted}; font-size: {TYPOGRAPHY.size_body}px; background: transparent;"
        )
        self._apply_idle_style()
        self._update_counter()

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._empty_hint.setGeometry(self.rect())

    def _apply_idle_style(self) -> None:
        p = PALETTE
        self.setStyleSheet(f"""
            QListWidget {{
                border: 2px dashed {p.border_strong};
                border-radius: {SPACING.radius_md}px;
                background-color: {p.bg_surface_alt};
                color: {p.text_primary};
                padding: {SPACING.md}px;
                font-size: {TYPOGRAPHY.size_body}px;
            }}
            QListWidget::item {{
                padding: 6px 8px;
                border-radius: 4px;
                border-bottom: 1px solid {p.border_subtle};
            }}
            QListWidget::item:selected {{
                background-color: rgba(74, 111, 212, 0.20);
                color: {p.senai_blue_light};
            }}
        """)

    def _apply_hover_style(self) -> None:
        p = PALETTE
        self.setStyleSheet(f"""
            QListWidget {{
                border: 2px dashed {p.senai_blue_light};
                border-radius: {SPACING.radius_md}px;
                background-color: rgba(74, 111, 212, 0.08);
                color: {p.text_primary};
                padding: {SPACING.md}px;
            }}
        """)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            self._apply_hover_style()
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self._apply_idle_style()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        self._apply_idle_style()
        pdf_paths = [
            Path(url.toLocalFile())
            for url in event.mimeData().urls()
            if url.toLocalFile().lower().endswith(".pdf")
        ]
        for path in pdf_paths:
            self._add_path(path)
        event.acceptProposedAction()

    def _add_path(self, path: Path) -> None:
        path_str = str(path.resolve())
        for index in range(self.count()):
            existing = self.item(index)
            if existing is not None and existing.data(Qt.ItemDataRole.UserRole) == path_str:
                return
        item = QListWidgetItem(path.name)
        item.setIcon(icon_file_pdf())
        item.setData(Qt.ItemDataRole.UserRole, path_str)
        self.addItem(item)
        self._update_counter()

    def add_path_string(self, path_str: str) -> None:
        self._add_path(Path(path_str))

    def _update_counter(self) -> None:
        count = self.count()
        self._empty_hint.setVisible(count == 0)
        if count == 0:
            self._counter_label.setText("Nenhum arquivo selecionado")
            self._counter_label.setStyleSheet(
                f"color: {PALETTE.text_muted}; font-size: {TYPOGRAPHY.size_caption}px; background: transparent;"
            )
        else:
            self._counter_label.setText(f"{count} arquivo{'s' if count != 1 else ''} selecionado{'s' if count != 1 else ''}")
            self._counter_label.setStyleSheet(
                f"color: {PALETTE.success}; font-size: {TYPOGRAPHY.size_caption}px; "
                f"font-weight: {TYPOGRAPHY.weight_medium}; background: transparent;"
            )

    def selected_paths(self) -> list[Path]:
        return [Path(self.item(i).data(Qt.ItemDataRole.UserRole)) for i in range(self.count())]


class ImportDialog(QDialog):
    """Fluxo de importação em lote ('Novo PDF / Processar Lote')."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        p = PALETTE
        self.setWindowTitle("Importar Relatórios PDF")
        self.setMinimumSize(540, 520)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {p.bg_surface};
            }}
        """)

        self._client_field = LabeledLineEdit("Cliente / Projeto", required=True)
        self._component_field = LabeledLineEdit("Componente Avaliado", required=True)
        self._counter_label = QLabel("Nenhum arquivo selecionado")
        self._counter_label.setStyleSheet(
            f"color: {p.text_muted}; font-size: {TYPOGRAPHY.size_caption}px; background: transparent;"
        )
        self._drop_zone = DropZone(self._counter_label)
        self._build_ui()

    def _build_ui(self) -> None:
        p = PALETTE
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.lg)
        layout.setSpacing(SPACING.md)

        # Cabeçalho
        title = QLabel("Importar relatórios PDF")
        title.setStyleSheet(heading_style(2))

        subtitle = QLabel("Arraste um ou mais PDFs brutos gerados pelos equipamentos ZEISS, ou clique em 'Selecionar'.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"color: {p.text_secondary}; font-size: {TYPOGRAPHY.size_caption}px; background: transparent;")

        # Placeholder da drop zone
        drop_placeholder = QLabel("Arraste arquivos PDF aqui")
        drop_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_placeholder.setStyleSheet(
            f"color: {p.text_muted}; font-size: {TYPOGRAPHY.size_body}px; "
            f"padding: {SPACING.lg}px; background: transparent;"
        )

        browse_row = QHBoxLayout()
        browse_btn = SecondaryButton("Selecionar arquivos…")
        browse_btn.clicked.connect(self._browse_files)
        browse_row.addWidget(browse_btn)
        browse_row.addWidget(self._counter_label)
        browse_row.addStretch()

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self._drop_zone, stretch=1)
        layout.addLayout(browse_row)

        # Separador
        sep = QLabel()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {p.border};")
        layout.addWidget(sep)

        layout.addWidget(self._client_field)
        layout.addWidget(self._component_field)
        layout.addSpacing(SPACING.sm)
        layout.addLayout(self._build_footer())

    def _build_footer(self) -> QHBoxLayout:
        row = QHBoxLayout()
        cancel_btn = SecondaryButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)

        confirm_btn = PrimaryButton("Importar e continuar →")
        confirm_btn.clicked.connect(self._on_confirm)

        row.addStretch(1)
        row.addWidget(cancel_btn)
        row.addWidget(confirm_btn)
        return row

    def _browse_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Selecionar PDFs", "", "PDF (*.pdf)")
        for path in paths:
            self._drop_zone.add_path_string(path)

    def _on_confirm(self) -> None:
        self._client_field.mark_touched()
        self._component_field.mark_touched()
        if not self._client_field.is_valid() or not self._component_field.is_valid():
            return
        if self._drop_zone.count() == 0:
            return
        self.accept()

    def get_result(self) -> dict:
        return {
            "pdf_paths": self._drop_zone.selected_paths(),
            "client_project": self._client_field.text(),
            "evaluated_component": self._component_field.text(),
        }
