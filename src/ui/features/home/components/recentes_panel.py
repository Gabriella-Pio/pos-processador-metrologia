"""Painel de arquivos recentes — lista, grade e busca."""
from __future__ import annotations

from PyQt6.QtCore import QEvent, pyqtSignal
from PyQt6.QtWidgets import QWidget

from src.ui.components.icons import icon_empty_file, icon_empty_results
from src.ui.features.home.components.dashboard_panel_shell import build_dashboard_panel_chrome
from src.ui.features.home.components.empty_state import EmptyState
from src.ui.features.home.components.grid_utils import (
    add_grid_card,
    finalize_dashboard_grid,
)
from src.ui.features.home.components.home_cards import RecentFileCard, RecentFileRow
from src.ui.features.home.components.layout_utils import (
    add_filter_empty_state,
    clear_layout,
    set_grid_filter_empty_mode,
)
from src.ui.features.home.components.view_controls import ListViewControls
from src.ui.features.home.models.dashboard import (
    RecentFileSummary,
    RecentFilesFilterState,
    apply_recent_files_filters,
    empty_results_messages,
)
from src.ui.styles import apply_elevation


class RecentesPanel(QWidget):
    opened = pyqtSignal(str)
    import_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("HomeSurface")
        self._all_files: list[RecentFileSummary] = []
        self._filter_state = RecentFilesFilterState()
        self._density = "comfortable"

        self._controls = ListViewControls(default_view="list")
        self._controls.view_changed.connect(self._on_view_changed)
        self._controls.density_changed.connect(self._on_density_changed)

        self._chrome = build_dashboard_panel_chrome(
            self,
            title="Arquivos recentes",
            subtitle="Continue de onde parou",
            controls=self._controls,
            with_grid_empty=True,
            outer_bottom_margin=0,
        )
        self._section_header = self._chrome.section_header
        self._list_layout = self._chrome.list_layout
        self._grid = self._chrome.grid
        self._grid_widget = self._chrome.grid_widget
        self._grid_empty_card = self._chrome.grid_empty_card
        self._grid_empty_layout = self._chrome.grid_empty_layout
        self._stack = self._chrome.stack
        self._grid_widget.installEventFilter(self)

    def refresh_appearance(self) -> None:
        self._section_header.refresh_appearance()
        self._controls.refresh_appearance()
        self._refresh_views()

    def eventFilter(self, obj, event) -> bool:
        if obj is self._grid_widget and event.type() == QEvent.Type.Resize:
            if self._chrome.sync_grid_columns():
                self._rebuild_grid(self._filtered_files())
        return super().eventFilter(obj, event)

    def render(self, files: list[RecentFileSummary]) -> None:
        self._all_files = list(files)
        self._refresh_views()

    def update_filters(self, state: RecentFilesFilterState) -> None:
        self._filter_state = state
        self._refresh_views()

    def visible_count(self) -> int:
        return len(self._filtered_files())

    def total_count(self) -> int:
        return len(self._all_files)

    def has_visible_items(self) -> bool:
        return self.visible_count() > 0

    def _filtered_files(self) -> list[RecentFileSummary]:
        return apply_recent_files_filters(self._all_files, self._filter_state)

    def _refresh_views(self) -> None:
        files = self._filtered_files()
        self._update_header_subtitle()
        self._rebuild_list(files)
        self._rebuild_grid(files)

    def _update_header_subtitle(self) -> None:
        visible = len(self._filtered_files())
        total = len(self._all_files)
        if total == 0:
            self._section_header.set_subtitle("Importe um PDF para começar")
        elif visible == total:
            self._section_header.set_subtitle(f"{total} relatório(s) no histórico")
        else:
            self._section_header.set_subtitle(f"{visible} de {total} relatório(s)")

    def _empty_filter_copy(self) -> tuple[str, str]:
        return empty_results_messages(
            self._filter_state.query,
            has_active_filters=not self._filter_state.is_default(),
        )

    def _rebuild_list(self, files: list[RecentFileSummary]) -> None:
        clear_layout(self._list_layout)

        if not self._all_files:
            empty = EmptyState(
                "Nenhum relatório recente",
                "Importe um PDF para começar.",
                "Importar PDF",
                icon=icon_empty_file(),
            )
            empty.action_requested.connect(self.import_requested.emit)
            self._list_layout.addWidget(empty)
            return

        if not files:
            title, subtitle = self._empty_filter_copy()
            empty = add_filter_empty_state(
                self._list_layout,
                title,
                subtitle,
                "Novo arquivo",
                icon_empty_results(),
            )
            empty.action_requested.connect(self.import_requested.emit)
            return

        compact = self._density == "compact"
        for summary in files:
            row = RecentFileRow(summary, compact=compact)
            row.opened.connect(self.opened.emit)
            self._list_layout.addWidget(row)

    def _rebuild_grid(self, files: list[RecentFileSummary]) -> None:
        self._chrome.clear_grid()

        if not self._all_files:
            set_grid_filter_empty_mode(
                self._grid_empty_card, self._grid_widget, show_empty=False
            )
            empty = EmptyState(
                "Nenhum relatório recente",
                "Importe um PDF para começar.",
                "Importar PDF",
                icon=icon_empty_file(),
            )
            empty.action_requested.connect(self.import_requested.emit)
            self._grid.addWidget(empty, 0, 0, 1, max(1, self._chrome.grid_cols))
            return

        if not files:
            set_grid_filter_empty_mode(
                self._grid_empty_card, self._grid_widget, show_empty=True
            )
            title, subtitle = self._empty_filter_copy()
            empty = add_filter_empty_state(
                self._grid_empty_layout,
                title,
                subtitle,
                "Novo arquivo",
                icon_empty_results(),
            )
            empty.action_requested.connect(self.import_requested.emit)
            return

        set_grid_filter_empty_mode(
            self._grid_empty_card, self._grid_widget, show_empty=False
        )

        cols = max(1, self._chrome.grid_cols)
        place_cols = min(cols, len(files)) if files else cols
        for index, summary in enumerate(files):
            card = RecentFileCard(summary)
            apply_elevation(card, blur=18, y_offset=3, alpha=80)
            card.opened.connect(self.opened.emit)
            add_grid_card(self._grid, card, index, place_cols)
        finalize_dashboard_grid(self._grid, place_cols)

    def _on_view_changed(self, mode: str) -> None:
        self._chrome.set_view(mode)
        if mode == "grid" and self._chrome.sync_grid_columns():
            self._rebuild_grid(self._filtered_files())

    def _on_density_changed(self, mode: str) -> None:
        self._density = mode
        self._rebuild_list(self._filtered_files())
