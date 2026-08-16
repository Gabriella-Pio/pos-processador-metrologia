"""
Workspace — editor à esquerda, preview à direita, abas por PDF do projeto.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCursor, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QLabel,
    QLineEdit,
    QPushButton,
    QTabBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)

from src.ui.components.inputs import LayoutTemplateSelector
from src.ui.components.icons import icon_edit, icon_plus
from src.ui.components.feedback import (
    FeedbackLevel,
    InlineBanner,
)
from src.ui.controllers.app_state import AppState
from src.ui.features.workspace.viewmodels.workspace_viewmodel import WorkspaceViewModel
from src.ui.features.workspace.components.section_editor_panel import SectionEditorPanel
from src.ui.features.workspace.components.workspace_export_flow import (
    apply_export_validation_banner,
    run_workspace_export,
)
from src.ui.features.workspace.components.workspace_media_flow import WorkspaceMediaFlowMixin
from src.ui.features.workspace.components.workspace_preview_chrome import (
    build_workspace_action_bar,
    build_workspace_preview_column,
    build_workspace_project_tabs_strip,
    sync_export_mode_menu_icons,
)
from src.ui.features.workspace.components.workspace_preview_sync import WorkspacePreviewSyncMixin
from src.ui.features.workspace.components.workspace_project_tabs import WorkspaceProjectTabsMixin
from src.ui.features.workspace.components.workspace_tab_labels import document_header_label
from src.ui.features.workspace.components.workspace_template_flow import WorkspaceTemplateFlowMixin
from src.ui.features.workspace.components.workspace_version_flow import WorkspaceVersionFlowMixin
from src.ui.shared.report_editor.editor_shell import build_editor_stack, create_three_column_splitter
from src.ui.shared.report_editor.preview_panel import PreviewPanel


class WorkspaceView(
    WorkspaceProjectTabsMixin,
    WorkspaceTemplateFlowMixin,
    WorkspaceMediaFlowMixin,
    WorkspacePreviewSyncMixin,
    WorkspaceVersionFlowMixin,
    QWidget,
):

    def __init__(self, app_state: AppState, view_model: WorkspaceViewModel, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("WorkspaceSurface")
        self._app_state = app_state
        self._vm = view_model
        self._active_section_id: str | None = None
        self._active_annotation_tool: str | None = None
        self._active_annotation_image = None
        self._section_anchor_map: dict[str, dict] = {}

        self._project_tabs = QTabBar()
        self._project_tabs.setObjectName("WorkspaceProjectTabs")
        self._project_tabs.setExpanding(True)
        self._project_tabs.setDocumentMode(True)
        self._project_tabs.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self._project_tabs.setMinimumHeight(30)
        self._project_tabs.currentChanged.connect(self._on_project_tab_changed)

        self._add_pdf_btn = QPushButton("Adicionar PDF")
        self._add_pdf_btn.setObjectName("WorkspaceAddPdfTab")
        self._add_pdf_btn.setIcon(icon_plus())
        self._add_pdf_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._add_pdf_btn.setToolTip("Incluir mais relatórios ZEISS no projeto")
        self._add_pdf_btn.clicked.connect(self._on_add_pdf_clicked)

        self._project_title_edit = QLineEdit()
        self._project_title_edit.setObjectName("WorkspaceProjectTitle")
        self._project_title_edit.setPlaceholderText("Título do projeto")
        self._project_title_edit.setToolTip("Nome exibido na Home — editável a qualquer momento")
        self._project_title_edit.editingFinished.connect(self._on_project_title_edited)
        self._project_title_edit.textChanged.connect(self._sync_project_title_width)
        self._project_title_block = False

        self._project_title_edit_btn = QToolButton()
        self._project_title_edit_btn.setObjectName("WorkspaceProjectTitleEditBtn")
        self._project_title_edit_btn.setAutoRaise(True)
        self._project_title_edit_btn.setIcon(icon_edit())
        self._project_title_edit_btn.setToolTip("Editar nome do projeto")
        self._project_title_edit_btn.setFixedSize(32, 32)
        self._project_title_edit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._project_title_edit_btn.clicked.connect(self._focus_project_title)

        self._document_title_label = QLabel("Nenhum documento carregado")
        self._document_title_label.setObjectName("WorkspaceDocTitleCompact")
        self._active_section_label = QLabel("")
        self._active_section_label.setObjectName("WorkspaceActiveSection")
        self._section_editor = SectionEditorPanel()
        self._preview_panel = PreviewPanel()
        self._banner = InlineBanner("", level=FeedbackLevel.INFO)
        self._banner.sync_visibility()

        self._build_ui()
        self._section_editor.bind_view_model(self._vm)
        self._connect_signals()
        self._setup_shortcuts()
        self._update_export_options_visibility()
        self._sync_project_title_width()


    def refresh_appearance(self) -> None:
        self._banner.refresh_appearance()
        if hasattr(self, "_export_btn"):
            self._export_btn.refresh_appearance()
        if hasattr(self, "_more_btn"):
            self._more_btn.refresh_appearance()
        self._section_editor.refresh_appearance()
        self._preview_panel.refresh_appearance()
        if hasattr(self, "_export_individual_action") and hasattr(self, "_export_merged_action"):
            sync_export_mode_menu_icons(
                self._export_individual_action,
                self._export_merged_action,
            )


    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        (
            self._project_tabs_strip,
            self._preview_status,
            self._data_dirty_label,
            self._more_btn,
            self._export_btn,
            self._preview_menu,
        ) = build_workspace_project_tabs_strip(
            self._project_tabs,
            self._add_pdf_btn,
            project_title_edit=self._project_title_edit,
            project_title_edit_btn=self._project_title_edit_btn,
            on_more_clicked=self._show_preview_menu,
            on_export_clicked=self._on_export_clicked,
            on_save_layout=self._on_save_template_clicked,
            on_change_layout=self._focus_template_combo,
        )
        self._save_layout_action = self._project_tabs_strip._save_layout_action
        self._export_individual_action = self._project_tabs_strip._export_individual_action
        self._export_merged_action = self._project_tabs_strip._export_merged_action
        self._export_individual_action.toggled.connect(self._on_export_mode_toggled)
        self._export_merged_action.toggled.connect(self._on_export_mode_toggled)
        outer.addWidget(self._project_tabs_strip)

        self._edit_placeholder = QLabel(
            "Selecione uma seção no sumário.\n"
            "Duplo-clique ou use o ícone de edição para abrir o formulário."
        )
        self._edit_placeholder.setObjectName("WorkspaceEditorPlaceholder")
        self._edit_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._edit_placeholder.setWordWrap(True)

        self._edit_container, self._edit_stack = build_editor_stack(
            self._edit_placeholder,
            self._section_editor.edit_view,
        )
        self._edit_container.setObjectName("WorkspaceEditorPanel")
        self._edit_container.setVisible(False)

        self._template_selector = LayoutTemplateSelector()
        self._template_combo = self._template_selector.combo
        self._template_combo.currentIndexChanged.connect(self._on_template_changed)
        self._action_bar = build_workspace_action_bar(
            self._document_title_label,
            self._active_section_label,
            self._template_selector,
        )
        self._meta_sep_before_section = self._action_bar._meta_sep_before_section
        self._meta_sep_before_layout = self._action_bar._meta_sep_before_layout

        splitter = create_three_column_splitter(
            self._section_editor,
            self._edit_container,
            build_workspace_preview_column(self._action_bar, self._banner, self._preview_panel),
        )
        self._main_splitter = splitter
        outer.addWidget(splitter, stretch=1)


    def _connect_signals(self) -> None:
        self._app_state.document_changed.connect(self._on_document_changed)
        self._app_state.project_changed.connect(self._on_project_changed)
        self._app_state.images_changed.connect(self._refresh_images)
        self._app_state.version_added.connect(self._refresh_versions)

        self._section_editor.section_selected.connect(self._on_section_selected)
        self._section_editor.edit_visibility_changed.connect(self._on_edit_visibility_changed)
        self._section_editor.section_delete_requested.connect(self._on_section_delete)
        self._section_editor.add_custom_section_requested.connect(self._on_add_custom_section)
        self._section_editor.sections_reordered.connect(self._vm.reorder_sections)
        self._section_editor.new_version_requested.connect(self._on_register_version)
        self._section_editor.version_preview_requested.connect(self._on_preview_version)
        self._section_editor.version_restore_requested.connect(self._on_restore_version)
        self._section_editor.version_export_requested.connect(self._on_export_version)
        self._section_editor.image_dropped.connect(self._on_image_dropped)
        self._section_editor.image_remove_requested.connect(self._on_image_remove)
        self._section_editor.image_caption_changed.connect(self._on_image_caption_changed)
        self._section_editor.image_selected.connect(self._on_image_selected)
        self._section_editor.image_edits_changed.connect(self._on_image_edits_changed)
        self._section_editor.tool_selected.connect(self._on_tool_selected)
        self._section_editor.bosello_picker_requested.connect(self._on_bosello_picker_requested)

        self._vm.project_loaded.connect(self._on_project_loaded)
        self._vm.project_display_name_changed.connect(self._on_project_display_name_changed)
        self._vm.sections_summary_ready.connect(self._on_sections_summary_ready)
        self._vm.preview_ready.connect(self._preview_panel.render_pages)
        self._vm.preview_generating.connect(self._on_preview_generating)
        self._vm.global_fields_ready.connect(self._on_global_fields_ready)
        self._vm.error_occurred.connect(
            lambda title, msg, details: show_friendly_error(self, title, msg, details)
        )
        self._vm.import_notice.connect(
            lambda title, msg: show_info(self, title, msg)
        )
        self._vm.export_finished.connect(self._on_export_finished)
        self._vm.layout_dirty_changed.connect(self._on_layout_dirty_changed)
        self._vm.data_dirty_changed.connect(self._on_data_dirty_changed)
        self._vm.template_dirty_changed.connect(self._on_layout_dirty_changed)
        self._vm.templates_list_ready.connect(self._populate_template_combo)
        self._vm.preview_metadata_ready.connect(self._on_preview_metadata)
        self._preview_panel.page_clicked.connect(self._on_preview_page_clicked)
        self._preview_panel.section_clicked.connect(self._on_preview_section_clicked)
        self._vm.version_timeline_changed.connect(self._on_version_timeline_changed)
        self._vm.version_status_changed.connect(self._on_version_status_changed)


    def _setup_shortcuts(self) -> None:
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        save_shortcut.activated.connect(self._on_register_version)

        export_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        export_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        export_shortcut.activated.connect(self._on_export_clicked)


    def _on_document_changed(self, document: ReportDocument | None) -> None:
        if document is None:
            self._document_title_label.setText("Nenhum documento carregado")
            self._active_section_label.setText("")
            self._sync_section_meta_row()
            self._clear_preview_pages()
            self._section_editor.update_document_context(None)
            return
        self._document_title_label.setText(
            document_header_label(document, self._app_state.project_session)
        )
        session = self._app_state.project_session
        if session is not None:
            paths = ProjectCommands.sync_attachment_paths(document, session)
        else:
            paths = list(document.attachment_pdf_paths)
            if not paths and document.source_pdf_path:
                paths = [document.source_pdf_path]
                document.attachment_pdf_paths = list(paths)
        self._section_editor.set_source_attachments(paths)
        self._section_editor.update_document_context(document)
        self._refresh_images()
        self._refresh_versions()
        self._vm.refresh_global_fields()
        self._section_editor.set_itens_medicao(self._vm.get_effective_itens_medicao())
        self._populate_template_combo(self._vm.list_templates())
        self._on_layout_dirty_changed(self._vm.is_layout_dirty())
        self._on_data_dirty_changed(self._vm.is_data_dirty())
        self._update_export_options_visibility()


    def _on_global_fields_ready(self, values: dict, overridden: set) -> None:
        self._section_editor.render_global_fields(values, overridden)


    def _on_edit_visibility_changed(self, visible: bool) -> None:
        self._edit_stack.setCurrentIndex(1 if visible else 0)
        self._edit_container.setVisible(visible)
        if visible:
            self._main_splitter.setSizes([240, 320, 800])
            QTimer.singleShot(0, self._preview_panel.center_horizontal_scroll)
        else:
            self._main_splitter.setSizes([240, 0, 1120])


    def _sync_section_meta_row(self) -> None:
        has_section = bool(self._active_section_label.text().strip())
        self._active_section_label.setVisible(has_section)
        self._meta_sep_before_section.setVisible(True)
        self._meta_sep_before_layout.setVisible(has_section)


    def _on_section_selected(self, section_id: str) -> None:
        self._active_section_id = section_id
        anchor = self._section_anchor_map.get(section_id, {})
        if isinstance(anchor, dict):
            title = anchor.get("display_title") or anchor.get("title") or section_id
        else:
            title = section_id
        self._active_section_label.setText(f"Seção: {title}")
        self._sync_section_meta_row()
        self._focus_preview_section(section_id)


    def _on_section_delete(self, section_id: str) -> None:
        if not confirm_action(
            self,
            "Excluir seção",
            "Deseja remover esta seção personalizada do sumário?",
        ):
            return
        if self._vm.delete_section(section_id):
            if self._active_section_id == section_id:
                self._active_section_id = None
                self._active_section_label.setText("")
                self._sync_section_meta_row()


    def _on_add_custom_section(self) -> None:
        section_id = self._vm.add_custom_section("Nova seção")
        if not section_id:
            return
        self._active_section_id = section_id
        self._section_editor.open_edit_for_section(section_id)
        self._active_section_label.setText("Seção: Nova seção")
        self._sync_section_meta_row()
        self._section_editor.focus_section_title()


    def _on_export_validation(self, issues: list[dict]) -> None:
        apply_export_validation_banner(self._banner, issues)


    def _on_export_clicked(self) -> None:
        run_workspace_export(
            self,
            self._vm,
            self._app_state,
            export_individual=self._export_individual_action.isChecked(),
            export_merged=self._export_merged_action.isChecked(),
        )


    def _on_export_finished(self, final_path: Path) -> None:
        show_info(self, "Exportação concluída", f"Relatório salvo em:\n{final_path}")

