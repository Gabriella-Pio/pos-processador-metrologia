"""Ícones corporativos via QtAwesome (Font Awesome 5 Solid)."""
from __future__ import annotations

import qtawesome as qta
from PyQt6.QtGui import QIcon

from src.ui.styles import PALETTE


def app_icon(name: str, *, color: str | None = None, scale: float = 1.0) -> QIcon:
    """Retorna ícone FA5 solid com cor do design system."""
    return qta.icon(
        f"fa5s.{name}",
        color=color or PALETTE.text_muted,
        scale_factor=scale,
    )


def icon_file_pdf() -> QIcon:
    return app_icon("file-pdf", color=PALETTE.senai_orange)


def icon_layers() -> QIcon:
    return app_icon("layer-group", color=PALETTE.senai_blue_light)


def icon_file_upload() -> QIcon:
    return app_icon("file-upload", color=PALETTE.senai_orange)


def icon_export() -> QIcon:
    return app_icon("file-export", color=PALETTE.text_on_primary, scale=0.9)


def icon_filter() -> QIcon:
    return app_icon("sliders-h", color=PALETTE.text_muted)


def icon_search() -> QIcon:
    return app_icon("search", color=PALETTE.text_muted)


def icon_plus() -> QIcon:
    return app_icon("plus", color=PALETTE.senai_orange)


def icon_cog() -> QIcon:
    return app_icon("cog", color=PALETTE.senai_blue_light)


def icon_help() -> QIcon:
    return app_icon("question-circle", color=PALETTE.text_on_primary)


def icon_universal_access() -> QIcon:
    return app_icon("universal-access", color=PALETTE.text_on_primary)


def icon_list() -> QIcon:
    return app_icon("list", color=PALETTE.text_muted)


def icon_grid() -> QIcon:
    return app_icon("th-large", color=PALETTE.text_muted)


def icon_density_comfortable() -> QIcon:
    return app_icon("align-justify", color=PALETTE.text_muted)


def icon_density_compact() -> QIcon:
    return app_icon("grip-lines", color=PALETTE.text_muted)


def icon_chevron_left() -> QIcon:
    return app_icon("chevron-left", color=PALETTE.text_on_primary)


def icon_chevron_right() -> QIcon:
    return app_icon("chevron-right", color=PALETTE.text_on_primary)


def icon_empty_search() -> QIcon:
    return app_icon("search", color=PALETTE.text_muted)


def icon_empty_results() -> QIcon:
    """Ícone para estado vazio de busca — escala neutra para evitar clipping."""
    return app_icon("search", color=PALETTE.text_muted, scale=1.0)


def icon_empty_file() -> QIcon:
    return app_icon("file-alt", color=PALETTE.text_muted, scale=1.0)


def icon_image() -> QIcon:
    return app_icon("image", color=PALETTE.text_muted, scale=0.9)


def icon_chart() -> QIcon:
    return app_icon("chart-bar", color=PALETTE.text_muted, scale=0.9)


def icon_table() -> QIcon:
    return app_icon("table", color=PALETTE.text_muted, scale=0.9)


def icon_edit() -> QIcon:
    return app_icon("pen", color=PALETTE.senai_blue_light, scale=0.85)


def icon_chevron_down() -> QIcon:
    return app_icon("chevron-down", color=PALETTE.text_muted, scale=0.85)


def icon_trash() -> QIcon:
    return app_icon("trash-alt", color=PALETTE.danger, scale=0.85)


def icon_grip() -> QIcon:
    return app_icon("grip-vertical", color=PALETTE.text_muted, scale=0.8)


def icon_close() -> QIcon:
    return app_icon("times", color=PALETTE.text_muted, scale=0.9)


def icon_ellipsis() -> QIcon:
    return app_icon("ellipsis-h", color=PALETTE.text_muted, scale=0.9)


def icon_chevron_up() -> QIcon:
    return app_icon("chevron-up", color=PALETTE.text_muted, scale=0.85)
