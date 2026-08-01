"""
Dashboard inicial (estilo Google Docs Home): ações rápidas, grade de
templates e histórico de arquivos recentes.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.ui.components.buttons import PrimaryButton, SecondaryButton
from src.ui.components.cards import RecentFileRow, RecentFileSummary, TemplateCard, TemplateSummary
from src.ui.components.feedback import show_friendly_error
from src.ui.components.header import AppHeader
from src.ui.components.inputs import SearchBar
from src.ui.styles import PALETTE, SPACING, apply_elevation, heading_style
from src.ui.viewmodels.home_viewmodel import HomeViewModel


class HomeView(QWidget):
    """Tela inicial. Comunica intenções do usuário para fora via sinais
    (``new_document_requested``, ``template_manager_requested``,
    ``recent_file_opened``) — quem decide o que fazer com isso é o
    ``MainWindow``/coordenador de navegação, não esta view.
    """

    new_document_requested = pyqtSignal()
    template_manager_requested = pyqtSignal()
    recent_file_opened = pyqtSignal(str)  # file_id

    def __init__(self, view_model: HomeViewModel, parent=None) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._recent_files_container: QVBoxLayout | None = None
        self._templates_grid: QGridLayout | None = None
        self._build_ui()
        self._connect_view_model()
        self._vm.load_dashboard()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(AppHeader(subtitle="Relatórios de Metrologia", show_back_button=False))

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.xl)
        content_layout.setSpacing(SPACING.lg)

        content_layout.addLayout(self._build_page_toolbar())
        content_layout.addLayout(self._build_quick_actions())
        content_layout.addWidget(self._build_section_label("Templates"))
        content_layout.addWidget(self._build_templates_grid())
        content_layout.addWidget(self._build_section_label("Arquivos recentes"))
        content_layout.addWidget(self._build_recent_files_list(), stretch=1)

        outer.addWidget(content, stretch=1)

    def _build_page_toolbar(self) -> QHBoxLayout:
        row = QHBoxLayout()
        title = QLabel("Meus relatórios")
        title.setStyleSheet(heading_style(1))
        search = SearchBar("Buscar arquivos ou templates...")
        search.setFixedWidth(320)
        row.addWidget(title)
        row.addStretch(1)
        row.addWidget(search)
        return row

    def _build_quick_actions(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(SPACING.md)

        new_pdf_btn = PrimaryButton("＋  Novo PDF / Processar Lote")
        new_pdf_btn.clicked.connect(self.new_document_requested.emit)

        new_template_btn = SecondaryButton("Criar Novo Template")
        new_template_btn.clicked.connect(self.template_manager_requested.emit)

        row.addWidget(new_pdf_btn)
        row.addWidget(new_template_btn)
        row.addStretch(1)
        return row

    def _build_section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(heading_style(3))
        return label

    def _build_templates_grid(self) -> QWidget:
        container = QFrame()
        self._templates_grid = QGridLayout(container)
        self._templates_grid.setSpacing(SPACING.md)
        self._templates_grid.setContentsMargins(0, 0, 0, 0)
        return container

    def _build_recent_files_list(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        self._recent_files_container = QVBoxLayout(content)
        self._recent_files_container.setContentsMargins(0, 0, 0, 0)
        self._recent_files_container.setSpacing(0)
        self._recent_files_container.addStretch(1)

        scroll.setWidget(content)
        return scroll

    # ------------------------------------------------------- ViewModel glue
    def _connect_view_model(self) -> None:
        self._vm.templates_loaded.connect(self._render_templates)
        self._vm.recent_files_loaded.connect(self._render_recent_files)
        self._vm.error_occurred.connect(
            lambda title, msg, details: show_friendly_error(self, title, msg, details)
        )

    def _render_templates(self, templates: list[TemplateSummary]) -> None:
        assert self._templates_grid is not None
        columns = 4
        for index, summary in enumerate(templates):
            card = TemplateCard(summary)
            apply_elevation(card, blur=16, y_offset=2, alpha=30)
            card.selected.connect(self.template_manager_requested.emit)
            self._templates_grid.addWidget(card, index // columns, index % columns)

    def _render_recent_files(self, files: list[RecentFileSummary]) -> None:
        assert self._recent_files_container is not None
        # Remove placeholder stretch, insere linhas, reinsere o stretch.
        while self._recent_files_container.count():
            self._recent_files_container.takeAt(0)
        for summary in files:
            row = RecentFileRow(summary)
            row.opened.connect(self.recent_file_opened.emit)
            self._recent_files_container.addWidget(row)
        self._recent_files_container.addStretch(1)