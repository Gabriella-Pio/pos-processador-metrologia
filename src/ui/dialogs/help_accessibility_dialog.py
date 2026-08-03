"""Diálogo de ajuda (atalhos) e painel de acessibilidade."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.ui.accessibility import FONT_SCALE_PRESETS, AppearanceManager, AppearanceSettings
from src.ui.components.buttons import PrimaryButton, SecondaryButton
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, heading_style

ShortcutRow = tuple[str, str, str]


SHORTCUT_GROUPS: tuple[tuple[str, tuple[ShortcutRow, ...]], ...] = (
    (
        "Navegação",
        (
            ("Alt+←", "Voltar", "Retorna à tela anterior"),
            ("Alt+→", "Avançar", "Avança na navegação"),
            ("F11", "Tela cheia", "Alterna janela maximizada / tela cheia"),
        ),
    ),
    (
        "Início",
        (
            ("Ctrl+N", "Novo arquivo", "Abre o assistente de importação de PDFs"),
            ("Ctrl+T", "Novo template", "Cria um template de relatório"),
            ("Ctrl+K", "Buscar", "Foca o campo de busca na Home"),
            ("Esc", "Limpar busca", "Limpa busca e filtros ativos"),
        ),
    ),
    (
        "Ajuda",
        (
            ("F1", "Ajuda", "Abre este painel de ajuda e acessibilidade"),
        ),
    ),
)

HELP_TIPS: tuple[str, ...] = (
    "Use os filtros da Home para refinar arquivos por período, projeto ou componente.",
    "Clique no logo SENAI ou em «Início» no breadcrumb para voltar à tela principal.",
    "Templates definem a estrutura reutilizável dos relatórios exportados.",
    "Preferências de tema, contraste e fonte são salvas automaticamente.",
)


def _dialog_stylesheet() -> str:
    p = PALETTE
    s = SPACING
    return f"""
        QDialog {{
            background-color: {p.bg_surface};
        }}
        QTabWidget::pane {{
            border: 1px solid {p.border};
            border-radius: {s.radius_md}px;
            background: {p.bg_surface_alt};
            top: -1px;
        }}
        QTabBar::tab {{
            background: transparent;
            color: {p.text_muted};
            border: none;
            border-bottom: 2px solid transparent;
            padding: 10px 18px;
            font-size: {TYPOGRAPHY.size_body}px;
            font-weight: {TYPOGRAPHY.weight_medium};
            margin-right: 4px;
        }}
        QTabBar::tab:selected {{
            color: {p.senai_orange};
            border-bottom: 2px solid {p.senai_orange};
            font-weight: {TYPOGRAPHY.weight_semibold};
        }}
        QTabBar::tab:hover {{
            color: {p.text_primary};
        }}
        QScrollArea {{
            background: transparent;
            border: none;
        }}
        QRadioButton {{
            color: {p.text_primary};
            spacing: 10px;
            font-size: {TYPOGRAPHY.size_body}px;
            padding: 4px 0;
        }}
        QRadioButton::indicator {{
            width: 16px;
            height: 16px;
        }}
    """


def _combo_stylesheet() -> str:
    p = PALETTE
    s = SPACING
    return f"""
        QComboBox {{
            background: {p.bg_surface};
            color: {p.text_primary};
            border: 1px solid {p.border_strong};
            border-radius: {s.radius_sm}px;
            padding: 10px 36px 10px 12px;
            font-size: {TYPOGRAPHY.size_body}px;
            min-height: 24px;
        }}
        QComboBox:hover {{
            border-color: {p.senai_blue_light};
            background: {p.bg_elevated};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 28px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {p.text_muted};
            margin-right: 10px;
        }}
        QComboBox QAbstractItemView {{
            background: {p.bg_elevated};
            color: {p.text_primary};
            border: 1px solid {p.border_strong};
            selection-background-color: rgba(240, 67, 30, 0.25);
            outline: none;
        }}
    """


def _scroll_page(content: QWidget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setWidget(content)
    return scroll


class HelpAccessibilityDialog(QDialog):
    """Centraliza atalhos do sistema e opções de acessibilidade."""

    def __init__(self, parent=None, *, initial_tab: int = 0) -> None:
        super().__init__(parent)
        self._manager = AppearanceManager.instance()
        self._draft = self._manager.settings
        self.setWindowTitle("Ajuda e Acessibilidade")
        self.setMinimumSize(580, 480)
        self.resize(640, 560)
        self._build_ui()
        self._tabs.setCurrentIndex(initial_tab)
        self._sync_controls_from_settings()

    def _build_ui(self) -> None:
        p = PALETTE
        self.setStyleSheet(_dialog_stylesheet())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        layout.setSpacing(SPACING.md)

        title = QLabel("Ajuda e Acessibilidade")
        title.setStyleSheet(heading_style(1))
        layout.addWidget(title)

        subtitle = QLabel(
            "Atalhos de teclado, dicas de uso e ajustes visuais para melhor leitura."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(
            f"color: {p.text_secondary}; font-size: {TYPOGRAPHY.size_body}px; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(subtitle)

        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        self._tabs.addTab(_scroll_page(self._build_shortcuts_tab()), "Atalhos")
        self._tabs.addTab(_scroll_page(self._build_accessibility_tab()), "Acessibilidade")
        layout.addWidget(self._tabs, stretch=1)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background: {p.border}; border: none;")
        layout.addWidget(divider)

        footer = QHBoxLayout()
        footer.setSpacing(SPACING.sm)
        reset_btn = SecondaryButton("Restaurar padrão")
        reset_btn.clicked.connect(self._reset_defaults)
        footer.addWidget(reset_btn)
        footer.addStretch(1)
        close_btn = PrimaryButton("Fechar")
        close_btn.setMinimumWidth(120)
        close_btn.clicked.connect(self.accept)
        footer.addWidget(close_btn)
        layout.addLayout(footer)

    def _build_shortcuts_tab(self) -> QWidget:
        p = PALETTE
        page = QWidget()
        page.setStyleSheet(f"background: transparent;")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        outer.setSpacing(SPACING.lg)

        for group_title, rows in SHORTCUT_GROUPS:
            outer.addWidget(self._group_title(group_title))
            outer.addWidget(self._shortcut_table(rows))

        outer.addWidget(self._group_title("Dicas"))
        tips_frame = QFrame()
        tips_frame.setStyleSheet(
            f"QFrame {{ background: {p.bg_surface}; border: 1px solid {p.border}; "
            f"border-radius: {SPACING.radius_md}px; }}"
        )
        tips_layout = QVBoxLayout(tips_frame)
        tips_layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)
        tips_layout.setSpacing(SPACING.sm)
        for tip in HELP_TIPS:
            row = QLabel(f"• {tip}")
            row.setWordWrap(True)
            row.setStyleSheet(
                f"color: {p.text_secondary}; font-size: {TYPOGRAPHY.size_body}px; "
                f"background: transparent; border: none;"
            )
            tips_layout.addWidget(row)
        outer.addWidget(tips_frame)
        outer.addStretch(1)
        return page

    def _group_title(self, text: str) -> QLabel:
        label = QLabel(text.upper())
        label.setStyleSheet(
            f"color: {PALETTE.text_muted}; font-size: 11px; "
            f"font-weight: {TYPOGRAPHY.weight_semibold}; letter-spacing: 0.8px; "
            f"background: transparent; border: none; margin-bottom: 2px;"
        )
        return label

    def _shortcut_table(self, rows: tuple[ShortcutRow, ...]) -> QFrame:
        p = PALETTE
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background: {p.bg_surface}; border: 1px solid {p.border}; "
            f"border-radius: {SPACING.radius_md}px; }}"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.xs)

        for index, (keys, action, description) in enumerate(rows):
            row = QHBoxLayout()
            row.setSpacing(SPACING.md)

            key_label = QLabel(keys)
            key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            key_label.setMinimumWidth(76)
            key_label.setStyleSheet(
                f"color: {p.senai_orange}; font-family: monospace; font-size: 12px; "
                f"font-weight: {TYPOGRAPHY.weight_bold}; background: rgba(240,67,30,0.12); "
                f"border: 1px solid rgba(240,67,30,0.25); border-radius: {SPACING.radius_sm}px; "
                f"padding: 6px 8px;"
            )

            text_col = QVBoxLayout()
            text_col.setSpacing(2)
            action_label = QLabel(action)
            action_label.setStyleSheet(
                f"color: {p.text_primary}; font-weight: {TYPOGRAPHY.weight_semibold}; "
                f"background: transparent; border: none;"
            )
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet(
                f"color: {p.text_muted}; font-size: 12px; background: transparent; border: none;"
            )
            text_col.addWidget(action_label)
            text_col.addWidget(desc_label)

            row.addWidget(key_label, 0, Qt.AlignmentFlag.AlignTop)
            row.addLayout(text_col, stretch=1)
            layout.addLayout(row)

            if index < len(rows) - 1:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setFixedHeight(1)
                sep.setStyleSheet(f"background: {p.border_subtle}; border: none;")
                layout.addWidget(sep)

        return frame

    def _build_accessibility_tab(self) -> QWidget:
        p = PALETTE
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        outer.setSpacing(SPACING.lg)

        outer.addWidget(self._settings_section(
            "Tema",
            "Escolha entre aparência escura ou clara.",
        ))
        theme_row = QHBoxLayout()
        theme_row.setSpacing(SPACING.xl)
        self._theme_group = QButtonGroup(self)
        self._theme_dark = QRadioButton("Escuro")
        self._theme_light = QRadioButton("Claro")
        for index, btn in enumerate((self._theme_dark, self._theme_light)):
            self._theme_group.addButton(btn, index)
            theme_row.addWidget(btn)
        theme_row.addStretch(1)
        outer.addLayout(theme_row)

        outer.addWidget(self._settings_section(
            "Contraste",
            "Alto contraste melhora legibilidade de textos e bordas.",
        ))
        contrast_row = QHBoxLayout()
        contrast_row.setSpacing(SPACING.xl)
        self._contrast_group = QButtonGroup(self)
        self._contrast_normal = QRadioButton("Normal")
        self._contrast_high = QRadioButton("Alto contraste")
        for index, btn in enumerate((self._contrast_normal, self._contrast_high)):
            self._contrast_group.addButton(btn, index)
            contrast_row.addWidget(btn)
        contrast_row.addStretch(1)
        outer.addLayout(contrast_row)

        outer.addWidget(self._settings_section(
            "Tamanho da fonte",
            "Ajuste o zoom global da interface.",
        ))
        self._font_combo = QComboBox()
        self._font_combo.setMinimumHeight(44)
        self._font_combo.setStyleSheet(_combo_stylesheet())
        for label, scale in FONT_SCALE_PRESETS:
            self._font_combo.addItem(label, scale)
        outer.addWidget(self._font_combo)

        hint = QLabel(
            "Alterações aplicadas imediatamente e salvas para a próxima sessão."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(
            f"color: {p.text_muted}; font-size: 12px; background: transparent; border: none;"
        )
        outer.addWidget(hint)

        preview = QFrame()
        preview.setStyleSheet(
            f"QFrame {{ background: {p.bg_surface}; border: 1px solid {p.border}; "
            f"border-radius: {SPACING.radius_md}px; }}"
        )
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)
        preview_layout.setSpacing(SPACING.xs)
        preview_caption = QLabel("PRÉ-VISUALIZAÇÃO")
        preview_caption.setStyleSheet(
            f"color: {p.text_muted}; font-size: 10px; font-weight: {TYPOGRAPHY.weight_semibold}; "
            f"letter-spacing: 0.6px; background: transparent; border: none;"
        )
        self._preview_title = QLabel("Relatório de Metrologia")
        self._preview_body = QLabel(
            "Texto de exemplo — dimensões, tolerâncias e resultados de medição."
        )
        self._preview_body.setWordWrap(True)
        preview_layout.addWidget(preview_caption)
        preview_layout.addWidget(self._preview_title)
        preview_layout.addWidget(self._preview_body)
        outer.addWidget(preview)

        self._theme_group.idClicked.connect(lambda _id: self._apply_draft())
        self._contrast_group.idClicked.connect(lambda _id: self._apply_draft())
        self._font_combo.currentIndexChanged.connect(lambda _idx: self._apply_draft())

        return page

    def _settings_section(self, title: str, description: str) -> QWidget:
        p = PALETTE
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        title_label = QLabel(title.upper())
        title_label.setStyleSheet(
            f"color: {p.text_muted}; font-size: 11px; "
            f"font-weight: {TYPOGRAPHY.weight_semibold}; letter-spacing: 0.8px; "
            f"background: transparent; border: none;"
        )
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(
            f"color: {p.text_secondary}; font-size: 12px; background: transparent; border: none;"
        )
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        return box

    def _sync_controls_from_settings(self) -> None:
        settings = self._draft
        self._theme_group.blockSignals(True)
        self._contrast_group.blockSignals(True)
        self._font_combo.blockSignals(True)
        try:
            self._theme_dark.setChecked(settings.theme == "dark")
            self._theme_light.setChecked(settings.theme == "light")
            self._contrast_normal.setChecked(settings.contrast == "normal")
            self._contrast_high.setChecked(settings.contrast == "high")
            for index in range(self._font_combo.count()):
                if abs(float(self._font_combo.itemData(index)) - settings.font_scale) < 0.001:
                    self._font_combo.setCurrentIndex(index)
                    break
        finally:
            self._theme_group.blockSignals(False)
            self._contrast_group.blockSignals(False)
            self._font_combo.blockSignals(False)
        self._refresh_preview_styles()
        self._refresh_widget_styles()

    def _collect_draft(self) -> AppearanceSettings:
        theme = "light" if self._theme_light.isChecked() else "dark"
        contrast = "high" if self._contrast_high.isChecked() else "normal"
        font_scale = float(self._font_combo.currentData() or 1.0)
        return AppearanceSettings(theme=theme, contrast=contrast, font_scale=font_scale)

    def _apply_draft(self) -> None:
        self._draft = self._collect_draft()
        self._manager.apply(self._draft)
        self._refresh_preview_styles()
        self._refresh_widget_styles()

    def _reset_defaults(self) -> None:
        self._draft = AppearanceSettings()
        self._manager.apply(self._draft)
        self._sync_controls_from_settings()

    def _refresh_preview_styles(self) -> None:
        p = PALETTE
        self._preview_title.setStyleSheet(
            f"color: {p.text_primary}; font-size: {TYPOGRAPHY.size_h3}px; "
            f"font-weight: {TYPOGRAPHY.weight_bold}; background: transparent; border: none;"
        )
        self._preview_body.setStyleSheet(
            f"color: {p.text_secondary}; font-size: {TYPOGRAPHY.size_body}px; "
            f"background: transparent; border: none;"
        )

    def _refresh_widget_styles(self) -> None:
        """Atualiza estilos do próprio diálogo após mudança de tema."""
        self.setStyleSheet(_dialog_stylesheet())
        self._font_combo.setStyleSheet(_combo_stylesheet())
