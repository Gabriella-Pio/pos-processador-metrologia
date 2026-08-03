"""Utilitários de grade responsiva para painéis do dashboard."""
from __future__ import annotations

from src.ui.styles.tokens import DASHBOARD_CARD_WIDTH, SPACING

MIN_GRID_COLUMNS = 1
MAX_GRID_COLUMNS = 6


def grid_columns_for_width(
    width: int,
    *,
    card_width: int = DASHBOARD_CARD_WIDTH,
    gap: int = SPACING.md,
    horizontal_margins: int = SPACING.xl * 2,
) -> int:
    """Calcula quantas colunas cabem na largura disponível do painel."""
    available = max(0, width - horizontal_margins)
    if available <= 0:
        return MIN_GRID_COLUMNS
    slot = card_width + gap
    columns = (available + gap) // slot
    return max(MIN_GRID_COLUMNS, min(columns, MAX_GRID_COLUMNS))
