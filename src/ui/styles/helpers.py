"""Funções de estilo Python — delegam tokens e fragmentos QSS quando possível."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QLabel, QWidget

from src.ui.styles.qss_loader import load_fragment, load_qss
from src.ui.styles.tokens import PALETTE, SPACING, TYPOGRAPHY


def base_stylesheet() -> str:
    return load_qss("components.qss")


def heading_style(level: int = 1) -> str:
    t = TYPOGRAPHY
    p = PALETTE
    sizes = {1: t.size_h1, 2: t.size_h2, 3: t.size_h3}
    weights = {1: t.weight_bold, 2: t.weight_semibold, 3: t.weight_semibold}
    size = sizes.get(level, t.size_body)
    weight = weights.get(level, t.weight_medium)
    return (
        f"font-size: {size}px; font-weight: {weight}; "
        f"color: {p.text_primary}; background: transparent;"
    )


def header_gradient_style() -> str:
    from src.ui.accessibility.themes import is_light_palette

    if is_light_palette():
        return load_fragment("header_gradient")
    # Tema escuro: faixa institucional (não só tokens de superfície).
    return """
QWidget#AppHeader {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #1d0c08,
        stop:0.40 #0D1117,
        stop:1 #0a0e1a
    );
    border-bottom: 3px solid #f0431e;
}
"""


def header_help_button_style() -> str:
    from src.ui.accessibility.themes import is_light_palette

    if is_light_palette():
        return load_fragment("header_help_btn")
    return """
QPushButton#AppHeaderHelpBtn,
QPushButton#AppHeaderSettingsBtn {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 10px;
}
QPushButton#AppHeaderHelpBtn:hover,
QPushButton#AppHeaderSettingsBtn:hover {
    background: rgba(240, 67, 30, 0.22);
    border-color: rgba(240, 67, 30, 0.45);
}
"""


def header_badge_style() -> str:
    return load_fragment("header_badge")


def header_logo_button_style() -> str:
    from src.ui.accessibility.themes import is_light_palette

    if is_light_palette():
        return load_fragment("header_logo_btn")
    return """
