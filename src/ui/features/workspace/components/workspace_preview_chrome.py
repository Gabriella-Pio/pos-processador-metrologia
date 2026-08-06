"""Montagem do painel de preview do workspace (cabeçalho + corpo + abas)."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QMenu, QVBoxLayout, QWidget

from src.ui.components.buttons import ChromeIconButton, PrimaryButton
from src.ui.components.inputs import LayoutTemplateSelector
from src.ui.components.feedback import InlineBanner
from src.ui.components.icons import icon_ellipsis, icon_export
from src.ui.shared.report_editor.preview_panel import PreviewPanel
from src.ui.styles import SPACING


def build_workspace_project_tabs_strip(
    project_tabs,
    add_pdf_btn,
    *,
    on_more_clicked,
    on_export_clicked,
    on_save_layout,
    on_change_layout,
) -> tuple[QWidget, QLabel, QLabel, ChromeIconButton, PrimaryButton, QMenu]:
    """Faixa superior com abas de PDF, status e ações de export."""
    row = QWidget()
    row.setObjectName("WorkspaceProjectTabsStrip")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(SPACING.md, SPACING.xs, SPACING.md, SPACING.xs)
    layout.setSpacing(SPACING.sm)
    layout.addWidget(project_tabs)
    layout.addWidget(add_pdf_btn)
    layout.addStretch(1)

    preview_status_label = QLabel("")
    preview_status_label.setObjectName("WorkspacePreviewStatus")
    layout.addWidget(preview_status_label, alignment=Qt.AlignmentFlag.AlignVCenter)

    data_dirty_label = QLabel("")
    data_dirty_label.setObjectName("WorkspaceDataDirty")
    layout.addWidget(data_dirty_label, alignment=Qt.AlignmentFlag.AlignVCenter)

    more_btn = ChromeIconButton(icon_ellipsis(), "Mais ações do projeto")
    more_btn.clicked.connect(on_more_clicked)
    layout.addWidget(more_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

    export_btn = PrimaryButton("Exportar", icon=icon_export())
    export_btn.setToolTip("Exportar PDF (Ctrl+E)")
    export_btn.clicked.connect(on_export_clicked)
    layout.addWidget(export_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

    preview_menu = QMenu(row)
    save_layout_action = preview_menu.addAction("Salvar layout…")
    save_layout_action.triggered.connect(on_save_layout)
    change_layout_action = preview_menu.addAction("Alterar layout…")
    change_layout_action.triggered.connect(on_change_layout)
    preview_menu.addSeparator()
    export_individual_action = preview_menu.addAction("Exportar PDFs individuais")
    export_individual_action.setCheckable(True)
    export_individual_action.setChecked(True)
    export_merged_action = preview_menu.addAction("Exportar um único PDF")
    export_merged_action.setCheckable(True)
    export_merged_action.setChecked(False)
    export_merged_action.setEnabled(False)
    export_merged_action.setToolTip("Em breve — mescla seções institucionais")

    row._preview_menu = preview_menu  # type: ignore[attr-defined]
    row._save_layout_action = save_layout_action  # type: ignore[attr-defined]
    row._export_individual_action = export_individual_action  # type: ignore[attr-defined]
    row._export_merged_action = export_merged_action  # type: ignore[attr-defined]
    return row, preview_status_label, data_dirty_label, more_btn, export_btn, preview_menu


def build_workspace_action_bar(
    document_title_label: QLabel,
    active_section_label: QLabel,
    template_selector: LayoutTemplateSelector,
) -> QWidget:
    """Barra de contexto acima do preview (título, seção ativa, template)."""
    action_bar = QWidget()
    action_bar.setObjectName("WorkspacePreviewContext")
    row = QHBoxLayout(action_bar)
    row.setContentsMargins(0, SPACING.xs, 0, SPACING.xs)
    row.setSpacing(SPACING.xs)
    row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

    row.addWidget(document_title_label)
    meta_sep_before_section = QLabel("·")
    meta_sep_before_section.setObjectName("WorkspaceMetaSeparator")
    row.addWidget(meta_sep_before_section)
    row.addWidget(active_section_label)
    meta_sep_before_layout = QLabel("·")
    meta_sep_before_layout.setObjectName("WorkspaceMetaSeparator")
    row.addWidget(meta_sep_before_layout)

    row.addWidget(template_selector)
    row.addStretch(1)

    action_bar._meta_sep_before_section = meta_sep_before_section  # type: ignore[attr-defined]
    action_bar._meta_sep_before_layout = meta_sep_before_layout  # type: ignore[attr-defined]
    return action_bar


def build_workspace_preview_column(
    action_bar: QWidget,
    banner: InlineBanner,
    preview_panel: PreviewPanel,
) -> QWidget:
    """Coluna direita do workspace: cabeçalho + banner + preview."""
    container = QWidget()
    container.setObjectName("WorkspacePreviewPanel")
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    header = QWidget()
    header.setObjectName("WorkspacePreviewHeader")
    header_layout = QVBoxLayout(header)
    header_layout.setContentsMargins(SPACING.lg, SPACING.sm, SPACING.lg, SPACING.sm)
    header_layout.setSpacing(0)
    header_layout.addWidget(action_bar)
    layout.addWidget(header)

    body = QWidget()
    body_layout = QVBoxLayout(body)
    body_layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.lg)
    body_layout.setSpacing(SPACING.sm)
    body_layout.addWidget(banner)
    body_layout.addWidget(preview_panel, stretch=1)
    layout.addWidget(body, stretch=1)
    return container
