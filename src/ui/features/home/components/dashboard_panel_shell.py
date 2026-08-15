"""Chrome compartilhado lista/grade dos painéis do dashboard Home."""
from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.ui.components.centered_layout import make_centered_column
from src.ui.features.home.components.grid_utils import (
    configure_dashboard_grid,
    grid_columns_for_width,
)
from src.ui.features.home.components.layout_utils import make_list_card_shell
from src.ui.features.home.components.section_header import TabSectionHeader
from src.ui.styles import SPACING


@dataclass
class DashboardPanelChrome:
    """Hosts de lista/grade + stack; o painel preenche com rows/cards próprios."""

    section_header: TabSectionHeader
    list_card: QFrame
    list_layout: QVBoxLayout
    grid_widget: QWidget
    grid: QGridLayout
    stack: QStackedWidget
    grid_empty_card: QFrame | None = None
    grid_empty_layout: QVBoxLayout | None = None
    grid_cols: int = 1

    def set_view(self, mode: str) -> None:
        self.stack.setCurrentIndex(0 if mode == "list" else 1)

    def clear_grid(self) -> None:
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def sync_grid_columns(self) -> bool:
        """Atualiza colunas no resize. True se mudou."""
        cols = grid_columns_for_width(self.grid_widget.width(), horizontal_margins=0)
        if cols == self.grid_cols:
            return False
        self.grid_cols = cols
        return True


def build_dashboard_panel_chrome(
    host: QWidget,
    *,
    title: str,
    subtitle: str,
    controls: QWidget,
    below_header: QWidget | None = None,
    with_grid_empty: bool = True,
    outer_bottom_margin: int | None = None,
) -> DashboardPanelChrome:
    """Monta coluna central + header + stack lista/grade no ``host``."""
    list_card, list_layout = make_list_card_shell()
    list_page = QWidget()
    list_page_layout = QVBoxLayout(list_page)
    list_page_layout.setContentsMargins(0, 0, 0, 0)
    list_page_layout.setSpacing(0)
    list_page_layout.addWidget(list_card, 0, Qt.AlignmentFlag.AlignTop)

    grid_widget = QWidget()
    grid_widget.setStyleSheet("background:transparent;")
    grid = QGridLayout(grid_widget)
    configure_dashboard_grid(grid, grid_widget)
    grid_cols = grid_columns_for_width(grid_widget.width())

    grid_empty_card: QFrame | None = None
    grid_empty_layout: QVBoxLayout | None = None
    grid_page = QWidget()
    grid_page_layout = QVBoxLayout(grid_page)
    grid_page_layout.setContentsMargins(0, 0, 0, SPACING.xl if with_grid_empty else SPACING.lg)
    grid_page_layout.setSpacing(0)
    if with_grid_empty:
        grid_empty_card, grid_empty_layout = make_list_card_shell()
        grid_empty_card.hide()
        grid_page_layout.addWidget(grid_empty_card, 0, Qt.AlignmentFlag.AlignTop)
    grid_page_layout.addWidget(grid_widget, 0, Qt.AlignmentFlag.AlignTop)
    grid_page_layout.addStretch(1)

    stack = QStackedWidget()
    stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
    stack.addWidget(list_page)
    stack.addWidget(grid_page)

    section_header = TabSectionHeader(title, subtitle, right=controls)

    centered_outer, column = make_centered_column()
    column.addWidget(section_header)
    if below_header is not None:
        column.addWidget(below_header)
    column.addWidget(stack)

    outer = QVBoxLayout(host)
    bottom = SPACING.lg if outer_bottom_margin is None else outer_bottom_margin
    outer.setContentsMargins(0, 0, 0, bottom)
    outer.addWidget(centered_outer)
    host.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

    return DashboardPanelChrome(
        section_header=section_header,
        list_card=list_card,
        list_layout=list_layout,
        grid_widget=grid_widget,
        grid=grid,
        stack=stack,
        grid_empty_card=grid_empty_card,
        grid_empty_layout=grid_empty_layout,
        grid_cols=grid_cols,
    )
