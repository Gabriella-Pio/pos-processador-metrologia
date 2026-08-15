"""Paletas de tema e perfis de contraste."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import fields

from src.ui.styles.tokens import PALETTE, Palette, Typography, TYPOGRAPHY

_BASE_TYPOGRAPHY = Typography()


def dark_palette() -> Palette:
    return Palette()


def is_light_palette(palette: Palette | None = None) -> bool:
    """True quando o fundo base é claro o bastante para exigir texto/logos escuros."""
    target = palette or PALETTE
    base = target.bg_base.lstrip("#")
    if len(base) != 6:
        return False
    r, g, b = int(base[0:2], 16), int(base[2:4], 16), int(base[4:6], 16)
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return luminance > 160


# Compat: imports antigos
_is_light_palette = is_light_palette


def light_palette() -> Palette:
    """Tema claro suave — evita branco puro para reduzir fadiga visual."""
    return Palette(
        bg_base="#C8D0DA",
        bg_surface="#DDE3EA",
        bg_surface_alt="#D4DAE2",
        bg_sidebar="#C0C8D2",
        bg_elevated="#E4E9EF",
        surface="#DDE3EA",
        surface_alt="#D4DAE2",
        surface_sidebar="#C0C8D2",
        surface_card="#DDE3EA",
        border="#A8B2BE",
        border_subtle="#B8C1CC",
        border_strong="#8892A0",
        # Texto um pouco mais escuro que o cinza do tema escuro invertido,
        # para não “sumir” em superfícies claras.
        text_primary="#10141C",
        text_secondary="#2A3344",
        text_muted="#3F4A5A",
        text_disabled="#6A7382",
        text_on_primary="#FFFFFF",
    )


def apply_high_contrast(palette: Palette) -> Palette:
    """Aumenta contraste de texto e bordas sobre a paleta base."""
    adjusted = deepcopy(palette)
    if is_light_palette(adjusted):
        adjusted.text_primary = "#0A0C10"
        adjusted.text_secondary = "#1A2030"
        adjusted.text_muted = "#2A3344"
        adjusted.border = "#1A2030"
        adjusted.border_strong = "#0A0C10"
        adjusted.bg_base = "#B0BAC6"
        adjusted.bg_surface = "#C8D0DA"
        adjusted.bg_surface_alt = "#BEC7D2"
    else:
        adjusted.text_primary = "#FFFFFF"
        adjusted.text_secondary = "#E6EDF3"
        adjusted.text_muted = "#C9D1D9"
        adjusted.border = "#8B949E"
        adjusted.border_strong = "#FFFFFF"
        adjusted.bg_base = "#000000"
        adjusted.bg_surface = "#0A0A0A"
    return adjusted


def copy_palette_into_global(source: Palette) -> None:
    for field in fields(Palette):
        setattr(PALETTE, field.name, getattr(source, field.name))


def apply_font_scale(scale: float) -> None:
    scale = max(0.85, min(1.4, scale))
    for field in fields(Typography):
        if not field.name.startswith("size_"):
            continue
        base = getattr(_BASE_TYPOGRAPHY, field.name)
        setattr(TYPOGRAPHY, field.name, max(10, round(base * scale)))
