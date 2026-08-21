"""Testes leves de tema claro vs escuro (logos e paleta)."""
from __future__ import annotations

from dataclasses import fields

from src.ui.accessibility.themes import (
    copy_palette_into_global,
    dark_palette,
    is_light_palette,
    light_palette,
)
from src.ui.components.header import (
    _leading_logo_candidates,
    _trailing_logo_candidates,
)
from src.ui.styles.qss_loader import render_qss
from src.ui.styles.tokens import PALETTE


def test_light_palette_is_detected() -> None:
    copy_palette_into_global(light_palette())
    assert is_light_palette() is True
    copy_palette_into_global(dark_palette())
    assert is_light_palette() is False


def test_logo_candidates_prefer_non_white_in_light_theme() -> None:
    copy_palette_into_global(light_palette())
    leading = _leading_logo_candidates()
    trailing = _trailing_logo_candidates(("logo-senai-white.png",))
    assert "white" not in leading[0]
    assert trailing[0] == "logo-senai.png"

    copy_palette_into_global(dark_palette())
    leading = _leading_logo_candidates()
    trailing = _trailing_logo_candidates(("logo-senai-white.png",))
    assert "white" in leading[0]
    assert trailing[0] == "logo-senai-white.png"


def _luminance(hex_color: str) -> float:
    raw = hex_color.lstrip("#")
    red, green, blue = int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)
    return 0.299 * red + 0.587 * green + 0.114 * blue


def test_tooltip_stays_light_text_on_dark_in_light_theme() -> None:
    snapshot = {field.name: getattr(PALETTE, field.name) for field in fields(PALETTE)}
    try:
        copy_palette_into_global(light_palette())
        assert _luminance(PALETTE.tooltip_text) > 160
        assert _luminance(PALETTE.tooltip_bg) < 80
        qss = render_qss("QToolTip {{ color: {tooltip_text}; background-color: {tooltip_bg}; }}")
        assert PALETTE.tooltip_text in qss
        assert PALETTE.tooltip_bg in qss
        assert PALETTE.text_primary not in qss
    finally:
        for name, value in snapshot.items():
            setattr(PALETTE, name, value)
