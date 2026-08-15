"""
Header institucional — gradiente SENAI, breadcrumb dinâmico e navegação textual.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QCursor, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.ui.accessibility.themes import is_light_palette
from src.ui.components.icons import icon_cog, icon_help
from src.ui.styles import (
    PALETTE,
    SPACING,
    TYPOGRAPHY,
    header_badge_style,
    header_gradient_style,
    header_help_button_style,
    header_logo_button_style,
)

_ASSETS_DIR = Path(__file__).parents[3] / "assets"

BreadcrumbHandler = Callable[[], None] | None

# Preferência: variantes white no escuro; coloridas (sem "white") no claro.
_LEADING_LOGOS_DARK = (
    "logo-centro-white.png",
    "logo-centro-senai-white.png",
    "logo-senai-white.png",
    "logo-centro-senai.png",
    "logo-senai.png",
    "logo-centro.png",
)
_LEADING_LOGOS_LIGHT = (
    "logo-centro.png",
    "logo-centro-senai.png",
    "logo-senai.png",
    "logo-centro-white.png",
    "logo-centro-senai-white.png",
    "logo-senai-white.png",
)
_TRAILING_LOGOS_DARK = ("logo-senai-white.png", "logo-senai.png")
_TRAILING_LOGOS_LIGHT = ("logo-senai.png", "logo-senai-white.png")


def _leading_logo_candidates() -> tuple[str, ...]:
    return _LEADING_LOGOS_LIGHT if is_light_palette() else _LEADING_LOGOS_DARK


def _trailing_logo_candidates(preferred: Sequence[str] = ()) -> tuple[str, ...]:
    theme_defaults = _TRAILING_LOGOS_LIGHT if is_light_palette() else _TRAILING_LOGOS_DARK
    if not preferred:
        return theme_defaults
    # Se o caller passou só variantes white, troca pela lista do tema.
    if all("white" in name for name in preferred) and is_light_palette():
        return theme_defaults
    if all("white" not in name for name in preferred) and not is_light_palette():
        return theme_defaults
    return tuple(preferred)


def _first_existing_logo(candidates: Sequence[str]) -> Path | None:
    for candidate in candidates:
        path = _ASSETS_DIR / candidate
        if path.exists():
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                return path
    return None


class BreadcrumbBar(QWidget):
    """Trilha de navegação — segmento ativo destacado em laranja."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)
        self._segments: list[tuple[str, BreadcrumbHandler]] = []

    def set_segments(self, segments: list[tuple[str, BreadcrumbHandler]]) -> None:
        self._segments = list(segments)
        self._rebuild()

    def refresh_appearance(self) -> None:
        self._rebuild()

    def _rebuild(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        p = PALETTE
        last_index = len(self._segments) - 1

        for index, (label, handler) in enumerate(self._segments):
            if index > 0:
                sep = QLabel("/")
                sep.setStyleSheet(
                    f"color: {p.text_disabled}; background: transparent; "
                    f"font-size: {TYPOGRAPHY.size_body}px; border: none; padding: 0 2px;"
                )
                self._layout.addWidget(sep)

            is_active = index == last_index and handler is None
            if handler is not None:
                btn = QPushButton(label)
                btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn.setFlat(True)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        color: {p.text_secondary};
                        background: transparent;
                        border: none;
                        font-size: {TYPOGRAPHY.size_body}px;
                        font-weight: {TYPOGRAPHY.weight_medium};
                        padding: 0;
                        text-align: left;
                    }}
                    QPushButton:hover {{
                        color: {p.senai_orange};
                    }}
                """)
                btn.clicked.connect(handler)
                self._layout.addWidget(btn)
            else:
                color = p.senai_orange if is_active else p.text_muted
                weight = TYPOGRAPHY.weight_semibold if is_active else TYPOGRAPHY.weight_regular
                lbl = QLabel(label)
                lbl.setStyleSheet(
                    f"color: {color}; font-size: {TYPOGRAPHY.size_body}px; font-weight: {weight}; "
                    f"background: transparent; border: none;"
                )
                self._layout.addWidget(lbl)


class _TextNavLink(QPushButton):
    """Link textual minimalista — sem ícones estilo navegador."""

    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFlat(True)
        self.setStyleSheet(AppHeader._nav_link_stylesheet())


class AppHeader(QWidget):
    """Faixa superior institucional com breadcrumb e navegação textual."""

    back_requested = pyqtSignal()
    forward_requested = pyqtSignal()
    home_requested = pyqtSignal()
    help_requested = pyqtSignal()
    preferences_requested = pyqtSignal()

    def __init__(
        self,
        subtitle: str = "Centro de Excelência em Metrologia",
        *,
        trailing_logos: Sequence[str] = (),
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("AppHeader")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(header_gradient_style())
        self.setFixedHeight(self._scaled_header_height())

        self._badge_label = QLabel()
        self._help_btn: QPushButton | None = None
        self._settings_btn: QPushButton | None = None
        self._back_link: Optional[_TextNavLink] = None
        self._forward_link: Optional[_TextNavLink] = None
        self._nav_divider: Optional[QFrame] = None
        self._brand_btn: Optional[QPushButton] = None
        self._breadcrumb = BreadcrumbBar()
        self._trailing_logo_preferred = tuple(trailing_logos)
        self._leading_logo_btn: QPushButton | None = None
        self._trailing_logo_buttons: list[QPushButton] = []
        self._trailing_logo_paths: list[Path] = []

        self._build_ui(subtitle)

    def _build_ui(self, subtitle: str) -> None:
        p, t, s = PALETTE, TYPOGRAPHY, SPACING
        layout = QHBoxLayout(self)
        layout.setContentsMargins(s.xl, s.sm, s.xl, s.sm)
        layout.setSpacing(s.md)

        logo_loaded = self._add_leading_logo(layout)
        if logo_loaded:
            layout.addSpacing(s.sm)

        text_container = QVBoxLayout()
        text_container.setSpacing(4)
        text_container.setContentsMargins(0, 0, 0, 0)

        if not logo_loaded:
            self._brand_btn = QPushButton("SENAI  ×  ZEISS")
            self._brand_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._brand_btn.setToolTip("Ir para Início")
            self._brand_btn.setFlat(True)
            self._brand_btn.setStyleSheet(self._brand_button_stylesheet())
            self._brand_btn.clicked.connect(self.home_requested.emit)
            text_container.addWidget(self._brand_btn)

        nav_row = QHBoxLayout()
        nav_row.setSpacing(10)
        nav_row.setContentsMargins(0, 0, 0, 0)

        self._back_link = _TextNavLink("Voltar")
        self._back_link.setToolTip("Voltar (Alt+←)")
        self._back_link.clicked.connect(self.back_requested.emit)
        self._back_link.hide()
        nav_row.addWidget(self._back_link)

        self._forward_link = _TextNavLink("Avançar")
        self._forward_link.setToolTip("Avançar (Alt+→)")
        self._forward_link.clicked.connect(self.forward_requested.emit)
        self._forward_link.hide()
        nav_row.addWidget(self._forward_link)

        self._nav_divider = QFrame()
        self._nav_divider.setFixedSize(1, 14)
        self._nav_divider.setStyleSheet(self._nav_divider_stylesheet())
        self._nav_divider.hide()
        nav_row.addWidget(self._nav_divider)

        nav_row.addWidget(self._breadcrumb)
        text_container.addLayout(nav_row)

        layout.addLayout(text_container)
        layout.addStretch(1)

        self._settings_btn = QPushButton()
        self._settings_btn.setObjectName("AppHeaderSettingsBtn")
        self._settings_btn.setIcon(icon_cog())
        self._settings_btn.setIconSize(QSize(18, 18))
        self._settings_btn.setFixedSize(38, 38)
        self._settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._settings_btn.setToolTip("Preferências (acessibilidade e armazenamento)")
        self._settings_btn.clicked.connect(self.preferences_requested.emit)
        self._apply_settings_button_style()
        layout.addWidget(self._settings_btn)

        self._help_btn = QPushButton()
        self._help_btn.setObjectName("AppHeaderHelpBtn")
        self._help_btn.setIcon(icon_help())
        self._help_btn.setIconSize(QSize(18, 18))
        self._help_btn.setFixedSize(38, 38)
        self._help_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._help_btn.setToolTip("Ajuda (F1)")
        self._help_btn.clicked.connect(self.help_requested.emit)
        self._apply_help_button_style()
        layout.addWidget(self._help_btn)

        self._badge_label.setObjectName("AppHeaderBadge")
        self._badge_label.setText("Pós-processador de Relatórios")
        self._apply_badge_style()
        layout.addWidget(self._badge_label)

        trailing = _trailing_logo_candidates(self._trailing_logo_preferred)
        if trailing:
            layout.addSpacing(s.sm)
            self._add_trailing_logos(layout, trailing)

        if subtitle and subtitle != "Centro de Excelência em Metrologia":
            self.set_subtitle(subtitle)
        else:
            self._breadcrumb.set_segments([("Início", None)])

    def _create_logo_button(self, path: Path, *, trailing: bool = False) -> QPushButton:
        pixmap = QPixmap(str(path))
        scaled = pixmap.scaledToHeight(40, Qt.TransformationMode.SmoothTransformation)
        logo_btn = QPushButton()
        logo_btn.setObjectName(
            "AppHeaderTrailingLogoBtn" if trailing else "AppHeaderLogoBtn"
        )
        logo_btn.setIcon(QIcon(scaled))
        logo_btn.setIconSize(scaled.size())
        logo_btn.setFixedSize(scaled.width() + 8, 44)
        logo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logo_btn.setToolTip("Ir para Início" if not trailing else path.stem.replace("-", " ").title())
        logo_btn.setStyleSheet(header_logo_button_style())
        if not trailing:
            logo_btn.clicked.connect(self.home_requested.emit)
        return logo_btn

    def _apply_logo_pixmap(self, btn: QPushButton, path: Path) -> None:
        pixmap = QPixmap(str(path))
        scaled = pixmap.scaledToHeight(40, Qt.TransformationMode.SmoothTransformation)
        btn.setIcon(QIcon(scaled))
        btn.setIconSize(scaled.size())
        btn.setFixedSize(scaled.width() + 8, 44)
        btn.setToolTip(
            "Ir para Início"
            if btn.objectName() == "AppHeaderLogoBtn"
            else path.stem.replace("-", " ").title()
        )
        btn.setStyleSheet(header_logo_button_style())

    def _add_leading_logo(self, layout: QHBoxLayout) -> bool:
        path = _first_existing_logo(_leading_logo_candidates())
        if path is None:
            return False
        self._leading_logo_btn = self._create_logo_button(path, trailing=False)
        layout.addWidget(self._leading_logo_btn)
        return True

    def _add_trailing_logos(self, layout: QHBoxLayout, candidates: Sequence[str]) -> None:
        path = _first_existing_logo(candidates)
        if path is None:
            return
        btn = self._create_logo_button(path, trailing=True)
        layout.addWidget(btn)
        self._trailing_logo_buttons.append(btn)
        self._trailing_logo_paths.append(path)

    def add_trailing_logo(self, asset_name: str) -> bool:
        """Adiciona logo no canto direito. Coloque o arquivo em ``assets/``."""
        path = _ASSETS_DIR / asset_name
        if not path.exists():
            return False
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            return False
        layout = self.layout()
        if not isinstance(layout, QHBoxLayout):
            return False
        btn = self._create_logo_button(path, trailing=True)
        layout.addWidget(btn)
        self._trailing_logo_buttons.append(btn)
        self._trailing_logo_paths.append(path)
        return True

    def set_breadcrumb(self, segments: list[tuple[str, BreadcrumbHandler]]) -> None:
        self._breadcrumb.set_segments(segments)

    def set_subtitle(self, text: str) -> None:
        self._breadcrumb.set_segments([(text, None)])

    def set_badge_text(self, text: str) -> None:
        self._badge_label.setText(text)

    def set_navigation_state(self, can_back: bool, can_forward: bool) -> None:
        show_nav = can_back or can_forward
        if self._back_link:
            self._back_link.setVisible(can_back)
            self._back_link.setEnabled(can_back)
        if self._forward_link:
            self._forward_link.setVisible(can_forward)
            self._forward_link.setEnabled(can_forward)
        if self._nav_divider:
            self._nav_divider.setVisible(show_nav)

    def _apply_settings_button_style(self) -> None:
        if self._settings_btn is None:
            return
        self._settings_btn.setIcon(icon_cog())
        self._settings_btn.setStyleSheet(header_help_button_style())

    def _apply_help_button_style(self) -> None:
        if self._help_btn is None:
            return
        self._help_btn.setIcon(icon_help())
        self._help_btn.setStyleSheet(header_help_button_style())

    def _apply_badge_style(self) -> None:
        self._badge_label.setStyleSheet(header_badge_style())

    def _sync_logos_for_theme(self) -> None:
        leading = _first_existing_logo(_leading_logo_candidates())
        if leading is not None and self._leading_logo_btn is not None:
            self._apply_logo_pixmap(self._leading_logo_btn, leading)

        trailing_path = _first_existing_logo(
            _trailing_logo_candidates(self._trailing_logo_preferred)
        )
        if trailing_path is not None and self._trailing_logo_buttons:
            self._apply_logo_pixmap(self._trailing_logo_buttons[0], trailing_path)
            self._trailing_logo_paths[0] = trailing_path

    def refresh_appearance(self) -> None:
        """Reaplica estilos após mudança de tema/contraste/fonte."""
        self.setFixedHeight(self._scaled_header_height())
        self.setStyleSheet(header_gradient_style())
        self._apply_settings_button_style()
        self._apply_help_button_style()
        self._apply_badge_style()
        self._sync_logos_for_theme()
        self._breadcrumb.refresh_appearance()
        if self._brand_btn is not None:
            self._brand_btn.setStyleSheet(self._brand_button_stylesheet())
        if self._back_link:
            self._back_link.setStyleSheet(self._nav_link_stylesheet())
        if self._forward_link:
            self._forward_link.setStyleSheet(self._nav_link_stylesheet())
        if self._nav_divider:
            self._nav_divider.setStyleSheet(self._nav_divider_stylesheet())

    @staticmethod
    def _scaled_header_height() -> int:
        return max(72, round(88 * TYPOGRAPHY.size_body / 13))

    @staticmethod
    def _nav_divider_stylesheet() -> str:
        return f"background: {PALETTE.border}; border: none;"

    @staticmethod
    def _brand_button_stylesheet() -> str:
        p, t = PALETTE, TYPOGRAPHY
        return f"""
            QPushButton {{
                color: {p.text_primary};
                font-size: {t.size_h3}px;
                font-weight: {t.weight_bold};
                letter-spacing: 1.2px;
                background: transparent;
                border: none;
                text-align: left;
                padding: 0;
            }}
            QPushButton:hover {{ color: {p.senai_orange}; }}
        """

    @staticmethod
    def _nav_link_stylesheet() -> str:
        p = PALETTE
        t = TYPOGRAPHY
        return f"""
            QPushButton {{
                color: {p.text_secondary};
                background: transparent;
                border: none;
                font-size: {t.size_body}px;
                font-weight: {t.weight_medium};
                padding: 0 4px;
            }}
            QPushButton:hover:enabled {{
                color: {p.senai_orange};
            }}
            QPushButton:disabled {{
                color: {p.text_disabled};
            }}
        """
