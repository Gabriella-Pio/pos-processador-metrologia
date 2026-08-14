"""Editor de linhas label | valor com reordenação por arraste."""
from __future__ import annotations

import uuid
from typing import Sequence

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QResizeEvent
from PyQt6.QtWidgets import (
    QAbstractScrollArea,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.ui.components.buttons import IconButton, SecondaryButton
from src.ui.components.icons import icon_close
from src.ui.components.placeholder_field import PlaceholderTextEdit
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, caption_style, heading_style


def _micro_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(
        f"color: {PALETTE.text_muted}; font-size: {TYPOGRAPHY.size_caption}px; "
        f"font-weight: {TYPOGRAPHY.weight_medium}; background: transparent;"
    )
    return label


class _TableRowWidget(QFrame):
    """Uma linha no estilo do PDF: rótulo + valor(es) no mesmo card."""

    remove_requested = pyqtSignal()

    def __init__(
        self,
        row: dict[str, str],
        *,
        multiline_value: bool = True,
        allow_remove: bool = False,
        value_columns: Sequence[tuple[str, str]] = (),
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.row_id = row.get("id", "")
        self._value_columns = tuple(value_columns)
        self._value_edits: dict[str, PlaceholderTextEdit] = {}
        self.setObjectName("IdentTableRow")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setStyleSheet(
            f"QFrame#IdentTableRow {{"
            f" background: {PALETTE.bg_surface};"
            f" border: 1px solid {PALETTE.border_subtle};"
            f" border-radius: 8px;"
            f"}}"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        layout.setSpacing(SPACING.sm)

        self._drag_handle = QLabel("⠿")
        self._drag_handle.setToolTip("Arraste para reordenar")
        self._drag_handle.setFixedWidth(18)
        self._drag_handle.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self._drag_handle.setStyleSheet(
            f"color: {PALETTE.text_muted}; font-size: 16px; background: transparent; padding-top: 4px;"
        )
        self._drag_handle.setCursor(Qt.CursorShape.SizeAllCursor)

        fields = QVBoxLayout()
        fields.setContentsMargins(0, 0, 0, 0)
        fields.setSpacing(4)

        fields.addWidget(_micro_label("Característica" if self._value_columns else "Rótulo (como no PDF)"))
        self._label_edit = PlaceholderTextEdit(multiline=False)
        self._label_edit.set_text(row.get("label", ""))
        fields.addWidget(self._label_edit)

        if self._value_columns:
            grid_host = QWidget()
            grid = QGridLayout(grid_host)
            grid.setContentsMargins(0, 4, 0, 0)
            grid.setHorizontalSpacing(SPACING.sm)
            grid.setVerticalSpacing(4)
            for index, (key, title) in enumerate(self._value_columns):
                cell = QVBoxLayout()
                cell.setContentsMargins(0, 0, 0, 0)
                cell.setSpacing(2)
                cell.addWidget(_micro_label(title))
                edit = PlaceholderTextEdit(multiline=False)
                edit.set_text(str(row.get(key, "")))
                self._value_edits[key] = edit
                cell.addWidget(edit)
                grid.addLayout(cell, index // 2, index % 2)
            fields.addWidget(grid_host)
            self._value_edit = None
        else:
            fields.addWidget(_micro_label("Valor"))
            self._value_edit = PlaceholderTextEdit(multiline=multiline_value)
            self._value_edit.set_text(row.get("value", ""))
            fields.addWidget(self._value_edit)

        layout.addWidget(self._drag_handle, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(fields, stretch=1)

        if allow_remove:
            remove_btn = IconButton(icon_close(), "Remover linha")
            remove_btn.setFixedSize(22, 22)
            remove_btn.setIconSize(QSize(12, 12))
            remove_btn.clicked.connect(self.remove_requested.emit)
            layout.addWidget(remove_btn, alignment=Qt.AlignmentFlag.AlignTop)

    def iter_value_edits(self):
        if self._value_edit is not None:
            yield self._value_edit
        yield from self._value_edits.values()

    def to_dict(self) -> dict[str, str]:
        data = {
            "id": self.row_id,
            "label": self._label_edit.get_text(),
        }
        if self._value_columns:
            for key, _title in self._value_columns:
                edit = self._value_edits.get(key)
                data[key] = edit.get_text() if edit is not None else ""
        else:
            data["value"] = self._value_edit.get_text() if self._value_edit is not None else ""
        return data


class DraggableTableRowsEditor(QFrame):
    rows_changed = pyqtSignal(list)
    restore_requested = pyqtSignal()

    def __init__(
        self,
        title: str = "Linhas da tabela",
        *,
        multiline_value: bool = True,
        allow_add_remove: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._loading = False
        self._multiline_value = multiline_value
        self._allow_add_remove = allow_add_remove
        self._value_columns: tuple[tuple[str, str], ...] = ()
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(400)
        self._debounce.timeout.connect(self._emit_rows)

        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(heading_style(4))
        self._title_label.setWordWrap(True)

        self._hint = QLabel(
            "Cada card é uma célula da tabela no PDF. Arraste ⠿ para reordenar; "
            "use ✕ para remover."
        )
        self._hint.setWordWrap(True)
        self._hint.setObjectName("SidebarHint")
        self._hint.setStyleSheet(caption_style())

        self._list = QListWidget()
        self._list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self._list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._list.setSpacing(8)
        self._list.setUniformItemSizes(False)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._list.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self._list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._list.setStyleSheet(
            "QListWidget { background: transparent; border: none; }"
            "QListWidget::item { background: transparent; padding: 0px; }"
        )
        self._list.model().rowsMoved.connect(self._emit_rows)

        self._actions = QVBoxLayout()
        self._actions.setSpacing(SPACING.xs)
        if allow_add_remove:
            add_btn = SecondaryButton("+ Adicionar linha")
            add_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            add_btn.clicked.connect(self._on_add_row)
            self._actions.addWidget(add_btn)
        restore = SecondaryButton("Restaurar linhas padrão")
        restore.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        restore.setToolTip("Volta rótulos, valores e ordem ao padrão do template")
        restore.clicked.connect(self.restore_requested.emit)
        self._actions.addWidget(restore)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.sm)
        layout.addWidget(self._title_label)
        layout.addWidget(self._hint)
        layout.addWidget(self._list)
        layout.addLayout(self._actions)

    def set_value_columns(self, columns: Sequence[tuple[str, str]] | None) -> None:
        """Alterna entre valor único e grade de campos (seções estatísticas)."""
        next_columns = tuple(columns or ())
        if next_columns == self._value_columns:
            return
        current_rows = self.get_rows()
        self._value_columns = next_columns
        if next_columns:
            self._hint.setText(
                "Cada card é uma característica da tabela do PDF. "
                "Edite os campos separados; arraste ⠿ para reordenar."
            )
        else:
            self._hint.setText(
                "Cada card é uma célula da tabela no PDF. Arraste ⠿ para reordenar; "
                "use ✕ para remover."
            )
        if current_rows:
            self.set_rows(current_rows)

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._sync_all_item_widths()

    def get_rows(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for index in range(self._list.count()):
            item = self._list.item(index)
            widget = self._list.itemWidget(item)
            if isinstance(widget, _TableRowWidget):
                rows.append(widget.to_dict())
        return rows

    def has_focused_editor(self) -> bool:
        for index in range(self._list.count()):
            item = self._list.item(index)
            widget = self._list.itemWidget(item)
            if not isinstance(widget, _TableRowWidget):
                continue
            if widget._label_edit.has_editor_focus():
                return True
            for edit in widget.iter_value_edits():
                if edit.has_editor_focus():
                    return True
        return False

    def set_rows(self, rows: list[dict[str, str]]) -> None:
        # Nunca remonta enquanto o usuário digita — o refresh do sumário
        # reenviava as linhas e destruía o foco a cada tecla.
        if self.has_focused_editor():
            return
        incoming = list(rows or [])
        if self.get_rows() == incoming:
            return
        self._loading = True
        self._list.clear()
        for row in incoming:
            self._append_row_item(row, emit_on_ready=False)
        self._loading = False
        QTimer.singleShot(0, self._sync_all_item_widths)

    def _viewport_width(self) -> int:
        return max(80, self._list.viewport().width())

    def _append_row_item(self, row: dict[str, str], *, emit_on_ready: bool = False) -> None:
        item = QListWidgetItem()
        item.setFlags(
            item.flags()
            | Qt.ItemFlag.ItemIsDragEnabled
            | Qt.ItemFlag.ItemIsDropEnabled
            | Qt.ItemFlag.ItemIsEnabled
        )
        widget = _TableRowWidget(
            row,
            multiline_value=self._multiline_value,
            allow_remove=self._allow_add_remove,
            value_columns=self._value_columns,
        )
        widget._label_edit.text_changed.connect(self._schedule_emit_rows)
        widget._label_edit.height_changed.connect(
            lambda w=widget: self._sync_widget_height(w)
        )
        for edit in widget.iter_value_edits():
            edit.text_changed.connect(self._schedule_emit_rows)
            edit.height_changed.connect(lambda w=widget: self._sync_widget_height(w))
        if self._allow_add_remove:
            widget.remove_requested.connect(lambda w=widget: self._remove_widget(w))
        self._list.addItem(item)
        self._list.setItemWidget(item, widget)
        self._sync_item_height(item, widget)
        QTimer.singleShot(0, lambda w=widget: self._sync_widget_height(w))
        if emit_on_ready:
            self._emit_rows()

    def _on_add_row(self) -> None:
        row_id = f"custom_{uuid.uuid4().hex[:8]}"
        row: dict[str, str] = {"id": row_id, "label": "Novo campo"}
        if self._value_columns:
            for key, _title in self._value_columns:
                row[key] = ""
        else:
            row["value"] = ""
        self._append_row_item(row, emit_on_ready=True)

    def _remove_widget(self, widget: _TableRowWidget) -> None:
        item = self._item_for_widget(widget)
        if item is None:
            return
        row = self._list.row(item)
        if row >= 0:
            self._list.takeItem(row)
            self._emit_rows()

    def _item_for_widget(self, widget: _TableRowWidget) -> QListWidgetItem | None:
        for index in range(self._list.count()):
            item = self._list.item(index)
            if item is not None and self._list.itemWidget(item) is widget:
                return item
        return None

    def _sync_widget_height(self, widget: _TableRowWidget) -> None:
        item = self._item_for_widget(widget)
        if item is None:
            return
        self._sync_item_height(item, widget)

    def _sync_all_item_widths(self) -> None:
        for index in range(self._list.count()):
            item = self._list.item(index)
            widget = self._list.itemWidget(item)
            if isinstance(widget, _TableRowWidget):
                self._sync_item_height(item, widget)

    def _sync_item_height(self, item: QListWidgetItem, widget: _TableRowWidget) -> None:
        try:
            if self._list.row(item) < 0:
                return
            width = self._viewport_width()
            widget.setMaximumWidth(width)
            widget.setFixedWidth(width)
            widget.adjustSize()
            hint = widget.sizeHint()
            min_h = 140 if self._value_columns else 88
            height = max(hint.height(), widget.minimumSizeHint().height(), min_h)
            item.setSizeHint(QSize(width, height))
        except RuntimeError:
            return

    def has_pending_emit(self) -> bool:
        return self._debounce.isActive()

    def _schedule_emit_rows(self, *_args) -> None:
        if self._loading:
            return
        self._debounce.start()

    def _emit_rows(self, *_args) -> None:
        if self._loading:
            return
        self.rows_changed.emit(self.get_rows())
