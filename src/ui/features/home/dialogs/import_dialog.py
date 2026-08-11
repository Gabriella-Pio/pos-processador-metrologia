"""Modal de importação em lote de PDFs — dark edition com drop zone animada."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent, QKeyEvent, QResizeEvent
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QSizePolicy,
    QVBoxLayout,
)

from src.ui.components.app_dialog import AppDialog
from src.ui.components.buttons import PrimaryButton, SecondaryButton
from src.ui.components.icons import icon_close, icon_file_pdf
from src.ui.components.inputs import LabeledLineEdit
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY


class _PdfListRow(QFrame):
    remove_requested = pyqtSignal(str)
    _ROW_HEIGHT = 36

    def __init__(self, path: Path, parent=None) -> None:
        super().__init__(parent)
        self.path_str = str(path.resolve())
        self.setMinimumHeight(self._ROW_HEIGHT)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 6, 6)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        icon = QLabel()
        icon.setPixmap(icon_file_pdf().pixmap(16, 16))
        icon.setFixedSize(16, 16)
        name = QLabel(path.name)
        name.setToolTip(self.path_str)
        name.setWordWrap(False)
        name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        name.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        name.setStyleSheet(f"color: {PALETTE.text_primary}; background: transparent;")
        remove_btn = IconButton(icon_close(), "Remover arquivo")
        remove_btn.setFixedSize(22, 22)
        remove_btn.setIconSize(QSize(12, 12))
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.path_str))
        layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(name, stretch=1, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(remove_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(super().sizeHint().width(), self._ROW_HEIGHT)


class DropZone(QListWidget):
    """Área de arrastar-e-soltar com animação de hover — restrita a arquivos .pdf."""

    def __init__(
        self,
        counter_label: QLabel,
        warning_label: QLabel | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._counter_label = counter_label
        self._warning_label = warning_label
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

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.remove_selected()
            event.accept()
            return
        super().keyPressEvent(event)

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
                padding: 0px;
                margin: 2px 0px;
                border-radius: 4px;
                border-bottom: 1px solid {p.border_subtle};
                min-height: {_PdfListRow._ROW_HEIGHT}px;
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
            QListWidget::item {{
                padding: 0px;
                margin: 2px 0px;
                border-radius: 4px;
                min-height: {_PdfListRow._ROW_HEIGHT}px;
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
        duplicates: list[str] = []
        for path in pdf_paths:
            if not self._add_path(path):
                duplicates.append(path.name)
        if duplicates:
            self.warn_duplicates(duplicates)
        event.acceptProposedAction()

    def _add_path(self, path: Path) -> bool:
        """Adiciona o PDF. Retorna False se já estava na lista."""
        path_str = str(path.resolve())
        for index in range(self.count()):
            existing = self.item(index)
            if existing is not None and existing.data(Qt.ItemDataRole.UserRole) == path_str:
                return False
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, path_str)
        item.setToolTip(path_str)
        row = _PdfListRow(path)
        row.remove_requested.connect(self._remove_path)
        self.addItem(item)
        self.setItemWidget(item, row)
        item.setSizeHint(QSize(self.viewport().width(), _PdfListRow._ROW_HEIGHT))
        self._update_counter()
        if self._warning_label is not None:
            self._warning_label.clear()
            self._warning_label.hide()
        return True

    def add_path_string(self, path_str: str) -> bool:
        return self._add_path(Path(path_str))

    def _remove_path(self, path_str: str) -> None:
        for index in range(self.count()):
            item = self.item(index)
            if item is not None and item.data(Qt.ItemDataRole.UserRole) == path_str:
                self.takeItem(index)
                break
        self._update_counter()
        if self._warning_label is not None:
            self._warning_label.clear()
            self._warning_label.hide()

    def remove_selected(self) -> None:
        for item in list(self.selectedItems()):
            row = self.row(item)
            self.takeItem(row)
        self._update_counter()
        if self._warning_label is not None:
            self._warning_label.clear()
            self._warning_label.hide()

    def warn_duplicates(self, names: list[str]) -> None:
        if len(names) == 1:
            msg = f"Arquivo já importado na lista: {names[0]}"
        else:
            msg = f"{len(names)} arquivos já estavam na lista e foram ignorados."
        if self._warning_label is not None:
            self._warning_label.setText(msg)
            self._warning_label.show()
        else:
            QMessageBox.information(self.window(), "Arquivo já importado", msg)

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


class ImportDialog(AppDialog):
    """Fluxo de importação em lote ('Novo PDF / Processar Lote')."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent, window_title="Importar Relatórios PDF", minimum_width=540)
        self.setMinimumHeight(560)
        self._surface.setMinimumHeight(520)

        self._client_field = LabeledLineEdit("Cliente / Projeto", required=True)
        self._component_field = LabeledLineEdit("Componente Avaliado", required=True)
        self._counter_label = QLabel("Nenhum arquivo selecionado")
        self._counter_label.setStyleSheet(
            f"color: {PALETTE.text_muted}; font-size: {TYPOGRAPHY.size_caption}px; background: transparent;"
        )
        self._warning_label = QLabel("")
        self._warning_label.setWordWrap(True)
        self._warning_label.setStyleSheet(
            f"color: {PALETTE.warning}; font-size: {TYPOGRAPHY.size_caption}px; background: transparent;"
        )
        self._drop_zone = DropZone(self._counter_label, self._warning_label)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = self.create_root_layout()
        self.add_dialog_header(
            layout,
            "Importar relatórios PDF",
            "Arraste um ou mais PDFs brutos gerados pelos equipamentos ZEISS, ou clique em 'Selecionar'.",
        )

        browse_row = QHBoxLayout()
        browse_btn = SecondaryButton("Selecionar arquivos…")
        browse_btn.clicked.connect(self._browse_files)
        remove_btn = SecondaryButton("Remover selecionados")
        remove_btn.setToolTip("Remove os PDFs marcados na lista (também Delete/Backspace)")
        remove_btn.clicked.connect(self._drop_zone.remove_selected)
        browse_row.addWidget(browse_btn)
        browse_row.addWidget(remove_btn)
        browse_row.addWidget(self._counter_label)
        browse_row.addStretch()

        layout.addWidget(self._drop_zone, stretch=1)
        layout.addLayout(browse_row)
        layout.addWidget(self._warning_label)
        layout.addWidget(self._client_field)
        layout.addWidget(self._component_field)

        self.add_dialog_divider(layout)
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
        duplicates: list[str] = []
        for path in paths:
            if not self._drop_zone.add_path_string(path):
                duplicates.append(Path(path).name)
        if duplicates:
            self._drop_zone.warn_duplicates(duplicates)

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
