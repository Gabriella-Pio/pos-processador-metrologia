"""Utilitários de layout dos painéis da Home."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFrame, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from src.ui.components.home.empty_state import EmptyState
from src.ui.styles import SPACING


def clear_layout(layout) -> None:
    """Remove widgets de um layout e agenda destruição — evita sobreposição fantasma."""
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()
            continue
        child_layout = item.layout()
        if child_layout is not None:
            clear_layout(child_layout)


def make_scroll(inner: QVBoxLayout) -> QScrollArea:
    wrapper = QWidget()
    wrapper.setObjectName("HomeScrollContent")
    wrapper.setLayout(inner)
    scroll = QScrollArea()
    scroll.setObjectName("HomePanelScroll")
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setWidget(wrapper)
    scroll.setMinimumHeight(0)
    scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    return scroll


def make_list_card_shell() -> tuple[QFrame, QVBoxLayout]:
    """Container HomeListCard full-width — usado na lista e no empty state da grade."""
    card = QFrame()
    card.setObjectName("HomeListCard")
    card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
    card_layout.setSpacing(0)
    card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    return card, card_layout


def set_grid_filter_empty_mode(
    empty_card: QFrame,
    grid_widget: QWidget,
    *,
    show_empty: bool,
) -> None:
    """Alterna grade vs. card de empty state sem reservar altura da grade."""
    if show_empty:
        grid_widget.hide()
        grid_widget.setMaximumHeight(0)
        empty_card.show()
    else:
        empty_card.hide()
        grid_widget.setMaximumHeight(16777215)
        grid_widget.show()


def add_filter_empty_state(
    layout: QVBoxLayout,
    title: str,
    subtitle: str,
    cta: str,
    icon: QIcon,
) -> EmptyState:
    """Preenche um layout (dentro de HomeListCard) com empty state padronizado."""
    clear_layout(layout)
    empty = EmptyState(title, subtitle, cta, icon=icon)
    layout.addWidget(empty, 0, Qt.AlignmentFlag.AlignTop)
    return empty
