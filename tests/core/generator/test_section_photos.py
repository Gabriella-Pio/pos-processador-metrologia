"""Testes de fotos adicionais em seções sem renderer nativo."""
from __future__ import annotations

from src.core.generator.components.photo_grid import append_section_photos_if_any
from src.core.generator.styles import ReportStyles


def test_append_section_photos_if_any_renders_paths() -> None:
    story: list = []
    styles = ReportStyles.criar_estilos()
    append_section_photos_if_any(
        story,
        styles,
        "identificacao",
        {
            "fotos_secoes": {
                "identificacao": ["/tmp/foto.png"],
            },
            "foto_captions": {},
        },
    )
    assert len(story) >= 2


def test_append_section_photos_if_any_skips_empty() -> None:
    story: list = []
    styles = ReportStyles.criar_estilos()
    append_section_photos_if_any(story, styles, "identificacao", {"fotos_secoes": {}})
    assert story == []
