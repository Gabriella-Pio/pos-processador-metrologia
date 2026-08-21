"""Evita janelas nativas fantasmas no Windows ao desmontar widgets."""
from __future__ import annotations

from PyQt6.QtWidgets import QLayout, QWidget


def discard_widget(widget: QWidget | None) -> None:
    """Esconde e destrói o widget sem ``setParent(None)``.

    No Windows, um ``QWidget`` visível (ou recém-removido do layout) sem pai
    vira janela de primeiro nível — só a barra minimizar/maximizar/fechar.
    """
    if widget is None:
        return
    widget.hide()
    widget.deleteLater()


def clear_layout(layout: QLayout | None, *, discard: bool = True) -> None:
    """Esvazia um layout. Com ``discard=False``, só esconde (widget reutilizado)."""
    if layout is None:
        return
    while layout.count():
        item = layout.takeAt(0)
        child = item.widget() if item is not None else None
        if child is None:
            continue
        child.hide()
        if discard:
            child.deleteLater()
