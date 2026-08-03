"""Controles de visualização da Home — lista/grade e densidade."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QWidget

from src.ui.components.icons import (
    icon_density_comfortable,
    icon_density_compact,
    icon_grid,
    icon_list,
)
from src.ui.styles import PALETTE, view_toggle_style


class ListViewControls(QWidget):
    """Lista / grade + densidade confortável / compacta (dois grupos de dois botões)."""

    view_changed = pyqtSignal(str)
    density_changed = pyqtSignal(str)

    def __init__(
        self,
        default_view: str = "list",
        default_density: str = "comfortable",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._view = default_view
        self._density = default_density

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._list_btn = self._make_icon_button(icon_list(), "list", "Lista")
        self._grid_btn = self._make_icon_button(icon_grid(), "grid", "Grade")
        layout.addWidget(self._list_btn)
        layout.addWidget(self._grid_btn)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setFixedWidth(1)
        divider.setFixedHeight(18)
        divider.setStyleSheet(
            f"background: {PALETTE.border_subtle}; border: none; max-width: 1px;"
        )
        layout.addWidget(divider)

        self._comfortable_btn = self._make_icon_button(
            icon_density_comfortable(), "comfortable", "Linhas confortáveis"
        )
        self._compact_btn = self._make_icon_button(
            icon_density_compact(), "compact", "Linhas compactas"
        )
        layout.addWidget(self._comfortable_btn)
        layout.addWidget(self._compact_btn)

        self._refresh()

    def _make_icon_button(self, icon: QIcon, mode: str, tooltip: str) -> QPushButton:
        button = QPushButton()
        button.setIcon(icon)
        button.setFixedSize(28, 28)
        button.setToolTip(tooltip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        if mode in ("list", "grid"):
            button.clicked.connect(lambda: self._switch_view(mode))
        else:
            button.clicked.connect(lambda: self._switch_density(mode))
        return button

    def _switch_view(self, mode: str) -> None:
        if mode == self._view:
            return
        self._view = mode
        self._refresh()
        self.view_changed.emit(mode)

    def _switch_density(self, mode: str) -> None:
        if mode == self._density:
            return
        self._density = mode
        self._refresh()
        self.density_changed.emit(mode)

    def _refresh(self) -> None:
        self._list_btn.setStyleSheet(view_toggle_style(active=self._view == "list"))
        self._grid_btn.setStyleSheet(view_toggle_style(active=self._view == "grid"))
        self._comfortable_btn.setStyleSheet(
            view_toggle_style(active=self._density == "comfortable")
        )
        self._compact_btn.setStyleSheet(view_toggle_style(active=self._density == "compact"))

    def refresh_appearance(self) -> None:
        self._refresh()


class ViewToggle(QWidget):
    """Botões lista / grade com ícones QtAwesome."""

    view_changed = pyqtSignal(str)

    def __init__(self, default: str = "list", parent=None) -> None:
        super().__init__(parent)
        self._current = default
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        self._list_btn = self._make_button(icon_list(), "list")
        self._grid_btn = self._make_button(icon_grid(), "grid")
        layout.addWidget(self._list_btn)
        layout.addWidget(self._grid_btn)
        self._refresh()

    def _make_button(self, icon: QIcon, mode: str) -> QPushButton:
        button = QPushButton()
        button.setIcon(icon)
        button.setFixedSize(28, 28)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda: self._switch(mode))
        return button

    def _switch(self, mode: str) -> None:
        if mode == self._current:
            return
        self._current = mode
        self._refresh()
        self.view_changed.emit(mode)

    def _refresh(self) -> None:
        self._list_btn.setStyleSheet(view_toggle_style(active=self._current == "list"))
        self._grid_btn.setStyleSheet(view_toggle_style(active=self._current == "grid"))

    def refresh_appearance(self) -> None:
        self._refresh()
