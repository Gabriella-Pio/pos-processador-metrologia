"""Utilitários de grade responsiva para painéis do dashboard."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGridLayout, QSizePolicy, QWidget

from src.ui.styles.tokens import SPACING, scaled_dashboard_card_size

MIN_GRID_COLUMNS = 1
MAX_GRID_COLUMNS = 5


def grid_columns_for_width(
    width: int,
    *,
    card_width: int | None = None,
    gap: int = SPACING.md,
    horizontal_margins: int = SPACING.xl * 2,
) -> int:
    """Quantas colunas cabem com a largura *mínima* do card."""
    resolved_width = card_width if card_width is not None else scaled_dashboard_card_size()[0]
    available = max(0, width - horizontal_margins)
    if available <= 0:
        return MIN_GRID_COLUMNS
    slot = resolved_width + gap
    columns = (available + gap) // slot
    return max(MIN_GRID_COLUMNS, min(columns, MAX_GRID_COLUMNS))


def configure_dashboard_grid(grid: QGridLayout, host: QWidget | None = None) -> None:
    """Grade com colunas elásticas — cards preenchem a célula."""
    grid.setSpacing(SPACING.md)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setAlignment(Qt.AlignmentFlag.AlignTop)
    if host is not None:
        host.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)


def finalize_dashboard_grid(grid: QGridLayout, columns: int) -> None:
    """Faz cada coluna ocupar fatia igual da largura."""
    cols = max(1, columns)
    for index in range(MAX_GRID_COLUMNS + 1):
        grid.setColumnStretch(index, 0)
        grid.setColumnMinimumWidth(index, 0)
    min_w, _ = scaled_dashboard_card_size()
    for index in range(cols):
        grid.setColumnStretch(index, 1)
        grid.setColumnMinimumWidth(index, min_w)


def apply_dashboard_card_size(widget: QWidget) -> None:
    """Card com largura flexível (preenche a coluna) e altura fixa."""
    min_w, height = scaled_dashboard_card_size()
    widget.setMinimumWidth(min_w)
    widget.setFixedHeight(height)
    widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


def add_grid_card(grid: QGridLayout, widget: QWidget, index: int, columns: int) -> None:
    row, col = divmod(index, max(1, columns))
    grid.addWidget(widget, row, col, Qt.AlignmentFlag.AlignTop)
