"""Barra de formatação markdown para campos de prosa."""
from __future__ import annotations

import re

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QKeySequence, QShortcut, QTextCursor
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QTextEdit

from src.core.domain.markdown_prose import strip_markdown_formatting
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY

_NUMBERED_PREFIX = re.compile(r"^\d+\. ")


class RichTextToolbar(QFrame):
    """Insere marcadores markdown no ``QTextEdit`` alvo."""

    format_requested = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("RichTextToolbar")
        self._editor: QTextEdit | None = None
        self._shortcuts: list[QShortcut] = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, SPACING.xs)
        layout.setSpacing(SPACING.xs)

        self._bold_btn = self._make_button("B", "Negrito (**texto**) — Ctrl+B")
        self._italic_btn = self._make_button("I", "Itálico (*texto*) — Ctrl+I")
        self._bullet_btn = self._make_button("•", "Lista com marcador (- item)")
        self._numbered_btn = self._make_button("1.", "Lista numerada (1. item)")
        self._clear_btn = self._make_button("Tx", "Limpar formatação da seleção")
        self._bold_btn.clicked.connect(lambda: self.apply_format("bold"))
        self._italic_btn.clicked.connect(lambda: self.apply_format("italic"))
        self._bullet_btn.clicked.connect(lambda: self.apply_format("bullet"))
        self._numbered_btn.clicked.connect(lambda: self.apply_format("numbered"))
        self._clear_btn.clicked.connect(self.clear_formatting)
        for button in (
            self._bold_btn,
            self._italic_btn,
            self._bullet_btn,
            self._numbered_btn,
            self._clear_btn,
        ):
            layout.addWidget(button)
        layout.addStretch(1)

        self.setStyleSheet(
            f"QFrame#RichTextToolbar {{ background: transparent; border: none; }}"
            f"QPushButton {{ background: {PALETTE.bg_surface_alt}; color: {PALETTE.text_primary}; "
            f"border: 1px solid {PALETTE.border_subtle}; border-radius: 6px; "
            f"min-width: 28px; min-height: 28px; padding: 2px 8px; "
            f"font-size: {TYPOGRAPHY.size_body}px; font-weight: 600; }}"
            f"QPushButton:hover {{ border-color: {PALETTE.senai_blue_light}; "
            f"color: {PALETTE.senai_blue_light}; }}"
        )

    def bind_editor(self, editor: QTextEdit) -> None:
        self._editor = editor
        for shortcut in self._shortcuts:
            shortcut.deleteLater()
        self._shortcuts = [
            self._bind_shortcut(editor, QKeySequence.StandardKey.Bold, "bold"),
            self._bind_shortcut(editor, QKeySequence.StandardKey.Italic, "italic"),
        ]

    def _bind_shortcut(self, editor: QTextEdit, sequence: QKeySequence, kind: str) -> QShortcut:
        shortcut = QShortcut(sequence, editor)
        shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        shortcut.activated.connect(lambda k=kind: self.apply_format(k))
        return shortcut

    def _make_button(self, label: str, tooltip: str) -> QPushButton:
        button = QPushButton(label)
        button.setToolTip(tooltip)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        return button

    def apply_format(self, kind: str) -> None:
        if self._editor is None:
            return
        editor = self._editor
        if kind == "bullet":
            self._toggle_line_prefix(editor, bullet=True)
        elif kind == "numbered":
            self._toggle_line_prefix(editor, bullet=False)
        else:
            wrapper = ("**", "**") if kind == "bold" else ("*", "*")
            self._wrap_selection(editor, *wrapper)
        self.format_requested.emit(kind)
        editor.setFocus()

    def clear_formatting(self) -> None:
        if self._editor is None:
            return
        editor = self._editor
        cursor = editor.textCursor()
        if cursor.hasSelection():
            selected = cursor.selectedText().replace("\u2029", "\n")
            cursor.insertText(strip_markdown_formatting(selected))
        else:
            cursor.select(QTextCursor.SelectionType.Document)
            cursor.insertText(strip_markdown_formatting(editor.toPlainText()))
        self.format_requested.emit("clear")
        editor.setFocus()

    @staticmethod
    def _wrap_selection(editor: QTextEdit, prefix: str, suffix: str) -> None:
        cursor = editor.textCursor()
        if cursor.hasSelection():
            selected = cursor.selectedText().replace("\u2029", "\n")
            cursor.insertText(f"{prefix}{selected}{suffix}")
            return
        cursor.insertText(f"{prefix}{suffix}")
        cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.MoveAnchor, len(suffix))
        editor.setTextCursor(cursor)

    @staticmethod
    def _toggle_line_prefix(editor: QTextEdit, *, bullet: bool) -> None:
        cursor = editor.textCursor()
        block = cursor.block()
        line_start = block.position()
        line_text = block.text()

        if bullet:
            if line_text.startswith("- "):
                cursor.setPosition(line_start)
                cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 2)
                cursor.removeSelectedText()
            else:
                numbered = _NUMBERED_PREFIX.match(line_text)
                if numbered:
                    cursor.setPosition(line_start)
                    cursor.movePosition(
                        QTextCursor.MoveOperation.Right,
                        QTextCursor.MoveMode.KeepAnchor,
                        len(numbered.group(0)),
                    )
                    cursor.removeSelectedText()
                if line_text.strip():
                    cursor.insertText("\n")
                cursor.insertText("- ")
        else:
            numbered = _NUMBERED_PREFIX.match(line_text)
            if numbered:
                cursor.setPosition(line_start)
                cursor.movePosition(
                    QTextCursor.MoveOperation.Right,
                    QTextCursor.MoveMode.KeepAnchor,
                    len(numbered.group(0)),
                )
                cursor.removeSelectedText()
            else:
                if line_text.startswith("- "):
                    cursor.setPosition(line_start)
                    cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 2)
                    cursor.removeSelectedText()
                elif line_text.strip():
                    cursor.insertText("\n")
                next_number = RichTextToolbar._next_number_for_block(editor, block)
                cursor.insertText(f"{next_number}. ")

        editor.setTextCursor(cursor)

    @staticmethod
    def _next_number_for_block(editor: QTextEdit, block) -> int:
        previous = block.previous()
        while previous.isValid():
            match = _NUMBERED_PREFIX.match(previous.text())
            if match:
                return int(match.group(0).split(".", 1)[0]) + 1
            if previous.text().strip():
                break
            previous = previous.previous()
        return 1
