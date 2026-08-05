"""Editor de linhas da tabela de medições (Resultados)."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from src.core.domain.report_field_registry import MEDICAO_COLUMNS
from src.ui.components.buttons import SecondaryButton
from src.ui.styles import SPACING, heading_style


class MedicoesTableEditor(QFrame):
    rows_changed = pyqtSignal(list)
    restore_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._loading = False
        self._columns = [col[0] for col in MEDICAO_COLUMNS]
        self._headers = [col[1] for col in MEDICAO_COLUMNS]

        title = QLabel("Tabela de medições")
        title.setStyleSheet(heading_style(4))

        self._table = QTableWidget(0, len(self._columns))
        self._table.setHorizontalHeaderLabels(self._headers)
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, len(self._columns)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self._table.verticalHeader().setDefaultSectionSize(32)
        self._table.setAlternatingRowColors(True)
        self._table.setWordWrap(False)
        self._table.setMinimumHeight(220)
        self._table.cellChanged.connect(self._on_cell_changed)

        btn_row = QHBoxLayout()
        self._add_btn = SecondaryButton("+ Linha")
        self._add_btn.clicked.connect(self._add_row)
        self._restore_btn = SecondaryButton("Restaurar original")
        self._restore_btn.clicked.connect(self.restore_requested.emit)
        btn_row.addWidget(self._add_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(self._restore_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, SPACING.sm, 0, 0)
        layout.setSpacing(SPACING.xs)
        layout.addWidget(title)
        layout.addWidget(self._table)
        layout.addLayout(btn_row)

    def set_rows(self, rows: list[dict[str, str]]) -> None:
        self._loading = True
        self._table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            for col_idx, col_key in enumerate(self._columns):
                item = QTableWidgetItem(row.get(col_key, ""))
                self._table.setItem(row_idx, col_idx, item)
        self._loading = False

    def _on_cell_changed(self, _row: int, _col: int) -> None:
        if self._loading:
            return
        self.rows_changed.emit(self.get_rows())

    def _add_row(self) -> None:
        row_idx = self._table.rowCount()
        self._loading = True
        self._table.insertRow(row_idx)
        defaults = {
            "caracteristica": "Nova característica",
            "tipo": "Dimensão",
            "valor_medido": "0",
            "nominal": "0",
            "tol_superior": "0",
            "tol_inferior": "0",
            "desvio": "0",
            "status": "Dentro",
        }
        for col_idx, col_key in enumerate(self._columns):
            self._table.setItem(row_idx, col_idx, QTableWidgetItem(defaults.get(col_key, "")))
        self._loading = False
        self.rows_changed.emit(self.get_rows())

    def get_rows(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for row_idx in range(self._table.rowCount()):
            row: dict[str, str] = {}
            for col_idx, col_key in enumerate(self._columns):
                item = self._table.item(row_idx, col_idx)
                row[col_key] = item.text() if item else ""
            rows.append(row)
        return rows
