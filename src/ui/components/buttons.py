"""
Botões reutilizáveis do Design System.

Cada classe representa uma "intenção" de ação (primária, secundária,
perigo, ícone) — a view nunca estiliza um QPushButton manualmente,
apenas escolhe qual componente semântico usar. Isso é o padrão
Strategy aplicado à apresentação: a variação de estilo é encapsulada
em cada subclasse, e a view depende apenas da interface comum de
QPushButton.
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QIcon
from PyQt6.QtWidgets import QPushButton

from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY


class _BaseButton(QPushButton):
    """Base comum: cursor de mão, altura mínima e fonte consistente."""

    def __init__(self, text: str = "", icon: Optional[QIcon] = None, parent=None) -> None:
        super().__init__(text, parent)
        if icon is not None:
            self.setIcon(icon)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setMinimumHeight(38)
        self.setFont_ = None  # placeholder para futura customização de fonte


class PrimaryButton(_BaseButton):
    """Ação principal de destaque (ex.: 'Exportar PDF Enriquecido')."""

    def __init__(self, text: str = "", icon: Optional[QIcon] = None, parent=None) -> None:
        super().__init__(text, icon, parent)
        p = PALETTE
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {p.senai_red};
                color: {p.text_on_primary};
                border: none;
                border-radius: {SPACING.radius_md}px;
                padding: 8px {SPACING.lg}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            }}
            QPushButton:hover {{ background-color: {p.senai_red_hover}; }}
            QPushButton:disabled {{ background-color: {p.text_disabled}; }}
        """)


class SecondaryButton(_BaseButton):
    """Ação secundária (ex.: 'Cancelar', 'Criar Novo Template')."""

    def __init__(self, text: str = "", icon: Optional[QIcon] = None, parent=None) -> None:
        super().__init__(text, icon, parent)
        p = PALETTE
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {p.surface};
                color: {p.zeiss_blue};
                border: 1px solid {p.border_strong};
                border-radius: {SPACING.radius_md}px;
                padding: 8px {SPACING.lg}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            }}
            QPushButton:hover {{ background-color: {p.surface_alt}; border-color: {p.zeiss_blue}; }}
        """)


class DangerButton(_BaseButton):
    """Ação destrutiva (ex.: 'Excluir template', 'Remover imagem')."""

    def __init__(self, text: str = "", icon: Optional[QIcon] = None, parent=None) -> None:
        super().__init__(text, icon, parent)
        p = PALETTE
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {p.danger_bg};
                color: {p.danger};
                border: 1px solid {p.danger_bg};
                border-radius: {SPACING.radius_md}px;
                padding: 8px {SPACING.lg}px;
                font-weight: {TYPOGRAPHY.weight_medium};
            }}
            QPushButton:hover {{ background-color: {p.danger}; color: {p.text_on_primary}; }}
        """)


class IconButton(_BaseButton):
    """Botão compacto apenas com ícone (toolbar de anotação, ações de card)."""

    def __init__(self, icon: QIcon, tooltip: str = "", parent=None) -> None:
        super().__init__("", icon, parent)
        p = PALETTE
        self.setFixedSize(36, 36)
        if tooltip:
            self.setToolTip(tooltip)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: {SPACING.radius_sm}px;
            }}
            QPushButton:hover {{ background-color: {p.surface_sidebar}; }}
            QPushButton:checked {{ background-color: {p.info_bg}; }}
        """)
