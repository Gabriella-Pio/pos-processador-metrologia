"""
Design System Premium — Dark Navy Edition.

Estrutura:
  tokens.py       → paleta, tipografia, espaçamento
  components.qss  → estilos globais da aplicação
  widgets.qss     → fragmentos por componente (tab, card, input…)
  qss_loader.py   → carrega e interpola tokens nos templates
  helpers.py      → API pública de estilos
"""
from src.ui.styles.helpers import (
    action_card_hover_style,
    action_card_icon_style,
    action_card_idle_style,
    action_card_subtitle_style,
    action_card_title_style,
    apply_elevation,
    badge_style,
    base_stylesheet,
    caption_style,
    card_style,
    default_template_badge_style,
    empty_state_cta_style,
    filter_toggle_button_style,
    form_label_style,
    header_badge_style,
    header_gradient_style,
    header_help_button_style,
    header_logo_button_style,
    heading_style,
    labeled_input_style,
    list_card_frame_style,
    panel_scroll_style,
    pdf_icon_pill_style,
    recent_file_row_style,
    search_bar_container_style,
    search_bar_divider_style,
    search_field_inner_style,
    search_icon_style,
    sidebar_panel_style,
    tab_bar_shell_style,
    tab_style,
    view_toggle_style,
)
from src.ui.styles.tokens import (
    DASHBOARD_CARD_WIDTH,
    PALETTE,
    SPACING,
    TYPOGRAPHY,
)

__all__ = [
    "DASHBOARD_CARD_WIDTH",
    "PALETTE",
    "SPACING",
    "TYPOGRAPHY",
    "action_card_hover_style",
    "action_card_icon_style",
    "action_card_idle_style",
    "action_card_subtitle_style",
    "action_card_title_style",
    "apply_elevation",
    "badge_style",
    "base_stylesheet",
    "caption_style",
    "card_style",
    "default_template_badge_style",
    "empty_state_cta_style",
    "filter_toggle_button_style",
    "form_label_style",
    "header_badge_style",
    "header_gradient_style",
    "header_help_button_style",
    "header_logo_button_style",
    "heading_style",
    "labeled_input_style",
    "list_card_frame_style",
    "panel_scroll_style",
    "pdf_icon_pill_style",
    "recent_file_row_style",
    "search_bar_container_style",
    "search_bar_divider_style",
    "search_field_inner_style",
    "search_icon_style",
    "sidebar_panel_style",
    "tab_bar_shell_style",
    "tab_style",
    "view_toggle_style",
]
