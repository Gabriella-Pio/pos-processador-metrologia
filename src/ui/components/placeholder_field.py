"""Campo de texto com placeholders `{chave}` — completer e chips removíveis."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (
    QCompleter,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.core.domain.placeholder_utils import PLACEHOLDER_CATALOG, extract_placeholders, placeholder_label, remove_placeholder
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY


class _PlaceholderChip(QPushButton):
    remove_requested = pyqtSignal(str)

    def __init__(self, key: str, parent=None) -> None:
        super().__init__(parent)
        self._key = key
        self.setText(f"{{{key}}} ✕")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(placeholder_label(key))
        self.clicked.connect(lambda: self.remove_requested.emit(self._key))
        self.setStyleSheet(
            f"QPushButton {{ background: {PALETTE.bg_surface_alt}; color: {PALETTE.senai_blue_light}; "
            f"border: 1px solid {PALETTE.border_subtle}; border-radius: 10px; padding: 2px 8px; "
            f"font-size: {TYPOGRAPHY.size_caption}px; }}"
        )


class _PlaceholderPopup(QListWidget):
    item_chosen = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMaximumHeight(220)
        self.setMinimumWidth(240)
        self.setStyleSheet(
            f"QListWidget {{ background: {PALETTE.bg_surface}; color: {PALETTE.text_primary}; "
            f"border: 1px solid {PALETTE.border_subtle}; border-radius: 6px; "
            f"font-size: {TYPOGRAPHY.size_body}px; padding: 4px; }}"
            f"QListWidget::item {{ padding: 6px 8px; border-radius: 4px; }}"
            f"QListWidget::item:selected {{ background: {PALETTE.bg_surface_alt}; "
            f"color: {PALETTE.senai_blue_light}; }}"
        )
        for key, label in PLACEHOLDER_CATALOG:
            self.addItem(f"{{{key}}} — {label}")
        self.itemClicked.connect(self._on_item_clicked)

    def _on_item_clicked(self, item) -> None:
        text = item.text()
        key = text.split("}", 1)[0].strip("{")
        self.item_chosen.emit(key)
        self.hide()


class PlaceholderTextEdit(QFrame):
    text_changed = pyqtSignal(str)

    def __init__(self, multiline: bool = True, parent=None) -> None:
        super().__init__(parent)
        self._loading = False
        self._completer = None
        self._popup: _PlaceholderPopup | None = None
        self._brace_pos: int | None = None

        completer_keys = [f"{{{key}}}" for key, _ in PLACEHOLDER_CATALOG]

        if multiline:
            self._editor: QLineEdit | QTextEdit = QTextEdit()
            self._editor.setMinimumHeight(72)
            self._editor.textChanged.connect(self._on_text_changed)
        else:
            self._editor = QLineEdit()
            self._editor.textChanged.connect(self._on_text_changed)

        completer = QCompleter(completer_keys)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        if isinstance(self._editor, QLineEdit):
            self._editor.setCompleter(completer)
        self._completer = completer

        self._chips_host = QWidget()
        self._chips_layout = QHBoxLayout(self._chips_host)
        self._chips_layout.setContentsMargins(0, 0, 0, 0)
        self._chips_layout.setSpacing(SPACING.xs)
        self._chips_layout.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.xs)
        layout.addWidget(self._editor)
        layout.addWidget(self._chips_host)

    def set_text(self, value: str) -> None:
        self._loading = True
        if isinstance(self._editor, QTextEdit):
            self._editor.setPlainText(value)
        else:
            self._editor.setText(value)
        self._loading = False
        self._rebuild_chips()

    def get_text(self) -> str:
        if isinstance(self._editor, QTextEdit):
            return self._editor.toPlainText()
        return self._editor.text()

    def _on_text_changed(self) -> None:
        if self._loading:
            return
        text = self.get_text()
        if text.endswith("{") and self._completer is not None:
            if isinstance(self._editor, QLineEdit):
                self._completer.complete()
            else:
                self._show_text_popup()
        self._rebuild_chips()
        self.text_changed.emit(text)

    def _show_text_popup(self) -> None:
        if not isinstance(self._editor, QTextEdit):
            return
        cursor = self._editor.textCursor()
        self._brace_pos = cursor.position() - 1
        if self._popup is None:
            self._popup = _PlaceholderPopup(self._editor)
            self._popup.item_chosen.connect(self._insert_placeholder_key)
        global_pos = self._editor.mapToGlobal(self._editor.cursorRect().bottomLeft())
        self._popup.setMinimumWidth(max(240, self._editor.width() // 2))
        self._popup.move(global_pos)
        self._popup.show()
        self._popup.setFocus()

    def _insert_placeholder_key(self, key: str) -> None:
        if not isinstance(self._editor, QTextEdit):
            return
        cursor = self._editor.textCursor()
        if self._brace_pos is not None and self._brace_pos >= 0:
            cursor.setPosition(self._brace_pos)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
        cursor.insertText(f"{{{key}}}")
        self._editor.setTextCursor(cursor)
        self._brace_pos = None
        self._rebuild_chips()
        self.text_changed.emit(self.get_text())

    def _rebuild_chips(self) -> None:
        while self._chips_layout.count() > 1:
            item = self._chips_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for key in extract_placeholders(self.get_text()):
            chip = _PlaceholderChip(key)
            chip.remove_requested.connect(self._remove_placeholder)
            self._chips_layout.insertWidget(self._chips_layout.count() - 1, chip)

    def _remove_placeholder(self, key: str) -> None:
        self.set_text(remove_placeholder(self.get_text(), key))
        self.text_changed.emit(self.get_text())
