"""Campos de entrada reutilizáveis, com label acoplado e estilo único."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import QLabel, QLineEdit, QVBoxLayout, QWidget

from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY


class LabeledLineEdit(QWidget):
    """Campo de texto com rótulo acima, usado nos formulários (Cliente,
    Componente Avaliado, campos de metadados de Controle Técnico etc.).
    """

    def __init__(
        self,
        label: str,
        placeholder: str = "",
        required: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._required = required
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label_text = f"{label} *" if required else label
        self._label = QLabel(label_text)
        self._label.setStyleSheet(
            f"font-size: {TYPOGRAPHY.size_caption}px; color: {PALETTE.text_secondary};"
        )

        self._field = QLineEdit()
        self._field.setPlaceholderText(placeholder)
        self._field.setMinimumHeight(36)
        self._apply_style()
        self._field.textChanged.connect(self._apply_style)

        layout.addWidget(self._label)
        layout.addWidget(self._field)

    def _apply_style(self) -> None:
        p = PALETTE
        is_invalid = self._required and not self._field.text().strip()
        border_color = p.danger if is_invalid and self._field.hasFocus() is False and self._touched() else p.border
        self._field.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {border_color};
                border-radius: {SPACING.radius_sm}px;
                padding: 6px {SPACING.sm}px;
                background-color: {p.surface};
            }}
            QLineEdit:focus {{ border: 1px solid {p.zeiss_blue}; }}
        """)

    def _touched(self) -> bool:
        """Evita marcar erro antes do usuário interagir com o campo."""
        return self._field.property("touched") is True

    def text(self) -> str:
        return self._field.text().strip()

    def set_text(self, value: str) -> None:
        self._field.setText(value)

    def is_valid(self) -> bool:
        return not self._required or bool(self.text())

    def mark_touched(self) -> None:
        self._field.setProperty("touched", True)
        self._apply_style()

    @property
    def field(self) -> QLineEdit:
        """Acesso ao QLineEdit interno para conexões de sinal específicas."""
        return self._field


class SearchBar(QLineEdit):
    """Campo de busca padrão (Dashboard, seleção de templates)."""

    def __init__(self, placeholder: str = "Buscar...", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(38)
        p = PALETTE
        self.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {p.border};
                border-radius: {SPACING.radius_lg}px;
                padding: 6px {SPACING.md}px;
                background-color: {p.surface_alt};
            }}
            QLineEdit:focus {{ border: 1px solid {p.zeiss_blue}; background-color: {p.surface}; }}
        """)
