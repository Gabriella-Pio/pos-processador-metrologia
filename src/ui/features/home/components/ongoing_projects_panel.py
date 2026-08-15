"""Painel de projetos em andamento — retomar edição sem exportar."""
from __future__ import annotations

from PyQt6.QtCore import QEvent, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.ui.components.centered_layout import make_centered_column
from src.ui.components.icons import icon_empty_file, icon_empty_results, icon_trash
from src.ui.features.home.components.empty_state import EmptyState
from src.ui.features.home.components.grid_utils import (
    add_grid_card,
    configure_dashboard_grid,
    finalize_dashboard_grid,
    grid_columns_for_width,
)
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
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, apply_elevation


class OngoingProjectsPanel(QWidget):
    opened = pyqtSignal(str)
    renamed = pyqtSignal(str, str)
    delete_requested = pyqtSignal(list)  # list[str] project ids
    import_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._all_projects: list[ProjectSummary] = []
        self._filter_state = RecentFilesFilterState()
        self._selected_ids: set[str] = set()

        self._controls = ListViewControls(default_view="list")
        self._controls.view_changed.connect(self._on_view_changed)
        self._controls.density_changed.connect(self._on_density_changed)
        self._density = "comfortable"

        self._selection_bar = self._build_selection_bar()

        self._list_card, self._list_layout = make_list_card_shell()
        list_page = QWidget()
        list_layout = QVBoxLayout(list_page)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.addWidget(self._list_card, 0, Qt.AlignmentFlag.AlignTop)

        self._grid_widget = QWidget()
        self._grid_widget.setStyleSheet("background:transparent;")
        self._grid = QGridLayout(self._grid_widget)
        configure_dashboard_grid(self._grid, self._grid_widget)
        self._grid_cols = grid_columns_for_width(self._grid_widget.width())
        self._grid_widget.installEventFilter(self)

        self._stack = QStackedWidget()
        self._stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._stack.addWidget(list_page)
        grid_page = QWidget()
        grid_layout = QVBoxLayout(grid_page)
        grid_layout.setContentsMargins(0, 0, 0, SPACING.lg)
        grid_layout.addWidget(self._grid_widget, 0, Qt.AlignmentFlag.AlignTop)
        grid_layout.addStretch(1)
        self._stack.addWidget(grid_page)

        self._section_header = TabSectionHeader(
            "Projetos em andamento",
            "Retome a edição sem precisar exportar",
            right=self._controls,
        )

        centered_outer, column = make_centered_column()
        column.addWidget(self._section_header)
        column.addWidget(self._selection_bar)
        column.addWidget(self._stack)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, SPACING.lg)
        outer.addWidget(centered_outer)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._sync_selection_bar()

    def _build_selection_bar(self) -> QWidget:
        p = PALETTE
        bar = QWidget()
        bar.setObjectName("ProjectSelectionBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, SPACING.sm)
        layout.setSpacing(SPACING.sm)

        self._selection_label = QLabel()
        self._selection_label.setStyleSheet(
            f"color: {p.text_secondary}; font-size: {TYPOGRAPHY.size_body}px; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(self._selection_label)

        self._select_all_btn = QPushButton("Selecionar todos")
        self._select_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._select_all_btn.clicked.connect(self._select_all_visible)
        layout.addWidget(self._select_all_btn)

        self._clear_selection_btn = QPushButton("Limpar")
        self._clear_selection_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_selection_btn.clicked.connect(self.clear_selection)
        layout.addWidget(self._clear_selection_btn)

        layout.addStretch(1)

        self._batch_delete_btn = QPushButton("Excluir selecionados")
        self._batch_delete_btn.setIcon(icon_trash())
        self._batch_delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._batch_delete_btn.clicked.connect(self._emit_batch_delete)
        layout.addWidget(self._batch_delete_btn)

        self._apply_selection_bar_styles()
        bar.hide()
        return bar

    def _apply_selection_bar_styles(self) -> None:
        p = PALETTE
        link = f"""
            QPushButton {{
                color: {p.text_secondary};
                background: transparent;
                border: 1px solid {p.border};
                border-radius: {SPACING.radius_sm}px;
                padding: 4px 10px;
                font-size: {TYPOGRAPHY.size_caption}px;
            }}
            QPushButton:hover {{
                color: {p.text_primary};
                border-color: {p.border_strong};
                background: {p.bg_surface_alt};
            }}
        """
        danger = f"""
            QPushButton {{
                color: {p.danger};
                background: rgba(248, 81, 73, 0.12);
                border: 1px solid rgba(248, 81, 73, 0.35);
                border-radius: {SPACING.radius_sm}px;
                padding: 4px 12px;
                font-size: {TYPOGRAPHY.size_caption}px;
                font-weight: {TYPOGRAPHY.weight_semibold};
            }}
            QPushButton:hover {{
                background: rgba(248, 81, 73, 0.22);
            }}
        """
        self._select_all_btn.setStyleSheet(link)
        self._clear_selection_btn.setStyleSheet(link)
        self._batch_delete_btn.setStyleSheet(danger)
        self._selection_label.setStyleSheet(
            f"color: {p.text_secondary}; font-size: {TYPOGRAPHY.size_body}px; "
            f"background: transparent; border: none;"
        )

    def refresh_appearance(self) -> None:
        self._section_header.refresh_appearance()
        self._controls.refresh_appearance()
        self._apply_selection_bar_styles()
        self._rebuild_views()

    def eventFilter(self, obj, event) -> bool:
        if obj is self._grid_widget and event.type() == QEvent.Type.Resize:
            cols = grid_columns_for_width(self._grid_widget.width(), horizontal_margins=0)
            if cols != self._grid_cols:
                self._grid_cols = cols
                self._rebuild_grid(self._filtered_projects())
        return super().eventFilter(obj, event)

    def render(self, projects: list[ProjectSummary]) -> None:
        self._all_projects = list(projects)
        valid = {p.project_id for p in projects}
        self._selected_ids &= valid
        self._rebuild_views()

    def update_filters(self, state: RecentFilesFilterState) -> None:
        self._filter_state = state
        self._rebuild_views()

    def clear_selection(self) -> None:
        self._selected_ids.clear()
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
        self._sync_selection_bar()

    def _wire_item(self, item: ProjectRow | ProjectCard) -> None:
        item.opened.connect(self.opened.emit)
        item.delete_requested.connect(self._on_single_delete)
        item.selection_changed.connect(self._on_selection_changed)
        if isinstance(item, ProjectRow):
            item.renamed.connect(self.renamed.emit)
        else:
            item.rename_requested.connect(self._on_card_rename)

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
            row = ProjectRow(
                summary,
                compact=compact,
                selected=summary.project_id in self._selected_ids,
            )
            self._wire_item(row)
            self._list_layout.addWidget(row)

    def _rebuild_grid(self, projects: list[ProjectSummary]) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not projects:
            return
        cols = max(1, self._grid_cols)
        place_cols = min(cols, len(projects)) if projects else cols
        for index, summary in enumerate(projects):
            card = ProjectCard(
                summary,
                selected=summary.project_id in self._selected_ids,
            )
            apply_elevation(card, blur=18, y_offset=3, alpha=80)
            self._wire_item(card)
            add_grid_card(self._grid, card, index, place_cols)
        finalize_dashboard_grid(self._grid, place_cols)

    def _on_view_changed(self, mode: str) -> None:
        self._stack.setCurrentIndex(0 if mode == "list" else 1)

    def _on_density_changed(self, mode: str) -> None:
        self._density = mode
        self._rebuild_list(self._filtered_projects())

    def _on_selection_changed(self, project_id: str, selected: bool) -> None:
        if selected:
            self._selected_ids.add(project_id)
        else:
            self._selected_ids.discard(project_id)
        self._sync_selection_bar()

    def _sync_selection_bar(self) -> None:
        count = len(self._selected_ids)
        self._selection_bar.setVisible(count > 0)
        if count == 1:
            self._selection_label.setText("1 projeto selecionado")
        else:
            self._selection_label.setText(f"{count} projetos selecionados")

    def _select_all_visible(self) -> None:
        for project in self._filtered_projects():
            self._selected_ids.add(project.project_id)
        self._rebuild_views()

    def _on_single_delete(self, project_id: str) -> None:
        self.delete_requested.emit([project_id])

    def _emit_batch_delete(self) -> None:
        ids = list(self._selected_ids)
        if ids:
            self.delete_requested.emit(ids)

    def _on_card_rename(self, project_id: str) -> None:
        summary = next(
            (p for p in self._all_projects if p.project_id == project_id),
            None,
        )
        if summary is None:
            return
        text, ok = QInputDialog.getText(
            self,
            "Renomear projeto",
            "Nome do projeto:",
            text=summary.display_name,
        )
        if not ok:
            return
        cleaned = text.strip()
        if cleaned and cleaned != summary.display_name:
            self.renamed.emit(project_id, cleaned)
