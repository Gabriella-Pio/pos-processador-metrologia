"""Design tokens — paleta, tipografia e espaçamento."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Palette:
    senai_orange: str = "#f0431e"
    senai_orange_hover: str = "#d63818"
    senai_orange_dark: str = "#9e2c12"
    senai_orange_glow: str = "rgba(240, 67, 30, 45)"

    senai_blue: str = "#254aa5"
    senai_blue_hover: str = "#1e3d8a"
    senai_blue_light: str = "#4a6fd4"
    senai_blue_glow: str = "rgba(37, 74, 165, 50)"

    senai_red: str = "#f0431e"
    senai_red_hover: str = "#d63818"
    senai_red_dark: str = "#9e2c12"
    zeiss_blue: str = "#4a6fd4"
    zeiss_blue_hover: str = "#3a5cb8"
    zeiss_blue_dark: str = "#254aa5"

    bg_base: str = "#0D1117"
    bg_surface: str = "#161B22"
    bg_surface_alt: str = "#1C2230"
    bg_sidebar: str = "#13191F"
    bg_elevated: str = "#21262D"

    surface: str = "#161B22"
    surface_alt: str = "#1C2230"
    surface_sidebar: str = "#13191F"
    surface_card: str = "#161B22"

    border: str = "#30363D"
    border_subtle: str = "#21262D"
    border_strong: str = "#484F58"

    text_primary: str = "#E6EDF3"
    text_secondary: str = "#8B949E"
    text_muted: str = "#6E7681"
    text_disabled: str = "#484F58"
    text_on_primary: str = "#FFFFFF"

    success: str = "#3FB950"
    success_bg: str = "rgba(63, 185, 80, 30)"
    warning: str = "#D29922"
    warning_bg: str = "rgba(210, 153, 34, 30)"
    danger: str = "#F85149"
    danger_bg: str = "rgba(248, 81, 73, 30)"
    info: str = "#4a6fd4"
    info_bg: str = "rgba(74, 111, 212, 30)"


@dataclass
class Typography:
    font_family: str = "Inter, Segoe UI, -apple-system, Roboto, sans-serif"
    size_h1: int = 24
    size_h2: int = 18
    size_h3: int = 15
    size_body: int = 13
    size_caption: int = 11
    weight_regular: int = 400
    weight_medium: int = 500
    weight_semibold: int = 600
    weight_bold: int = 700


@dataclass
class Spacing:
    xs: int = 4
    sm: int = 8
    md: int = 16
    lg: int = 24
    xl: int = 32
    radius_sm: int = 6
    radius_md: int = 10
    radius_lg: int = 16
    radius_pill: int = 999
    header_height: int = 70


PALETTE = Palette()
TYPOGRAPHY = Typography()
SPACING = Spacing()

# Largura padrão dos cards do dashboard (usada no cálculo de colunas responsivas)
DASHBOARD_CARD_WIDTH = 168
