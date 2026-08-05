"""Campo de texto com placeholders `{chave}` — completer, chips e altura dinâmica."""
from __future__ import annotations

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QFontMetrics, QTextCursor, QTextOption
from PyQt6.QtWidgets import (
    QCompleter,
    QFrame,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QSizePolicy,
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
    """Editor com placeholders; altura cresce com o texto (e com chips)."""

    text_changed = pyqtSignal(str)
    height_changed = pyqtSignal()

    _MIN_LINES_COMPACT = 1
    _MIN_LINES_MULTILINE = 2
    _MAX_HEIGHT = 360
    _PAD_Y = 14

    def __init__(self, multiline: bool = True, parent=None) -> None:
        super().__init__(parent)
        self._loading = False
        self._multiline = multiline
        self._completer = None
        self._popup: _PlaceholderPopup | None = None
        self._brace_pos: int | None = None

        completer_keys = [f"{{{key}}}" for key, _ in PLACEHOLDER_CATALOG]

        self._editor = QTextEdit()
        self._editor.setAcceptRichText(False)
        self._editor.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self._editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._editor.setTabChangesFocus(True)
        self._editor.textChanged.connect(self._on_text_changed)
        self._editor.document().documentLayout().documentSizeChanged.connect(
            lambda _size: self._adjust_editor_height()
        )

        completer = QCompleter(completer_keys)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
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

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._adjust_editor_height()

    def set_text(self, value: str) -> None:
        self._loading = True
        self._editor.setPlainText(value or "")
        self._loading = False
        self._rebuild_chips()
        self._adjust_editor_height()

    def get_text(self) -> str:
        return self._editor.toPlainText()

    def sizeHint(self) -> QSize:
        width = max(120, self.width() or 200)
        chips_h = self._chips_host.sizeHint().height() if self._chips_host.isVisible() else 0
        spacing = SPACING.xs if chips_h else 0
        height = self._editor.height() + chips_h + spacing
        return QSize(width, max(height, self._min_editor_height()))

    def minimumSizeHint(self) -> QSize:
        hint = self.sizeHint()
        return QSize(80, hint.height())

    def _min_editor_height(self) -> int:
        metrics = QFontMetrics(self._editor.font())
        lines = self._MIN_LINES_MULTILINE if self._multiline else self._MIN_LINES_COMPACT
        return metrics.lineSpacing() * lines + self._PAD_Y

    def _adjust_editor_height(self) -> None:
        doc_height = int(self._editor.document().documentLayout().documentSize().height())
        target = max(self._min_editor_height(), doc_height + self._PAD_Y)
        target = min(target, self._MAX_HEIGHT)
        if self._editor.height() != target:
            self._editor.setFixedHeight(target)
        # Scroll interno só se estourou o teto
        if target >= self._MAX_HEIGHT:
            self._editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            self._editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.updateGeometry()
        self.height_changed.emit()

    def _on_text_changed(self) -> None:
        if self._loading:
            return
        text = self.get_text()
        if text.endswith("{"):
            self._show_text_popup()
        self._rebuild_chips()
        self._adjust_editor_height()
        self.text_changed.emit(text)

    def _show_text_popup(self) -> None:
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
        cursor = self._editor.textCursor()
        if self._brace_pos is not None and self._brace_pos >= 0:
            cursor.setPosition(self._brace_pos)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
        cursor.insertText(f"{{{key}}}")
        self._editor.setTextCursor(cursor)
        self._brace_pos = None
        self._rebuild_chips()
        self._adjust_editor_height()
        self.text_changed.emit(self.get_text())

    def _rebuild_chips(self) -> None:
        while self._chips_layout.count() > 1:
            item = self._chips_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        keys = extract_placeholders(self.get_text())
        self._chips_host.setVisible(bool(keys))
        for key in keys:
            chip = _PlaceholderChip(key)
            chip.remove_requested.connect(self._remove_placeholder)
            self._chips_layout.insertWidget(self._chips_layout.count() - 1, chip)
        self.updateGeometry()
        self.height_changed.emit()

    def _remove_placeholder(self, key: str) -> None:
        self.set_text(remove_placeholder(self.get_text(), key))
        self.text_changed.emit(self.get_text())
