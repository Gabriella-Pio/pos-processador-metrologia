"""Layout compartilhado do editor de relatório (3 colunas + stack de edição)."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QSplitter, QStackedWidget, QVBoxLayout, QWidget

DEFAULT_SPLITTER_SIZES = (240, 320, 800)

#: Proporções das três colunas com o formulário de seção aberto / apenas preview.
EDITING_RATIOS = (0.18, 0.24, 0.58)
PREVIEW_ONLY_RATIOS = (0.18, 0.0, 0.82)

_MIN_SIDEBAR = 200
_MIN_EDITOR = 280
_MIN_PREVIEW = 320


def splitter_sizes(total_width: int, ratios: tuple[float, float, float]) -> list[int]:
    """Converte proporções na largura real do splitter, respeitando mínimos por coluna.

    Tamanhos absolutos quebram quando a escala do Windows encolhe a área lógica:
    somar colunas pensadas para 1360 px numa janela de 1280 px espreme o preview.
    """
    total = total_width if total_width > 0 else sum(DEFAULT_SPLITTER_SIZES)
    sidebar = max(_MIN_SIDEBAR, round(total * ratios[0]))
    editor = max(_MIN_EDITOR, round(total * ratios[1])) if ratios[1] > 0 else 0
    preview = total - sidebar - editor
    if preview < _MIN_PREVIEW:
        deficit = _MIN_PREVIEW - preview
        editor = max(0, editor - deficit)
        preview = total - sidebar - editor
    return [sidebar, editor, max(0, preview)]


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