QPushButton#AppHeaderLogoBtn, QPushButton#AppHeaderTrailingLogoBtn {
    background: transparent;
    border: none;
}
QPushButton#AppHeaderLogoBtn:hover, QPushButton#AppHeaderTrailingLogoBtn:hover {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 8px;
}
"""


def apply_elevation(
    widget: QWidget,
    blur: int = 24,
    y_offset: int = 4,
    alpha: int = 80,
) -> None:
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, y_offset)
    effect.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(effect)


def restore_link_color() -> str:
    """Azul institucional no claro (contraste); azul claro no escuro."""
    from src.ui.accessibility.themes import is_light_palette

    return PALETTE.senai_blue if is_light_palette() else PALETTE.senai_blue_light


def configure_restore_link(label: QLabel, *, caption: str = "Restaurar") -> None:
    """QLabel com ``<a>`` visível nos dois temas — o QSS não pinta âncoras HTML."""
    color = restore_link_color()
    label.setObjectName("FieldRestoreLink")
    label.setTextFormat(Qt.TextFormat.RichText)
    label.setOpenExternalLinks(False)
    label.setCursor(Qt.CursorShape.PointingHandCursor)
    label.setText(
        f'<a href="restore" style="color:{color}; text-decoration:none;">{caption}</a>'
    )
    palette = label.palette()
    qcolor = QColor(color)
    palette.setColor(QPalette.ColorRole.Link, qcolor)
    palette.setColor(QPalette.ColorRole.LinkVisited, qcolor)
    label.setPalette(palette)


def caption_style(muted: bool = True) -> str:
    color = PALETTE.text_secondary if muted else PALETTE.text_primary
    return (
        f"font-size: {TYPOGRAPHY.size_caption}px; "
        f"color: {color}; "
        f"background: transparent;"
    )


def badge_style(color: str, bg: str) -> str:
    s = SPACING
    return (
        f"color: {color}; background-color: {bg}; "
        f"border-radius: {s.radius_pill}px; "
        f"font-size: {TYPOGRAPHY.size_caption}px; "
        f"font-weight: {TYPOGRAPHY.weight_semibold}; "
        f"padding: 2px 8px;"
    )


def sidebar_panel_style() -> str:
    p = PALETTE
    return f"background-color: {p.bg_sidebar}; border: none;"


def card_style(hover: bool = False) -> str:
    p, s = PALETTE, SPACING
    border = p.senai_blue_light if hover else p.border
    return (
        f"background-color: {p.bg_surface}; "
        f"border: 1px solid {border}; "
        f"border-radius: {s.radius_md}px;"
    )


def tab_bar_shell_style() -> str:
    return load_fragment("tab_bar_shell")


def tab_style(*, active: bool = False) -> str:
    return load_fragment("tab_active" if active else "tab_inactive")


def view_toggle_style(*, active: bool = False) -> str:
    return load_fragment("view_toggle_active" if active else "view_toggle_inactive")


def app_popup_menu_style() -> str:
    """Estilo direto do menu popup — QSS global falha em alguns temas nativos (ex.: light)."""
    p, s = PALETTE, SPACING
    return f"""
        QMenu#AppPopupMenu {{
            background-color: {p.bg_elevated};
            color: {p.text_primary};
            border: 1px solid {p.border_strong};
            border-radius: {s.radius_sm}px;
            padding: 4px;
        }}
        QMenu#AppPopupMenu::item {{
            color: {p.text_primary};
            background-color: transparent;
            padding: 8px 16px 8px 12px;
            border-radius: 4px;
        }}
        QMenu#AppPopupMenu::item:selected {{
            color: {p.text_primary};
            background-color: rgba(240, 67, 30, 0.22);
        }}
        QMenu#AppPopupMenu::item:disabled {{
            color: {p.text_disabled};
        }}
        QMenu#AppPopupMenu::separator {{
            height: 1px;
            background: {p.border};
            margin: 4px 8px;
        }}
        QMenu#AppPopupMenu::indicator {{
            width: 0px;
            height: 0px;
        }}
    """


def configure_app_popup_menu(menu) -> None:
    """Aplica objectName, fundo opaco e cores do tema ao QMenu flutuante."""
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QColor, QPalette

    menu.setObjectName("AppPopupMenu")
    menu.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    menu.setStyleSheet(app_popup_menu_style())
    palette = menu.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor(PALETTE.bg_elevated))
    palette.setColor(QPalette.ColorRole.Base, QColor(PALETTE.bg_elevated))
    palette.setColor(QPalette.ColorRole.Text, QColor(PALETTE.text_primary))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(PALETTE.text_primary))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(PALETTE.text_primary))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(240, 67, 30, 56))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(PALETTE.text_primary))
    menu.setPalette(palette)


def action_card_idle_style() -> str:
    return load_fragment("action_card_idle")


def action_card_hover_style(accent_color: str | None = None) -> str:
    p = PALETTE
    return load_fragment("action_card_hover", accent_color=accent_color or p.senai_blue_light)


def dashboard_card_media_style(*, orange: bool = False) -> str:
    return load_fragment(
        "dashboard_card_media_orange" if orange else "dashboard_card_media"
    )


def action_card_icon_style(
    *,
    accent_color: str,
    accent_bg: str,
    icon: str,
) -> str:
    t = TYPOGRAPHY
    font_size = f"{t.size_caption}px" if len(icon) > 1 else f"{t.size_h2 + 4}px"
    letter_spacing = "1px" if len(icon) > 1 else "0px"
    return (
        f"background-color: {accent_bg}; "
        f"color: {accent_color}; "
        f"font-size: {font_size}; "
        f"font-weight: {t.weight_bold}; "
        f"border-radius: 14px; "
        f"border: none; "
        f"letter-spacing: {letter_spacing};"
    )


def action_card_title_style() -> str:
    return load_fragment("action_card_title")


def action_card_subtitle_style() -> str:
    return load_fragment("action_card_subtitle")


def recent_file_row_style() -> str:
    return load_fragment("recent_file_row")


def pdf_icon_pill_style() -> str:
    return load_fragment("pdf_icon_pill")


def default_template_badge_style() -> str:
    return load_fragment("default_template_badge")


def list_card_frame_style() -> str:
    return load_fragment("list_card_frame")


def form_label_style() -> str:
    return load_fragment("form_label")


def labeled_input_style(*, invalid: bool = False) -> str:
    p = PALETTE
    border_color = p.danger if invalid else p.border
    focus_color = p.danger if invalid else p.senai_blue_light
    return load_fragment(
        "labeled_input",
        border_color=border_color,
        focus_color=focus_color,
    )


def search_bar_container_style(*, focused: bool = False) -> str:
    p = PALETTE
    border_color = p.senai_blue_light if focused else p.border
    background = p.bg_surface_alt if focused else p.bg_surface
    return load_fragment(
        "search_bar_container",
        border_color=border_color,
        background=background,
    )


def search_field_inner_style() -> str:
    return load_fragment("search_field_inner")


def search_icon_style() -> str:
    return load_fragment("search_icon")


def search_bar_divider_style() -> str:
    return load_fragment("search_bar_divider")


def filter_toggle_button_style() -> str:
    return load_fragment("filter_toggle_button")


def panel_scroll_style() -> str:
    return load_fragment("panel_scroll")


def workspace_bookmark_search_style() -> str:
    return load_fragment("workspace_bookmark_search")


def workspace_bookmark_tree_style() -> str:
    return load_fragment("workspace_bookmark_tree")


def workspace_image_list_style() -> str:
    return load_fragment("workspace_image_list")


def workspace_drop_hint_style(*, active: bool = False) -> str:
    name = "workspace_drop_hint_active" if active else "workspace_drop_hint"
    return load_fragment(name)


def workspace_annotation_toolbar_style() -> str:
    return load_fragment("workspace_annotation_toolbar")


def workspace_annotation_button_style() -> str:
    return load_fragment("workspace_annotation_button")


def workspace_version_entry_style(*, is_latest: bool = False) -> str:
    p = PALETTE
    entry_bg = p.bg_surface_alt if is_latest else "transparent"
    return load_fragment("workspace_version_entry", entry_bg=entry_bg)


def inline_banner_style(*, color: str, bg: str) -> str:
    return load_fragment("inline_banner", banner_color=color, banner_bg=bg)


def primary_button_style() -> str:
    p, s, t = PALETTE, SPACING, TYPOGRAPHY
    return f"""
        QPushButton {{
            background-color: {p.senai_orange};
            color: {p.text_on_primary};
            border: none;
            border-bottom: 3px solid {p.senai_orange_dark};
            border-radius: {s.radius_md}px;
            padding: 7px {s.lg}px;
            font-weight: {t.weight_semibold};
            font-size: {t.size_body}px;
        }}
        QPushButton:hover {{
            background-color: {p.senai_orange_hover};
            border-bottom-color: {p.senai_orange_dark};
        }}
        QPushButton:pressed {{
            background-color: {p.senai_orange_dark};
            border-bottom-width: 1px;
            padding-top: 9px;
        }}
        QPushButton:disabled {{
            background-color: {p.text_disabled};
            border-bottom-color: transparent;
            color: {p.text_on_primary};
        }}
    """


def secondary_button_style() -> str:
    p, s, t = PALETTE, SPACING, TYPOGRAPHY
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {p.senai_blue_light};
            border: 1.5px solid {p.senai_blue};
            border-radius: {s.radius_md}px;
            padding: 7px {s.lg}px;
            font-weight: {t.weight_medium};
            font-size: {t.size_body}px;
        }}
        QPushButton:hover {{
            background-color: rgba(74, 111, 212, 0.15);
            border-color: {p.senai_blue_light};
            color: {p.text_primary};
        }}
        QPushButton:pressed {{
            background-color: rgba(74, 111, 212, 0.25);
        }}
        QPushButton:disabled {{
            color: {p.text_disabled};
            border-color: {p.border};
        }}
    """


def empty_state_cta_style() -> str:
    return load_fragment("empty_state_cta")
