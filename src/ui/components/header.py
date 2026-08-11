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

_LEADING_LOGO_CANDIDATES = (
    "logo-centro-white.png",
    "logo-centro-senai-white.png",
    "logo-senai-white.png",
    "logo-centro-senai.png",
    "logo-senai.png",
    "logo-centro.png",
)


class BreadcrumbBar(QWidget):
    """Trilha de navegação — segmento ativo destacado em laranja."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)

    def set_segments(self, segments: list[tuple[str, BreadcrumbHandler]]) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        p = PALETTE
        last_index = len(segments) - 1

        for index, (label, handler) in enumerate(segments):
            if index > 0:
                sep = QLabel("/")
                sep.setStyleSheet(
                    f"color: rgba(255,255,255,0.25); background: transparent; "
                    f"font-size: 13px; border: none; padding: 0 2px;"
                )
                self._layout.addWidget(sep)

            is_active = index == last_index and handler is None
            if handler is not None:
                btn = QPushButton(label)
                btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn.setFlat(True)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        color: rgba(255,255,255,0.70);
                        background: transparent;
                        border: none;
                        font-size: 13px;
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
                color = p.senai_orange if is_active else "rgba(255,255,255,0.55)"
                weight = TYPOGRAPHY.weight_semibold if is_active else TYPOGRAPHY.weight_regular
                lbl = QLabel(label)
                lbl.setStyleSheet(
                    f"color: {color}; font-size: 13px; font-weight: {weight}; "
                    f"background: transparent; border: none;"
                )
                self._layout.addWidget(lbl)


class _TextNavLink(QPushButton):
    """Link textual minimalista — sem ícones estilo navegador."""

    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent)
        p = PALETTE
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFlat(True)
        self.setStyleSheet(f"""
            QPushButton {{
                color: rgba(255,255,255,0.55);
                background: transparent;
                border: none;
                font-size: 13px;
                font-weight: {TYPOGRAPHY.weight_medium};
                padding: 0 4px;
            }}
            QPushButton:hover:enabled {{
                color: {p.senai_orange};
            }}
            QPushButton:disabled {{
                color: rgba(255,255,255,0.15);
            }}
        """)


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
        self.setStyleSheet(header_gradient_style())
        self.setFixedHeight(88)

        self._badge_label = QLabel()
        self._help_btn: QPushButton | None = None
        self._settings_btn: QPushButton | None = None
        self._back_link: Optional[_TextNavLink] = None
        self._forward_link: Optional[_TextNavLink] = None
        self._nav_divider: Optional[QFrame] = None
        self._brand_btn: Optional[QPushButton] = None
        self._breadcrumb = BreadcrumbBar()
        self._trailing_logo_candidates = tuple(trailing_logos)
        self._trailing_logo_buttons: list[QPushButton] = []

        self._build_ui(subtitle)

    def _build_ui(self, subtitle: str) -> None:
        p, t, s = PALETTE, TYPOGRAPHY, SPACING
        layout = QHBoxLayout(self)
        layout.setContentsMargins(s.xl, s.sm, s.xl, s.sm)
        layout.setSpacing(s.md)

        logo_loaded = self._add_logo_candidates(layout, _LEADING_LOGO_CANDIDATES)
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
            self._brand_btn.setStyleSheet(f"""
                QPushButton {{
                    color: {p.text_on_primary};
                    font-size: 16px;
                    font-weight: {t.weight_bold};
                    letter-spacing: 1.2px;
                    background: transparent;
                    border: none;
                    text-align: left;
                    padding: 0;
                }}
                QPushButton:hover {{ color: {p.senai_orange}; }}
            """)
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
        self._nav_divider.setStyleSheet("background: rgba(255,255,255,0.18); border: none;")
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

        if self._trailing_logo_candidates:
            layout.addSpacing(s.sm)
            self._add_trailing_logos(layout, self._trailing_logo_candidates)

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

    def _add_logo_candidates(self, layout: QHBoxLayout, candidates: Sequence[str]) -> bool:
        for candidate in candidates:
            path = _ASSETS_DIR / candidate
            if path.exists():
                pixmap = QPixmap(str(path))
                if not pixmap.isNull():
                    layout.addWidget(self._create_logo_button(path, trailing=False))
                    return True
        return False

    def _add_trailing_logos(self, layout: QHBoxLayout, candidates: Sequence[str]) -> None:
        for candidate in candidates:
            path = _ASSETS_DIR / candidate
            if not path.exists():
                continue
            pixmap = QPixmap(str(path))
            if pixmap.isNull():
                continue
            btn = self._create_logo_button(path, trailing=True)
            layout.addWidget(btn)
            self._trailing_logo_buttons.append(btn)

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
        self._settings_btn.setStyleSheet(header_help_button_style())

    def _apply_help_button_style(self) -> None:
        if self._help_btn is None:
            return
        self._help_btn.setIcon(icon_help())
        self._help_btn.setStyleSheet(header_help_button_style())

    def _apply_badge_style(self) -> None:
        self._badge_label.setStyleSheet(header_badge_style())

    def refresh_appearance(self) -> None:
        """Reaplica estilos após mudança de tema/contraste/fonte."""
        self.setStyleSheet(header_gradient_style())
        self._apply_settings_button_style()
        self._apply_help_button_style()
        self._apply_badge_style()
        for btn in self._trailing_logo_buttons:
            btn.setStyleSheet(header_logo_button_style())
        p, t = PALETTE, TYPOGRAPHY
        if self._back_link:
            self._back_link.setStyleSheet(self._nav_link_stylesheet())
        if self._forward_link:
            self._forward_link.setStyleSheet(self._nav_link_stylesheet())
        if self._nav_divider:
            self._nav_divider.setStyleSheet("background: rgba(255,255,255,0.18); border: none;")

    @staticmethod
    def _nav_link_stylesheet() -> str:
        p = PALETTE
        t = TYPOGRAPHY
        return f"""
            QPushButton {{
                color: rgba(255,255,255,0.55);
                background: transparent;
                border: none;
                font-size: 13px;
                font-weight: {t.weight_medium};
                padding: 0 4px;
            }}
            QPushButton:hover:enabled {{
                color: {p.senai_orange};
            }}
            QPushButton:disabled {{
                color: rgba(255,255,255,0.15);
            }}
        """
