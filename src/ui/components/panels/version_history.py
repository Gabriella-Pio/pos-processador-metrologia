"""Histórico de versões com timeline visual."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMenu, QScrollArea, QVBoxLayout, QWidget

from src.core.domain.ports import VersionEntry
from src.ui.components.buttons import ChromeIconButton, PrimaryButton
from src.ui.components.icons import icon_ellipsis
from src.ui.components.panels._chrome import section_header
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, configure_app_popup_menu, sidebar_panel_style
from src.ui.styles.helpers import workspace_version_entry_style


class _VersionEntryWidget(QWidget):
    """Mini-card de versão com timeline visual (border-left colorida)."""

    preview_requested = pyqtSignal(int)
    restore_requested = pyqtSignal(int)
    export_requested = pyqtSignal(int)

    def __init__(self, entry: VersionEntry, is_latest: bool = False, parent=None) -> None:
        super().__init__(parent)
        self._entry = entry
        self._is_latest = is_latest
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.sm)

        self._line = QFrame()
        self._line.setFixedWidth(3)
        self._line.setMinimumHeight(32)
        layout.addWidget(self._line, 0, Qt.AlignmentFlag.AlignTop)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)
        content_layout.setContentsMargins(0, 0, 0, 0)

        header_row = QHBoxLayout()
        self._version_label = QLabel(f"v{entry.version_number}")
        self._responsible_label = QLabel(f"  {entry.responsible_name}")
        header_row.addWidget(self._version_label)
        header_row.addWidget(self._responsible_label)
        header_row.addStretch()
        content_layout.addLayout(header_row)

        self._meta = QLabel(
            f"{entry.timestamp.strftime('%d/%m/%Y %H:%M')}  ·  {entry.description}"
        )
        self._meta.setWordWrap(True)
        content_layout.addWidget(self._meta)

        layout.addLayout(content_layout, stretch=1)

        self._actions_btn = ChromeIconButton(
            icon_ellipsis(),
            "Ações da versão",
        )
        self._actions_btn.clicked.connect(self._show_actions_menu)
        layout.addWidget(self._actions_btn, 0, Qt.AlignmentFlag.AlignTop)

        self.setToolTip(
            "Use o ícone ⋯ ou o botão direito para visualizar, restaurar ou exportar"
        )
        self.refresh_appearance()

    def _build_actions_menu(self) -> QMenu:
        menu = QMenu(self)
        configure_app_popup_menu(menu)
        preview_action = QAction("Visualizar", self)
        restore_action = QAction("Restaurar e editar", self)
        export_action = QAction("Exportar esta versão", self)
        preview_action.triggered.connect(
            lambda: self.preview_requested.emit(self._entry.version_number)
        )
        restore_action.triggered.connect(
            lambda: self.restore_requested.emit(self._entry.version_number)
        )
        export_action.triggered.connect(
            lambda: self.export_requested.emit(self._entry.version_number)
        )
        menu.addAction(preview_action)
        menu.addAction(restore_action)
        menu.addAction(export_action)
        return menu

    def _show_actions_menu(self) -> None:
        menu = self._build_actions_menu()
        pos = self._actions_btn.mapToGlobal(self._actions_btn.rect().bottomLeft())
        menu.exec(pos)

    def _show_context_menu(self, pos) -> None:
        menu = self._build_actions_menu()
        menu.exec(self.mapToGlobal(pos))

    def refresh_appearance(self) -> None:
        p = PALETTE
        accent_color = p.senai_orange if self._is_latest else p.senai_blue_light
        self._line.setStyleSheet(
            f"background-color: {accent_color}; border-radius: 2px;"
        )
        self._version_label.setStyleSheet(
            f"color: {accent_color}; font-size: {TYPOGRAPHY.size_caption}px; "
            f"font-weight: {TYPOGRAPHY.weight_bold}; background: transparent;"
        )
        self._responsible_label.setStyleSheet(
            f"color: {p.text_primary}; font-size: {TYPOGRAPHY.size_caption}px; "
            f"font-weight: {TYPOGRAPHY.weight_medium}; background: transparent;"
        )
        self._meta.setStyleSheet(
            f"color: {p.text_muted}; font-size: {TYPOGRAPHY.size_micro}px; background: transparent;"
        )
        self.setStyleSheet(workspace_version_entry_style(is_latest=self._is_latest))
        if hasattr(self, "_actions_btn"):
            self._actions_btn.refresh_appearance()


class VersionHistoryPanel(QFrame):
    """Histórico de versões com timeline visual em tempo real."""

    new_version_requested = pyqtSignal()
    preview_requested = pyqtSignal(int)
    restore_requested = pyqtSignal(int)
    export_requested = pyqtSignal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._entries: list[VersionEntry] = []

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._content = QWidget()
        self._layout = QVBoxLayout(self._content)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addStretch()
        self._scroll.setWidget(self._content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(section_header("Histórico de Versões"))
        outer.addWidget(self._scroll, stretch=1)

        self._new_version_btn = PrimaryButton("Nova versão")
        self._new_version_btn.clicked.connect(self.new_version_requested.emit)
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        btn_row.addStretch(1)
        btn_row.addWidget(self._new_version_btn)
        outer.addLayout(btn_row)

        self.refresh_appearance()

    def refresh_appearance(self) -> None:
        self.setStyleSheet(sidebar_panel_style())
        self._scroll.setStyleSheet("background: transparent;")
        self._content.setStyleSheet("background: transparent;")
        if hasattr(self, "_new_version_btn"):
            self._new_version_btn.refresh_appearance()
        for index in range(self._layout.count() - 1):
            widget = self._layout.itemAt(index).widget()
            if widget is not None and hasattr(widget, "refresh_appearance"):
                widget.refresh_appearance()

    def render_history(self, entries: list[VersionEntry]) -> None:
        self._entries = list(entries)
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for i, entry in enumerate(reversed(entries)):
            is_latest = i == 0
            widget = _VersionEntryWidget(entry, is_latest=is_latest)
            widget.preview_requested.connect(self.preview_requested.emit)
            widget.restore_requested.connect(self.restore_requested.emit)
            widget.export_requested.connect(self.export_requested.emit)
            self._layout.insertWidget(self._layout.count() - 1, widget)
