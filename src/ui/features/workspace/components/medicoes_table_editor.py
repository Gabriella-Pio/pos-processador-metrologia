"""Editor de linhas da tabela de medições (Resultados) — cards, como nas seções unificadas."""
from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QVBoxLayout

from src.ui.shared.report_editor.draggable_table_rows_editor import DraggableTableRowsEditor

# Característica vai no rótulo do card; demais colunas em grade 2×N.
MEDICAO_VALUE_COLUMNS: tuple[tuple[str, str], ...] = (
    ("tipo", "Tipo"),
    ("valor_medido", "Medido"),
    ("nominal", "Nominal"),
    ("tol_superior", "Tol. +"),
    ("tol_inferior", "Tol. -"),
    ("desvio", "Desvio"),
    ("status", "Status"),
)


def _to_editor_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for index, row in enumerate(rows or []):
        item = {
            "id": str(row.get("id") or f"med_{index}"),
            "label": str(row.get("caracteristica", "")),
        }
        for key, _title in MEDICAO_VALUE_COLUMNS:
            item[key] = str(row.get(key, ""))
        out.append(item)
    return out


def _from_editor_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in rows or []:
        item = {"caracteristica": str(row.get("label", ""))}
        for key, _title in MEDICAO_VALUE_COLUMNS:
            item[key] = str(row.get(key, ""))
        out.append(item)
    return out


class MedicoesTableEditor(QFrame):
    rows_changed = pyqtSignal(list)
    restore_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._loading = False
        self._editor = DraggableTableRowsEditor(
            "Tabela de medições",
            multiline_value=False,
            allow_add_remove=True,
        )
        self._editor.set_value_columns(MEDICAO_VALUE_COLUMNS)
        self._editor.rows_changed.connect(self._on_rows_changed)
        self._editor.restore_requested.connect(self.restore_requested.emit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._editor)

    def set_rows(self, rows: list[dict[str, str]]) -> None:
        self._loading = True
        self._editor.set_rows(_to_editor_rows(rows))
        self._loading = False

    def get_rows(self) -> list[dict[str, str]]:
        return _from_editor_rows(self._editor.get_rows())

    def has_focused_editor(self) -> bool:
        return self._editor.has_focused_editor()

    def has_pending_emit(self) -> bool:
        return self._editor.has_pending_emit()

    def _on_rows_changed(self, rows: list[dict[str, str]]) -> None:
        if self._loading:
            return
        self.rows_changed.emit(_from_editor_rows(rows))
