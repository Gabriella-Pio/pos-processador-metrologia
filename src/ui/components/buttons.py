"""
Botões reutilizáveis do Design System — Dark Edition.

Hierarquia visual clara:
  PrimaryButton  → ação principal (laranja SENAI, destaque máximo)
  SecondaryButton → ação secundária (outline azul SENAI)
  GhostButton    → ação terciária (sem background, apenas texto)
  DangerButton   → ação destrutiva (vermelho suave)
  IconButton     → compacto de ícone (toolbars)
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QIcon
from PyQt6.QtWidgets import QPushButton

from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY
from src.ui.styles.helpers import primary_button_style, secondary_button_style


class _BaseButton(QPushButton):
    """Base comum: cursor de mão, altura mínima e fonte consistente."""

    def __init__(self, text: str = "", icon: Optional[QIcon] = None, parent=None) -> None:
        super().__init__(text, parent)
        if icon is not None:
            self.setIcon(icon)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(36)

    def refresh_appearance(self) -> None:
        """Reaplicado por subclasses após mudança de tema."""


class PrimaryButton(_BaseButton):
    """Ação principal — laranja SENAI com profundidade 3-D sutil."""

    def __init__(self, text: str = "", icon: Optional[QIcon] = None, parent=None) -> None:
        super().__init__(text, icon, parent)
        self.refresh_appearance()

    def refresh_appearance(self) -> None:
        self.setStyleSheet(primary_button_style())


class SecondaryButton(_BaseButton):
    """Ação secundária — outline azul SENAI sobre dark."""

    def __init__(self, text: str = "", icon: Optional[QIcon] = None, parent=None) -> None:
        super().__init__(text, icon, parent)
        self.refresh_appearance()

    def refresh_appearance(self) -> None:
        self.setStyleSheet(secondary_button_style())


class GhostButton(_BaseButton):
    """Ação terciária — sem fundo, apenas texto com underline no hover."""

    def __init__(self, text: str = "", icon: Optional[QIcon] = None, parent=None) -> None:
        super().__init__(text, icon, parent)
        self.refresh_appearance()

    def refresh_appearance(self) -> None:
        p = PALETTE
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {p.text_secondary};
                border: none;
                border-radius: {SPACING.radius_sm}px;
                padding: 7px {SPACING.md}px;
                font-weight: {TYPOGRAPHY.weight_regular};
                font-size: {TYPOGRAPHY.size_body}px;
            }}
            QPushButton:hover {{
                color: {p.text_primary};
                background-color: {p.bg_surface_alt};
            }}
            QPushButton:pressed {{
                color: {p.text_secondary};
            }}
        """)


class DangerButton(_BaseButton):
    """Ação destrutiva — vermelho de alerta."""

    def __init__(self, text: str = "", icon: Optional[QIcon] = None, parent=None) -> None:
        super().__init__(text, icon, parent)
        self.refresh_appearance()

    def refresh_appearance(self) -> None:
        p = PALETTE
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {p.danger_bg};
                color: {p.danger};
                border: 1px solid rgba(248, 81, 73, 0.35);
                border-radius: {SPACING.radius_md}px;
                padding: 7px {SPACING.lg}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            }}
            QPushButton:hover {{
                background-color: {p.danger};
                color: {p.text_on_primary};
                border-color: {p.danger};
            }}
            QPushButton:pressed {{
                background-color: #c73e38;
            }}
        """)


class IconButton(_BaseButton):
    """Botão compacto de ícone para toolbars e ações de card."""

    def __init__(self, icon: QIcon, tooltip: str = "", parent=None) -> None:
        super().__init__("", icon, parent)
        self.setFixedSize(34, 34)
        if tooltip:
            self.setToolTip(tooltip)
        self.refresh_appearance()

    def refresh_appearance(self) -> None:
        p = PALETTE
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: {SPACING.radius_sm}px;
            }}
            QPushButton:hover {{
                background-color: {p.bg_surface_alt};
                border: 1px solid {p.border};
            }}
            QPushButton:checked {{
                background-color: rgba(74, 111, 212, 0.20);
                border: 1px solid {p.senai_blue};
            }}
        """)
