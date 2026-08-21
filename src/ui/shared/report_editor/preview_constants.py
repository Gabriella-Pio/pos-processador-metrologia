"""Constantes compartilhadas da preview rasterizada.

``PREVIEW_ZOOM`` é o zoom lógico: quantos pixels Qt cada ponto do PDF ocupa na
tela. A rasterização usa ``raster_zoom()``, que multiplica esse valor pela
densidade física do monitor — sem isso o Qt amplia uma imagem já pronta e o
texto do preview sai borrado em telas com escala acima de 100%.
"""
from __future__ import annotations

PREVIEW_ZOOM = 1.6


def raster_zoom() -> float:
    from src.ui.styles.screen_metrics import preview_device_pixel_ratio

    return PREVIEW_ZOOM * preview_device_pixel_ratio()

