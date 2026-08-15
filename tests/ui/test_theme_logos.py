"""Testes leves de tema claro vs escuro (logos e paleta)."""
from __future__ import annotations

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
