"""
Design System central da aplicação.

Centraliza paleta de cores (institucional SENAI/ZEISS), tipografia,
espaçamentos e geração de folhas de estilo (QSS) para os componentes.
Nenhuma view ou componente deve declarar cores/fontes "soltas" em código —
tudo referencia esta camada, o que garante consistência visual e permite
trocar o tema em um único ponto (Open/Closed Principle).
"""
from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QWidget


@dataclass(frozen=True)
class Palette:
    """Paleta de cores institucional.

    Vermelho SENAI como cor de destaque/ação primária, azul ZEISS como
    cor de apoio/identidade técnica, e uma escala neutra estilo
    Google Workspace para fundos, bordas e texto.
    """

    # Cores institucionais
    senai_red: str = "#EE1B24"
    senai_red_hover: str = "#C4141C"
    senai_red_dark: str = "#8C0F16"  # usado no gradiente do header institucional
    zeiss_blue: str = "#0069B4"
    zeiss_blue_hover: str = "#00568F"
    zeiss_blue_dark: str = "#003C63"

    # Neutros (estilo "Google Docs/Drive")
    surface: str = "#FFFFFF"
    surface_alt: str = "#F5F6F8"
    surface_sidebar: str = "#EEF1F4"
    surface_header_text: str = "#FFFFFF"
    border: str = "#E2E5EA"
    border_strong: str = "#C7CBD1"

    text_primary: str = "#1F1F1F"
    text_secondary: str = "#5F6368"
    text_disabled: str = "#9AA0A6"
    text_on_primary: str = "#FFFFFF"

    # Feedback
    success: str = "#1E8E3E"
    success_bg: str = "#E6F4EA"
    warning: str = "#F9AB00"
    warning_bg: str = "#FEF7E0"
    danger: str = "#D93025"
    danger_bg: str = "#FCE8E6"
    info: str = "#0069B4"
    info_bg: str = "#E8F0FE"


@dataclass(frozen=True)
class Typography:
    """Escala tipográfica única da aplicação."""

    font_family: str = "Segoe UI, Roboto, -apple-system, sans-serif"
    size_h1: int = 22
    size_h2: int = 18
    size_h3: int = 15
    size_body: int = 13
    size_caption: int = 11
    weight_regular: int = 400
    weight_medium: int = 500
    weight_bold: int = 700


@dataclass(frozen=True)
class Spacing:
    """Escala de espaçamento (múltiplos de 4px, padrão Material/Google)."""

    xs: int = 4
    sm: int = 8
    md: int = 16
    lg: int = 24
    xl: int = 32
    xxl: int = 48

    radius_sm: int = 6
    radius_md: int = 10
    radius_lg: int = 16

    header_height: int = 64


# Instâncias globais (podem ser trocadas por um ThemeManager no futuro,
# se for necessário suportar dark mode ou temas por cliente).
PALETTE = Palette()
TYPOGRAPHY = Typography()
SPACING = Spacing()


def base_stylesheet() -> str:
    """Retorna o QSS global aplicado à janela principal.

    Estilos específicos de componentes (botões, cards) ficam junto de
    cada componente em ``src/ui/components`` para manter coesão alta
    (cada arquivo é responsável apenas pelo seu próprio visual).
    """
    p, t = PALETTE, TYPOGRAPHY
    return f"""
        QWidget {{
            font-family: {t.font_family};
            font-size: {t.size_body}px;
            color: {p.text_primary};
            background-color: {p.surface};
        }}
        QMainWindow {{
            background-color: {p.surface_alt};
        }}
        QToolTip {{
            background-color: {p.text_primary};
            color: {p.text_on_primary};
            border: none;
            padding: 4px 8px;
            border-radius: {SPACING.radius_sm}px;
        }}
        QScrollBar:vertical {{
            background: transparent;
            width: 10px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {p.border_strong};
            border-radius: 5px;
            min-height: 24px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {p.text_secondary};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
    """


def heading_style(level: int = 1) -> str:
    """QSS inline para títulos (h1/h2/h3), usado via ``setStyleSheet``."""
    t = TYPOGRAPHY
    sizes = {1: t.size_h1, 2: t.size_h2, 3: t.size_h3}
    size = sizes.get(level, t.size_body)
    return f"font-size: {size}px; font-weight: {t.weight_bold}; color: {PALETTE.text_primary};"


def header_gradient_style() -> str:
    """QSS do header institucional: faixa em gradiente vermelho SENAI,
    com uma borda inferior no azul ZEISS — é o que dá identidade visual
    real à aplicação (em vez de uma barra branca genérica).
    """
    p = PALETTE
    return f"""
        QWidget#AppHeader {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 {p.senai_red_dark}, stop:0.55 {p.senai_red}, stop:1 {p.senai_red_hover}
            );
            border-bottom: 3px solid {p.zeiss_blue};
        }}
    """


def apply_elevation(widget: QWidget, blur: int = 20, y_offset: int = 3, alpha: int = 45) -> None:
    """Aplica uma sombra sutil (Material-like) a cards e painéis.

    Substitui o visual "chapado" (sem profundidade) por elevação real —
    um dos motivos da UI parecer datada era a ausência disso: tudo tinha
    a mesma altura visual, sem hierarquia.
    """
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, y_offset)
    effect.setColor(QColor(20, 24, 32, alpha))
    widget.setGraphicsEffect(effect)


def caption_style(muted: bool = True) -> str:
    color = PALETTE.text_secondary if muted else PALETTE.text_primary
    return f"font-size: {TYPOGRAPHY.size_caption}px; color: {color};"