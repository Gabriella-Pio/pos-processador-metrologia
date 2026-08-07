"""Campo de texto com placeholders `{chave}` — completer, chips e altura dinâmica."""
from __future__ import annotations

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFontMetrics, QKeyEvent, QTextCursor, QTextOption
from PyQt6.QtWidgets import (
    QCompleter,
    QFrame,
    QListWidget,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.core.domain.markdown_prose import resolve_list_enter
from src.core.domain.placeholder_utils import PLACEHOLDER_CATALOG, extract_placeholders, placeholder_label, remove_placeholder
from src.ui.components.flow_layout import FlowLayout
from src.ui.components.rich_text_toolbar import RichTextToolbar
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY


class _PlainTextEdit(QTextEdit):
    """``QTextEdit`` que sempre cola texto puro (sem HTML do Word/PDF)."""

    def __init__(self, *, continue_lists: bool = False, parent=None) -> None:
        super().__init__(parent)
        self._continue_lists = continue_lists

    def insertFromMimeData(self, source) -> None:  # noqa: N802
        if source is not None and source.hasText():
            self.textCursor().insertText(source.text())
            return
        super().insertFromMimeData(source)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if (
            self._continue_lists
            and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            and event.modifiers() == Qt.KeyboardModifier.NoModifier
        ):
            cursor = self.textCursor()
            action = resolve_list_enter(cursor.block().text())
            if action.kind == "continue":
                cursor.insertText(action.insert_text)
                event.accept()
                return
            if action.kind == "exit":
                block_start = cursor.block().position()
                cursor.setPosition(block_start)
                cursor.movePosition(
                    QTextCursor.MoveOperation.Right,
                    QTextCursor.MoveMode.KeepAnchor,
                    action.prefix_length,
                )
                cursor.removeSelectedText()
                super().keyPressEvent(event)
                return
        super().keyPressEvent(event)


class _PlaceholderChip(QPushButton):
    remove_requested = pyqtSignal(str)

    def __init__(self, key: str, parent=None) -> None:
        super().__init__(parent)
        self._key = key
        self.setText(f"{{{key}}} ✕")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(placeholder_label(key))
        self.clicked.connect(lambda: self.remove_requested.emit(self._key))
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
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
    """Editor com placeholders; chips ficam *fora* da caixa do input."""

    text_changed = pyqtSignal(str)
    height_changed = pyqtSignal()

    _MIN_LINES_COMPACT = 1
    _MIN_LINES_MULTILINE = 2
    _MAX_HEIGHT = 360
    _PAD_Y = 16

    def __init__(
        self,
        multiline: bool = True,
        *,
        supports_formatting: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._loading = False
        self._multiline = multiline
        self._supports_formatting = supports_formatting and multiline
        self._toolbar: RichTextToolbar | None = None
        self._popup: _PlaceholderPopup | None = None
        self._brace_pos: int | None = None

        completer_keys = [f"{{{key}}}" for key, _ in PLACEHOLDER_CATALOG]

        # Caixa visual só no editor — chips ficam abaixo, fora da borda
        self._editor = _PlainTextEdit(continue_lists=self._supports_formatting)
        self._editor.setObjectName("PlaceholderEditor")
        self._editor.setAcceptRichText(False)
        self._editor.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self._editor.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._editor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._editor.setTabChangesFocus(True)
        self._editor.setStyleSheet(
            f"QTextEdit#PlaceholderEditor {{"
            f" background: {PALETTE.bg_surface_alt};"
            f" color: {PALETTE.text_primary};"
            f" border: 1px solid {PALETTE.border_subtle};"
            f" border-radius: 8px;"
            f" padding: 6px 8px;"
            f" font-size: {TYPOGRAPHY.size_body}px;"
            f"}}"
            f"QTextEdit#PlaceholderEditor:focus {{"
            f" border: 1px solid {PALETTE.senai_blue_light};"
            f"}}"
        )
        self._editor.textChanged.connect(self._on_text_changed)
        self._editor.document().documentLayout().documentSizeChanged.connect(
            lambda _size: self._adjust_editor_height()
        )

        self._completer = QCompleter(completer_keys)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        self._chips_host = QWidget()
        self._chips_host.setObjectName("PlaceholderChipsHost")
        self._chips_host.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._chips_layout = FlowLayout(
            self._chips_host,
            margin=0,
            h_spacing=SPACING.xs,
            v_spacing=SPACING.xs,
        )
        self._chips_layout.setContentsMargins(2, 4, 2, 0)
        self._chips_host.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING.xs)
        if self._supports_formatting:
            self._toolbar = RichTextToolbar(self)
            self._toolbar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self._toolbar.bind_editor(self._editor)
            layout.addWidget(self._toolbar)
        layout.addWidget(self._editor)
        layout.addWidget(self._chips_host)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setStyleSheet("PlaceholderTextEdit { background: transparent; border: none; }")
        QTimer.singleShot(0, self._adjust_editor_height)

    def set_text(self, value: str, *, force: bool = False) -> None:
        """Atualiza o texto. Com foco, ignora sync externo (evita cursor voltar ao início)."""
        new_value = value or ""
        if self._editor.toPlainText() == new_value:
            return
        if not force and self._editor.hasFocus():
            return
        self._loading = True
        self._editor.setPlainText(new_value)
        self._loading = False
        self._rebuild_chips()
        self._adjust_editor_height()
        QTimer.singleShot(0, self._adjust_editor_height)

    def get_text(self) -> str:
        return self._editor.toPlainText()

    def has_editor_focus(self) -> bool:
        return self._editor.hasFocus()

    def focus_editor(self, *, select_all: bool = False) -> None:
        self._editor.setFocus(Qt.FocusReason.OtherFocusReason)
        if select_all:
            cursor = self._editor.textCursor()
            cursor.select(QTextCursor.SelectionType.Document)
            self._editor.setTextCursor(cursor)

    def sizeHint(self) -> QSize:
        width = max(80, self.width() or 120)
        chips_h = 0
        if self._chips_host.isVisible():
            chips_h = self._chips_layout.heightForWidth(width)
        chrome_h = self._chrome_height()
        spacing = SPACING.xs if chips_h else 0
        height = chrome_h + self._editor.height() + chips_h + spacing
        return QSize(width, max(height, chrome_h + self._min_editor_height()))

    def minimumSizeHint(self) -> QSize:
        hint = self.sizeHint()
        return QSize(60, hint.height())

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        QTimer.singleShot(0, self._adjust_editor_height)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._adjust_editor_height()

    def _chrome_height(self) -> int:
        if self._toolbar is None:
            return 0
        return self._toolbar.sizeHint().height() + SPACING.xs

    def _editor_content_width(self) -> int:
        viewport_width = self._editor.viewport().width()
        if viewport_width >= 40:
            return viewport_width
        frame_width = self.width()
        if frame_width >= 40:
            return max(40, frame_width - 16)
        return 200

    def _min_editor_height(self) -> int:
        metrics = QFontMetrics(self._editor.font())
        lines = self._MIN_LINES_MULTILINE if self._multiline else self._MIN_LINES_COMPACT
        return metrics.lineSpacing() * lines + self._PAD_Y

    def _adjust_editor_height(self) -> None:
        doc = self._editor.document()
        doc.setTextWidth(self._editor_content_width())
        doc_height = int(doc.size().height())
        target = max(self._min_editor_height(), doc_height + self._PAD_Y)
        target = min(target, self._MAX_HEIGHT)
        if self._editor.height() != target:
            self._editor.setFixedHeight(target)
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
        while self._chips_layout.count():
            item = self._chips_layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
        keys = extract_placeholders(self.get_text())
        self._chips_host.setVisible(bool(keys))
        for key in keys:
            chip = _PlaceholderChip(key)
            chip.remove_requested.connect(self._remove_placeholder)
            self._chips_layout.addWidget(chip)
        self.updateGeometry()
        self.height_changed.emit()

    def _remove_placeholder(self, key: str) -> None:
        self.set_text(remove_placeholder(self.get_text(), key))
        self.text_changed.emit(self.get_text())


def ceil_doc_height(editor: QTextEdit) -> float:
    return editor.document().documentLayout().documentSize().height()
