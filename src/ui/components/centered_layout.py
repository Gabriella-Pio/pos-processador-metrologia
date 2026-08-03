"""Coluna centralizada reutilizável — alinha hero e painéis da Home."""
from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QSizePolicy, QVBoxLayout, QWidget

from src.ui.styles import SPACING

HOME_CONTENT_MAX_WIDTH = 1100


def make_centered_column(
    max_width: int = HOME_CONTENT_MAX_WIDTH,
    *,
    background: str | None = None,
) -> tuple[QWidget, QVBoxLayout]:
    """Retorna (wrapper externo, layout da coluna interna com max-width)."""
    outer = QWidget()
    outer.setObjectName("HomeCenteredColumn")
    outer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
    if background is not None:
        outer.setStyleSheet(f"background: {background};")

    row = QHBoxLayout(outer)
    row.setContentsMargins(SPACING.xl, 0, SPACING.xl, 0)
    row.setSpacing(0)

    column = QWidget()
    column.setMaximumWidth(max_width)
    column.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

    column_layout = QVBoxLayout(column)
    column_layout.setContentsMargins(0, 0, 0, 0)
    column_layout.setSpacing(SPACING.md)

    row.addStretch(1)
    row.addWidget(column, stretch=100)
    row.addStretch(1)
    return outer, column_layout
