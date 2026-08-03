"""
TabBar — barra de navegação por abas da Home.

Usa QTabBar nativo com estilo alinhado ao painel de Ajuda (underline laranja).
Emite ``tab_changed(int)`` ao trocar de aba.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QTabBar, QVBoxLayout, QWidget

from src.ui.components.centered_layout import make_centered_column


class TabBar(QWidget):
    """Barra de abas da Home — left-aligned dentro da coluna central."""

    tab_changed = pyqtSignal(int)

    def __init__(self, tab_labels: list[str], parent=None) -> None:
        super().__init__(parent)
        self._labels = list(tab_labels)
        self._counts = [0] * len(tab_labels)

        self._tab_bar = QTabBar()
        self._tab_bar.setObjectName("HomeTabBar")
        self._tab_bar.setDocumentMode(True)
        self._tab_bar.setExpanding(False)
        self._tab_bar.setDrawBase(False)
        for label in tab_labels:
            self._tab_bar.addTab(label)
        self._tab_bar.currentChanged.connect(self._on_tab_changed)

        shell = QWidget()
        shell.setObjectName("HomeTabBarShell")
        self._shell = shell
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        shell_layout.addWidget(self._tab_bar)

        centered_outer, column = make_centered_column()
        column.addWidget(shell)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(centered_outer)

        self.setFixedHeight(44)

    def _on_tab_changed(self, index: int) -> None:
        if index >= 0:
            self.tab_changed.emit(index)

    def set_active(self, index: int) -> None:
        """Troca a aba ativa programaticamente."""
        if 0 <= index < self._tab_bar.count():
            self._tab_bar.setCurrentIndex(index)

    def update_count(self, index: int, count: int) -> None:
        """Exibe contagem no label da aba — ex: 'Arquivos (3)'."""
        if 0 <= index < len(self._labels):
            self._counts[index] = count
            label = (
                f"{self._labels[index]} ({count})"
                if count > 0
                else self._labels[index]
            )
            self._tab_bar.setTabText(index, label)

    def refresh_appearance(self) -> None:
        """Estilos vêm do QSS global (#HomeTabBar)."""

    def set_stuck(self, stuck: bool) -> None:
        """Indica se a barra está fixa abaixo do header durante scroll."""
        self._shell.setProperty("stuck", stuck)
        self._shell.style().unpolish(self._shell)
        self._shell.style().polish(self._shell)

    @property
    def tab_widget(self) -> QTabBar:
        return self._tab_bar
