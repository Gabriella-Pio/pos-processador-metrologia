"""
Header institucional reutilizável — aparece no topo tanto do Dashboard
quanto do Workspace, dando identidade visual consistente (faixa em
gradiente vermelho SENAI + borda azul ZEISS) em vez de cada tela ter
sua própria barra branca genérica.
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, header_gradient_style


class AppHeader(QWidget):
    """Faixa superior institucional.

    ``show_back_button=True`` exibe uma seta de voltar à esquerda
    (usada no Workspace, para retornar ao Dashboard) — o Dashboard em
    si não tem pra onde voltar, então fica sem o botão.
    """

    back_requested = pyqtSignal()

    def __init__(
        self,
        subtitle: str = "Centro de Excelência em Metrologia",
        show_back_button: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("AppHeader")
        self.setStyleSheet(header_gradient_style())
        self.setFixedHeight(SPACING.header_height)

        self._title_label = QLabel()
        self._build_ui(subtitle, show_back_button)

    def _build_ui(self, subtitle: str, show_back_button: bool) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, 0, SPACING.lg, 0)
        layout.setSpacing(SPACING.md)

        if show_back_button:
            back_btn = QPushButton("←  Voltar")
            back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            back_btn.setStyleSheet(f"""
                QPushButton {{
                    color: {PALETTE.text_on_primary};
                    background-color: rgba(255, 255, 255, 0.14);
                    border: 1px solid rgba(255, 255, 255, 0.35);
                    border-radius: {SPACING.radius_md}px;
                    padding: 6px {SPACING.md}px;
                    font-weight: {TYPOGRAPHY.weight_medium};
                }}
                QPushButton:hover {{ background-color: rgba(255, 255, 255, 0.24); }}
            """)
            back_btn.clicked.connect(self.back_requested.emit)
            layout.addWidget(back_btn)

        text_container = QVBoxLayout()
        text_container.setSpacing(0)

        brand_label = QLabel("SENAI  ×  ZEISS")
        brand_label.setStyleSheet(
            f"color: {PALETTE.text_on_primary}; font-size: {TYPOGRAPHY.size_h2}px; "
            f"font-weight: {TYPOGRAPHY.weight_bold}; letter-spacing: 1px;"
        )
        self._title_label.setText(subtitle)
        self._title_label.setStyleSheet(
            f"color: rgba(255,255,255,0.85); font-size: {TYPOGRAPHY.size_caption}px;"
        )

        text_container.addWidget(brand_label)
        text_container.addWidget(self._title_label)
        layout.addLayout(text_container)
        layout.addStretch(1)

    def set_subtitle(self, text: str) -> None:
        """Permite trocar o texto secundário (ex.: nome do relatório em edição)."""
        self._title_label.setText(text)