"""Painel de projetos em andamento — retomar edição sem exportar."""
from __future__ import annotations

from PyQt6.QtCore import QEvent, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QGridLayout,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.ui.components.centered_layout import make_centered_column
from src.ui.features.home.components.empty_state import EmptyState
from src.ui.features.home.components.grid_utils import grid_columns_for_width
from src.ui.features.home.components.layout_utils import (
    add_filter_empty_state,
    clear_layout,
    make_list_card_shell,
)
from src.ui.features.home.components.project_card import ProjectCard, ProjectRow
from src.ui.features.home.components.section_header import TabSectionHeader
from src.ui.features.home.components.view_controls import ListViewControls
from src.ui.features.home.models.dashboard import (
    ProjectSummary,
    RecentFilesFilterState,
    apply_projects_filters,
    empty_results_messages,
)
from src.ui.components.icons import icon_empty_file, icon_empty_results
from src.ui.styles import SPACING, apply_elevation


class OngoingProjectsPanel(QWidget):
    opened = pyqtSignal(str)
    renamed = pyqtSignal(str, str)
    import_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._all_projects: list[ProjectSummary] = []
        self._filter_state = RecentFilesFilterState()

        self._controls = ListViewControls(default_view="list")
        self._controls.view_changed.connect(self._on_view_changed)
        self._controls.density_changed.connect(self._on_density_changed)
        self._density = "comfortable"

        self._list_card, self._list_layout = make_list_card_shell()
        list_page = QWidget()
        list_layout = QVBoxLayout(list_page)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.addWidget(self._list_card, 0, Qt.AlignmentFlag.AlignTop)

        self._grid_widget = QWidget()
        self._grid_widget.setStyleSheet("background:transparent;")
        self._grid = QGridLayout(self._grid_widget)
        self._grid.setSpacing(SPACING.md)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self._grid_cols = grid_columns_for_width(self._grid_widget.width())
        self._grid_widget.installEventFilter(self)

        self._stack = QStackedWidget()
        self._stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._stack.addWidget(list_page)
        grid_page = QWidget()
        grid_layout = QVBoxLayout(grid_page)
        grid_layout.setContentsMargins(0, 0, 0, SPACING.lg)
        grid_layout.addWidget(self._grid_widget)
        self._stack.addWidget(grid_page)

        self._section_header = TabSectionHeader(
            "Projetos em andamento",
            "Retome a edição sem precisar exportar",
            right=self._controls,
        )

        centered_outer, column = make_centered_column()
        column.addWidget(self._section_header)
        column.addWidget(self._stack)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, SPACING.lg)
        outer.addWidget(centered_outer)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

    def refresh_appearance(self) -> None:
        self._controls.refresh_appearance()
        self._rebuild_views()

    def eventFilter(self, obj, event) -> bool:
        if obj is self._grid_widget and event.type() == QEvent.Type.Resize:
            cols = grid_columns_for_width(self._grid_widget.width())
            if cols != self._grid_cols:
                self._grid_cols = cols
                self._rebuild_grid(self._filtered_projects())
        return super().eventFilter(obj, event)

    def render(self, projects: list[ProjectSummary]) -> None:
        self._all_projects = list(projects)
        self._rebuild_views()

    def update_filters(self, state: RecentFilesFilterState) -> None:
        self._filter_state = state
        self._rebuild_views()

    def visible_count(self) -> int:
        return len(self._filtered_projects())

    def has_visible_items(self) -> bool:
        return self.visible_count() > 0

    def _filtered_projects(self) -> list[ProjectSummary]:
        return apply_projects_filters(self._all_projects, self._filter_state)

    def _empty_filter_copy(self) -> tuple[str, str]:
        return empty_results_messages(
            self._filter_state.query,
            has_active_filters=not self._filter_state.is_default(),
        )

    def _rebuild_views(self) -> None:
        projects = self._filtered_projects()
        total = len(self._all_projects)
        visible = len(projects)
        if total == 0:
            self._section_header.set_subtitle("Importe PDFs para criar um projeto")
        elif visible == total:
            self._section_header.set_subtitle(f"{total} projeto(s) salvo(s) localmente")
        else:
            self._section_header.set_subtitle(f"{visible} de {total} projeto(s)")
        self._rebuild_list(projects)
        self._rebuild_grid(projects)

    def _rebuild_list(self, projects: list[ProjectSummary]) -> None:
        clear_layout(self._list_layout)
        if not self._all_projects:
            empty = EmptyState(
                "Nenhum projeto em andamento",
                "Ao importar e editar PDFs, o projeto é salvo automaticamente.",
                "Importar PDF",
                icon=icon_empty_file(),
            )
            empty.action_requested.connect(self.import_requested.emit)
            self._list_layout.addWidget(empty)
            return
        if not projects:
            title, subtitle = self._empty_filter_copy()
            empty = add_filter_empty_state(
                self._list_layout,
                title,
                subtitle,
                "Importar PDF",
                icon_empty_results(),
            )
            empty.action_requested.connect(self.import_requested.emit)
            return
        compact = self._density == "compact"
        for summary in projects:
            row = ProjectRow(summary, compact=compact)
            row.opened.connect(self.opened.emit)
            row.renamed.connect(self.renamed.emit)
            self._list_layout.addWidget(row)

    def _rebuild_grid(self, projects: list[ProjectSummary]) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not projects:
            return
        cols = max(1, self._grid_cols)
        for index, summary in enumerate(projects):
            card = ProjectCard(summary)
            apply_elevation(card, blur=18, y_offset=3, alpha=80)
            card.opened.connect(self.opened.emit)
            self._grid.addWidget(card, index // cols, index % cols)

    def _on_view_changed(self, mode: str) -> None:
        self._stack.setCurrentIndex(0 if mode == "list" else 1)

    def _on_density_changed(self, mode: str) -> None:
        self._density = mode
        self._rebuild_list(self._filtered_projects())
