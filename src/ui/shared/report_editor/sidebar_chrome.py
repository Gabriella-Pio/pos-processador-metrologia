"""Cabeçalho e estilo comuns das abas da sidebar (Sumário, Dados, Histórico)."""
from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.ui.styles import SPACING


def sidebar_section_header(title: str) -> QWidget:
    """Cabeçalho uppercase + divisor — mesmo visual da aba Histórico."""
    container = QWidget()
    container.setObjectName("SidebarTabHeader")
    layout = QVBoxLayout(container)
    layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.sm)
    layout.setSpacing(6)

    label = QLabel(title.upper())
    label.setObjectName("SidebarSectionTitle")
    layout.addWidget(label)

    divider = QFrame()
    divider.setObjectName("SidebarDivider")
    divider.setFrameShape(QFrame.Shape.HLine)
    divider.setFixedHeight(1)
    layout.addWidget(divider)

    return container


def editor_panel_header(title: str = "") -> tuple[QWidget, QLabel, QWidget]:
    """Cabeçalho do painel central de edição — título + host de ações à direita."""
    container = QWidget()
    container.setObjectName("EditorPanelHeader")
    outer = QHBoxLayout(container)
    outer.setContentsMargins(SPACING.md, SPACING.sm, SPACING.sm, 0)
    outer.setSpacing(SPACING.xs)

    title_block = QWidget()
    title_layout = QVBoxLayout(title_block)
    title_layout.setContentsMargins(0, SPACING.xs, 0, SPACING.sm)
    title_layout.setSpacing(6)

    label = QLabel(title.upper() if title else "EDITAR SEÇÃO")
    label.setObjectName("SidebarSectionTitle")
    label.setWordWrap(True)
    title_layout.addWidget(label)

    divider = QFrame()
    divider.setObjectName("SidebarDivider")
    divider.setFrameShape(QFrame.Shape.HLine)
    divider.setFixedHeight(1)
    title_layout.addWidget(divider)

    outer.addWidget(title_block, stretch=1)

    actions_host = QWidget()
    actions_host.setObjectName("EditorPanelHeaderActions")
    actions_layout = QHBoxLayout(actions_host)
    actions_layout.setContentsMargins(0, 0, SPACING.xs, SPACING.sm)
    actions_layout.setSpacing(SPACING.xs)
    outer.addWidget(actions_host)

    return container, label, actions_host
