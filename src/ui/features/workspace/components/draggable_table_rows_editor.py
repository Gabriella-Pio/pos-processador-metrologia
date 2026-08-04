"""Editor de linhas label | valor com reordenação por arraste."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QVBoxLayout

from src.ui.components.buttons import SecondaryButton
from src.ui.components.placeholder_field import PlaceholderTextEdit
from src.ui.styles import SPACING, heading_style


class _TableRowWidget(QFrame):
    def __init__(self, row: dict[str, str], parent=None) -> None:
        super().__init__(parent)
        self.row_id = row.get("id", "")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.xs, SPACING.xs, SPACING.xs, SPACING.xs)
        layout.setSpacing(SPACING.sm)

        self._drag_handle = QLabel("⠿")
        self._drag_handle.setToolTip("Arraste para reordenar")
        self._drag_handle.setFixedWidth(16)

        self._label_edit = PlaceholderTextEdit(multiline=False)
        self._label_edit.set_text(row.get("label", ""))
        self._value_edit = PlaceholderTextEdit(multiline=False)
        self._value_edit.set_text(row.get("value", ""))

        layout.addWidget(self._drag_handle)
        layout.addWidget(self._label_edit, stretch=2)
        layout.addWidget(self._value_edit, stretch=3)

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.row_id,
            "label": self._label_edit.get_text(),
            "value": self._value_edit.get_text(),
        }


class DraggableTableRowsEditor(QFrame):
    rows_changed = pyqtSignal(list)
    restore_requested = pyqtSignal()

    def __init__(self, title: str = "Linhas da tabela", parent=None) -> None:
        super().__init__(parent)
        self._loading = False

        title_label = QLabel(title)
        title_label.setStyleSheet(heading_style(4))

        self._list = QListWidget()
        self._list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self._list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._list.setSpacing(4)
        self._list.model().rowsMoved.connect(self._emit_rows)

        btn_row = QHBoxLayout()
        restore = SecondaryButton("Restaurar ordem padrão")
        restore.clicked.connect(self.restore_requested.emit)
        btn_row.addStretch(1)
        btn_row.addWidget(restore)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, SPACING.sm, 0, 0)
        layout.setSpacing(SPACING.xs)
        layout.addWidget(title_label)
        layout.addWidget(self._list)
        layout.addLayout(btn_row)

    def set_rows(self, rows: list[dict[str, str]]) -> None:
        self._loading = True
        self._list.clear()
        for row in rows:
            item = QListWidgetItem()
            item.setFlags(
                item.flags()
                | Qt.ItemFlag.ItemIsDragEnabled
                | Qt.ItemFlag.ItemIsDropEnabled
                | Qt.ItemFlag.ItemIsEnabled
            )
            widget = _TableRowWidget(row)
            widget._label_edit.text_changed.connect(self._emit_rows)
            widget._value_edit.text_changed.connect(self._emit_rows)
            item.setSizeHint(widget.sizeHint())
            self._list.addItem(item)
            self._list.setItemWidget(item, widget)
        self._loading = False

    def get_rows(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for index in range(self._list.count()):
            item = self._list.item(index)
            widget = self._list.itemWidget(item)
            if isinstance(widget, _TableRowWidget):
                rows.append(widget.to_dict())
        return rows

    def _emit_rows(self, *_args) -> None:
        if self._loading:
            return
        self.rows_changed.emit(self.get_rows())
