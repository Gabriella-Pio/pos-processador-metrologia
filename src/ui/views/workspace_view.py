"""
Workspace principal: layout profissional de 3 colunas para
edição/preview do relatório enriquecido.

    Sidebar Esquerda | Área Central (Preview)     | Sidebar Direita
    (Bookmarks)      | (documento renderizado)    | (Imagens, Anotações,
                      |                            |  Histórico de versões)

Toda a orquestração de dados passa pelo ``WorkspaceViewModel`` — esta
view apenas monta widgets, conecta sinais e reage a mudanças de estado
via ``AppState`` (Observer), sem chamar parser/exportador diretamente.
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QFrame,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from src.core.ports import ReportDocument
from src.ui.components.buttons import PrimaryButton, SecondaryButton
from src.ui.components.feedback import InlineBanner, FeedbackLevel, show_friendly_error, show_info
from src.ui.components.panels import (
    AnnotationToolbar,
    BookmarksPanel,
    ImageManagerPanel,
    VersionHistoryPanel,
)
from src.ui.styles import PALETTE, SPACING, heading_style
from src.ui.viewmodels.app_state import AppState
from src.ui.viewmodels.workspace_viewmodel import WorkspaceViewModel


class WorkspaceView(QWidget):
    """Tela de trabalho principal do operador de metrologia."""

    def __init__(self, app_state: AppState, view_model: WorkspaceViewModel, parent=None) -> None:
        super().__init__(parent)
        self._app_state = app_state
        self._vm = view_model
        self._active_section_id: str | None = None

        self._bookmarks_panel = BookmarksPanel()
        self._image_panel = ImageManagerPanel()
        self._annotation_toolbar = AnnotationToolbar()
        self._version_panel = VersionHistoryPanel()
        self._preview_scroll_area = QScrollArea()
        self._preview_pages_widget = QWidget()
        self._preview_pages_layout = QVBoxLayout(self._preview_pages_widget)
        self._document_title_label = QLabel("Nenhum documento carregado")

        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_top_action_bar())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_left_sidebar())
        splitter.addWidget(self._build_center_area())
        splitter.addWidget(self._build_right_sidebar())
        splitter.setSizes([220, 640, 320])
        outer.addWidget(splitter, stretch=1)

    def _build_top_action_bar(self) -> QWidget:
        bar = QWidget()
        bar.setStyleSheet(f"background-color: {PALETTE.surface}; border-bottom: 1px solid {PALETTE.border};")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(SPACING.lg, SPACING.sm, SPACING.lg, SPACING.sm)

        self._document_title_label.setStyleSheet(heading_style(2))
        layout.addWidget(self._document_title_label)
        layout.addStretch(1)

        new_version_btn = SecondaryButton("Registrar nova versão")
        new_version_btn.clicked.connect(self._on_register_version)

        export_btn = PrimaryButton("Exportar PDF Enriquecido")
        export_btn.clicked.connect(self._on_export_clicked)

        layout.addWidget(new_version_btn)
        layout.addWidget(export_btn)
        return bar

    def _build_left_sidebar(self) -> QWidget:
        self._bookmarks_panel.section_selected.connect(self._on_section_selected)
        return self._bookmarks_panel

    def _build_center_area(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        layout.setSpacing(SPACING.md)

        self._banner = InlineBanner(
            "Pré-visualização do relatório enriquecido. O que aparece aqui é a versão renderizada do PDF final.",
            level=FeedbackLevel.INFO,
        )

        self._preview_scroll_area.setWidgetResizable(True)
        self._preview_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._preview_scroll_area.setWidget(self._preview_pages_widget)
        self._preview_pages_layout.setContentsMargins(0, 0, 0, 0)
        self._preview_pages_layout.setSpacing(SPACING.lg)
        self._preview_pages_widget.setStyleSheet("background: transparent;")

        layout.addWidget(self._banner)
        layout.addWidget(self._preview_scroll_area, stretch=1)
        return container

    def _build_right_sidebar(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet(f"background-color: {PALETTE.surface_sidebar};")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._image_panel.image_dropped.connect(self._on_image_dropped)
        layout.addWidget(self._image_panel, stretch=2)
        layout.addWidget(self._annotation_toolbar)

        separator = QLabel()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {PALETTE.border};")
        layout.addWidget(separator)

        layout.addWidget(self._version_panel, stretch=1)
        return container

    # ------------------------------------------------------- ViewModel glue
    def _connect_signals(self) -> None:
        self._app_state.document_changed.connect(self._on_document_changed)
        self._app_state.images_changed.connect(self._refresh_images)
        self._app_state.version_added.connect(self._refresh_versions)
        self._vm.sections_summary_ready.connect(self._bookmarks_panel.render_sections)
        self._vm.preview_ready.connect(self._render_preview_pages)

        self._vm.error_occurred.connect(
            lambda title, msg, details: show_friendly_error(self, title, msg, details)
        )
        self._vm.export_finished.connect(self._on_export_finished)

    def _on_document_changed(self, document: ReportDocument | None) -> None:
        if document is None:
            self._document_title_label.setText("Nenhum documento carregado")
            self._clear_preview_pages()
            return
        self._document_title_label.setText(
            f"{document.client_project} — {document.evaluated_component}"
        )
        self._refresh_images()
        self._refresh_versions()

    def _on_section_selected(self, section_id: str) -> None:
        self._active_section_id = section_id

    def _on_image_dropped(self, image_path: Path) -> None:
        if self._active_section_id is None:
            show_friendly_error(
                self,
                "Selecione uma seção primeiro",
                "Escolha uma seção no sumário à esquerda antes de associar uma fotografia.",
            )
            return
        self._vm.add_image_to_section(image_path, self._active_section_id)

    def _refresh_images(self) -> None:
        document = self._app_state.active_document
        if document is not None:
            self._image_panel.render_images(document.images)

    def _refresh_versions(self) -> None:
        document = self._app_state.active_document
        if document is not None:
            self._version_panel.render_history(document.version_history)

    def _render_preview_pages(self, pages_png: list[bytes]) -> None:
        self._clear_preview_pages()

        if not pages_png:
            empty_label = QLabel("Nenhuma página disponível para preview.")
            empty_label.setStyleSheet(f"color: {PALETTE.text_secondary}; padding: {SPACING.lg}px;")
            self._preview_pages_layout.addWidget(empty_label)
            self._preview_pages_layout.addStretch(1)
            return

        for index, page_png in enumerate(pages_png, start=1):
            page_container = QWidget()
            page_layout = QVBoxLayout(page_container)
            page_layout.setContentsMargins(0, 0, 0, 0)
            page_layout.setSpacing(SPACING.sm)

            page_label = QLabel(f"Página {index}")
            page_label.setStyleSheet(f"font-weight: 600; color: {PALETTE.text_secondary};")

            image_label = QLabel()
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image_label.setStyleSheet(
                f"background-color: {PALETTE.surface}; border: 1px solid {PALETTE.border}; border-radius: {SPACING.radius_md}px; padding: {SPACING.sm}px;"
            )

            pixmap = QPixmap()
            pixmap.loadFromData(page_png)
            image_label.setPixmap(pixmap)

            page_layout.addWidget(page_label)
            page_layout.addWidget(image_label)
            self._preview_pages_layout.addWidget(page_container)

        self._preview_pages_layout.addStretch(1)

    def _clear_preview_pages(self) -> None:
        while self._preview_pages_layout.count():
            item = self._preview_pages_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _on_register_version(self) -> None:
        # Em produção, abriria um pequeno modal pedindo responsável/descrição;
        # aqui a chamada ao ViewModel já demonstra o fluxo de dados.
        self._vm.register_new_version(responsible_name="Operador atual", description="Atualização manual")

    def _on_export_clicked(self) -> None:
        output_path, _ = QFileDialog.getSaveFileName(self, "Exportar PDF Enriquecido", "", "PDF (*.pdf)")
        if not output_path:
            return
        self._vm.export_document(Path(output_path))

    def _on_export_finished(self, final_path: Path) -> None:
        show_info(self, "Exportação concluída", f"O relatório foi salvo em:\n{final_path}")
