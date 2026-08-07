"""Aba Arquivos — projetos em andamento + exportações."""
from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from src.ui.features.home.components.exports_panel import ExportsPanel
from src.ui.features.home.components.ongoing_projects_panel import OngoingProjectsPanel
from src.ui.features.home.models.dashboard import RecentFilesFilterState
from src.ui.styles import SPACING


class ArquivosPanel(QWidget):
    project_opened = pyqtSignal(str)
    export_opened = pyqtSignal(str)
    import_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("HomeSurface")

        self._ongoing = OngoingProjectsPanel()
        self._ongoing.opened.connect(self.project_opened.emit)
        self._ongoing.import_requested.connect(self.import_requested.emit)

        self._exports = ExportsPanel()
        self._exports.opened.connect(self.export_opened.emit)
        self._exports.import_requested.connect(self.import_requested.emit)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(SPACING.xl)
        outer.addWidget(self._ongoing)
        outer.addWidget(self._exports)
        self.setSizePolicy(
            self._ongoing.sizePolicy().horizontalPolicy(),
            self._ongoing.sizePolicy().verticalPolicy(),
        )

    def refresh_appearance(self) -> None:
        self._ongoing.refresh_appearance()
        self._exports.refresh_appearance()

    def render_projects(self, projects) -> None:
        self._ongoing.render(projects)

    def render_exports(self, files) -> None:
        self._exports.render(files)

    def update_filters(self, state: RecentFilesFilterState) -> None:
        self._ongoing.apply_search(state.query)
        self._exports.update_filters(state)

    def visible_count(self) -> int:
        return self._ongoing.visible_count() + self._exports.visible_count()

    def has_visible_items(self) -> bool:
        return self._ongoing.has_visible_items() or self._exports.has_visible_items()

    def ongoing_visible_count(self) -> int:
        return self._ongoing.visible_count()

    def exports_visible_count(self) -> int:
        return self._exports.visible_count()

    def total_export_count(self) -> int:
        return self._exports.total_count()
