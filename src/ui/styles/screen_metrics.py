"""Métricas da tela — mantém a UI utilizável sob qualquer escala do Windows.

A escala de exibição do Windows (100%, 125%, 150%, 175%…) reduz o espaço lógico
que o Qt entrega à aplicação: um monitor 1920x1080 a 150% vira 1280x720. Tamanhos
fixos calculados para telas grandes passam a estourar a área disponível.
"""
from __future__ import annotations

from PyQt6.QtGui import QGuiApplication, QScreen
from PyQt6.QtWidgets import QWidget

#: Folga reservada para bordas de janela, barra de tarefas e sombra dos diálogos.
SCREEN_MARGIN = 48

_MIN_DPR = 1.0
_MAX_DPR = 3.0


def _screen_for(reference: QWidget | None = None) -> QScreen | None:
    if reference is not None:
        handle = reference.window().windowHandle()
        if handle is not None and handle.screen() is not None:
            return handle.screen()
        return reference.screen()
    return QGuiApplication.primaryScreen()


def available_size(reference: QWidget | None = None) -> tuple[int, int]:
    """Área lógica utilizável (já descontada a barra de tarefas), em pixels Qt."""
    screen = _screen_for(reference)
    if screen is None:
        return (1280, 720)
    geometry = screen.availableGeometry()
    return (geometry.width(), geometry.height())


def fit_to_screen(
    width: int,
    height: int,
    *,
    reference: QWidget | None = None,
    margin: int = SCREEN_MARGIN,
) -> tuple[int, int]:
    """Reduz ``width``/``height`` ao que cabe na tela, preservando o pedido original."""
    max_w, max_h = available_size(reference)
    return (min(width, max(240, max_w - margin)), min(height, max(240, max_h - margin)))


def fit_dialog(
    dialog: QWidget,
    width: int,
    height: int,
    *,
    margin: int = SCREEN_MARGIN,
) -> tuple[int, int]:
    """Define mínimo e tamanho inicial de um diálogo sem ultrapassar a tela."""
    parent = dialog.parentWidget()
    fitted_w, fitted_h = fit_to_screen(width, height, reference=parent or dialog, margin=margin)
    dialog.setMinimumSize(fitted_w, fitted_h)
    dialog.resize(fitted_w, fitted_h)
    return (fitted_w, fitted_h)


def preview_device_pixel_ratio(reference: QWidget | None = None) -> float:
    """Fator de pixels físicos por pixel lógico, arredondado para passos de 0,25.

    Rasterizar o PDF nesse fator evita que o Qt amplie uma imagem já pronta,
    que é o que deixa o texto do preview borrado em telas com escala > 100%.
    """
    screen = _screen_for(reference)
    ratio = screen.devicePixelRatio() if screen is not None else 1.0
    stepped = round(ratio * 4) / 4
    return min(_MAX_DPR, max(_MIN_DPR, stepped))
