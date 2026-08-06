"""Layout compartilhado do editor de relatório (3 colunas + stack de edição)."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QSplitter, QStackedWidget, QVBoxLayout, QWidget

DEFAULT_SPLITTER_SIZES = (240, 320, 800)


def create_three_column_splitter(
    sidebar: QWidget,
    editor_column: QWidget,
    preview_column: QWidget,
    *,
    sizes: tuple[int, int, int] = DEFAULT_SPLITTER_SIZES,
) -> QSplitter:
    """Sidebar | coluna de edição | preview."""
    splitter = QSplitter(Qt.Orientation.Horizontal)
    splitter.addWidget(sidebar)
    splitter.addWidget(editor_column)
    splitter.addWidget(preview_column)
    splitter.setSizes(list(sizes))
    splitter.setStretchFactor(0, 1)
    splitter.setStretchFactor(1, 2)
    splitter.setStretchFactor(2, 3)
    return splitter


def build_editor_stack(
    placeholder: QWidget,
    edit_view: QWidget,
) -> tuple[QWidget, QStackedWidget]:
    """Coluna central com placeholder e formulário de seção empilhados."""
    container = QWidget()
    container.setObjectName("WorkspaceEditorColumn")
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    stack = QStackedWidget()
    stack.setObjectName("WorkspaceEditorStack")
    stack.addWidget(placeholder)
    stack.addWidget(edit_view)
    layout.addWidget(stack)
    return container, stack


def build_editor_column(
    placeholder: QWidget,
    edit_view: QWidget,
    *,
    header: QWidget | None = None,
) -> tuple[QWidget, QStackedWidget]:
    """Coluna de edição com cabeçalho opcional (ex.: título da seção ativa no template)."""
    inner, stack = build_editor_stack(placeholder, edit_view)
    if header is None:
        return inner, stack
    container = QWidget()
    container.setObjectName("WorkspaceEditorColumn")
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    layout.addWidget(header)
    layout.addWidget(inner, stretch=1)
    return container, stack


def build_preview_column(
    preview_panel: QWidget,
    header: QWidget | None = None,
    *,
    body_widgets: list[QWidget] | None = None,
) -> QWidget:
    """Coluna direita: cabeçalho opcional + corpo (banner, preview, etc.)."""
    from src.ui.styles import SPACING

    container = QWidget()
    container.setObjectName("WorkspacePreviewPanel")
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    if header is not None:
        layout.addWidget(header)

    body = QWidget()
    body_layout = QVBoxLayout(body)
    body_layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.lg)
    body_layout.setSpacing(SPACING.sm)
    for widget in body_widgets or []:
        body_layout.addWidget(widget)
    body_layout.addWidget(preview_panel, stretch=1)
    layout.addWidget(body, stretch=1)
    return container
