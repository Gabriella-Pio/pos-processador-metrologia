"""Testes de grade de fotos e fotos adicionais em seções."""
from __future__ import annotations

from reportlab.platypus import Table

from src.core.generator.components.photo_grid import (
    append_photo_grid,
    append_section_photos_if_any,
)
from src.core.generator.styles import ReportStyles


def _centered_photo_tables(story: list) -> list[Table]:
    """Tabelas de 1 coluna (largura total) usadas para centralizar foto isolada/sobra."""
    out: list[Table] = []
    for item in story:
        if not isinstance(item, Table):
            continue
        widths = list(item._colWidths)  # noqa: SLF001
        if len(widths) != 1:
            continue
        if abs(float(widths[0]) - 540.0) > 0.1:
            continue
        out.append(item)
    return out


def _assert_cell_centered(table: Table) -> None:
    cell_style = table._cellStyles[0][0]  # noqa: SLF001
    assert cell_style.alignment == "CENTER"


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
    assert _centered_photo_tables(story), "foto única deve ir em tabela centralizada"


def test_append_section_photos_if_any_skips_empty() -> None:
    story: list = []
    styles = ReportStyles.criar_estilos()
    append_section_photos_if_any(story, styles, "identificacao", {"fotos_secoes": {}})
    assert story == []


def test_append_photo_grid_centers_single_photo() -> None:
    story: list = []
    styles = ReportStyles.criar_estilos()
    append_photo_grid(
        story,
        ["/tmp/unica.png"],
        {"/tmp/unica.png": "legenda da foto"},
        styles,
    )
    centered = _centered_photo_tables(story)
    assert len(centered) == 1
    _assert_cell_centered(centered[0])
    cell = centered[0]._cellvalues[0][0]  # noqa: SLF001
    assert isinstance(cell, list)
    assert len(cell) >= 1


def test_append_photo_grid_centers_odd_leftover() -> None:
    story: list = []
    styles = ReportStyles.criar_estilos()
    append_photo_grid(
        story,
        ["/tmp/a.png", "/tmp/b.png", "/tmp/c.png"],
        None,
        styles,
    )
    pair_tables = [
        item
        for item in story
        if isinstance(item, Table) and len(item._colWidths) == 2  # noqa: SLF001
    ]
    centered = _centered_photo_tables(story)
    assert len(pair_tables) == 1
    assert len(centered) == 1
    _assert_cell_centered(centered[0])
