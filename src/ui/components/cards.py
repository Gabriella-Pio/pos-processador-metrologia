"""
Cards reutilizáveis para o Dashboard (grade de templates e lista de
arquivos recentes), no espírito visual do Google Docs/Drive.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, caption_style


@dataclass(frozen=True)
class TemplateSummary:
    """DTO simples para exibição de um template na grade (sem lógica)."""

    template_id: str
    name: str
    is_default: bool = False


@dataclass(frozen=True)
class RecentFileSummary:
    """DTO simples para exibição de um arquivo recente (sem lógica)."""

    file_id: str
    file_name: str
    client_project: str
    version: str
    updated_at: datetime


class TemplateCard(QFrame):
    """Card clicável representando um template na grade do Dashboard.

    Emite ``selected`` com o ``template_id`` ao ser clicado — a view
    conecta esse sinal ao ViewModel, sem conter lógica de negócio aqui.
    """

    selected = pyqtSignal(str)

    def __init__(self, summary: TemplateSummary, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._summary = summary
        self._build_ui()

    def _build_ui(self) -> None:
        p = PALETTE
        self.setFixedSize(180, 130)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {p.surface};
                border: 1px solid {p.border};
                border-radius: {SPACING.radius_md}px;
            }}
            QFrame:hover {{ border-color: {p.zeiss_blue}; }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)

        thumb = QLabel("📄")
        thumb.setStyleSheet(f"font-size: 32px; color: {p.zeiss_blue};")
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_label = QLabel(self._summary.name)
        name_label.setWordWrap(True)
        name_label.setStyleSheet(f"font-weight: {TYPOGRAPHY.weight_medium};")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(thumb, stretch=1)
        layout.addWidget(name_label)

        if self._summary.is_default:
            badge = QLabel("Padrão SENAI/ZEISS")
            badge.setStyleSheet(caption_style())
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(badge)

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        self.selected.emit(self._summary.template_id)
        super().mousePressEvent(event)


class RecentFileRow(QFrame):
    """Linha de tabela/cartão para um arquivo recente no Dashboard."""

    opened = pyqtSignal(str)

    def __init__(self, summary: RecentFileSummary, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._summary = summary
        self._build_ui()

    def _build_ui(self) -> None:
        p = PALETTE
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame {{ background-color: transparent; border-bottom: 1px solid {p.border}; }}
            QFrame:hover {{ background-color: {p.surface_alt}; }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)

        icon = QLabel("📄")
        name = QLabel(self._summary.file_name)
        name.setMinimumWidth(220)

        client = QLabel(self._summary.client_project)
        client.setStyleSheet(caption_style())

        version = QLabel(f"v{self._summary.version}")
        version.setStyleSheet(caption_style())

        updated = QLabel(self._summary.updated_at.strftime("%d/%m/%Y %H:%M"))
        updated.setStyleSheet(caption_style())

        for widget in (icon, name, client, version, updated):
            layout.addWidget(widget)
        layout.addStretch(1)

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        self.opened.emit(self._summary.file_id)
        super().mousePressEvent(event)
