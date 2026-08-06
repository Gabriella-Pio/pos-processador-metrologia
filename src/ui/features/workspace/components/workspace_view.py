"""
Workspace — editor à esquerda, preview à direita, abas por PDF do projeto.
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QKeySequence, QPixmap, QShortcut
from PyQt6.QtWidgets import (
    QFileDialog,
    QLabel,
    QPushButton,
    QTabBar,
    QVBoxLayout,
    QWidget,
)

from src.core.domain.ports import ReportDocument
from src.ui.components.inputs import LayoutTemplateSelector
from src.ui.components.icons import icon_plus
from src.ui.components.feedback import (
    FeedbackLevel,
    InlineBanner,
    confirm_action,
    show_friendly_error,
    show_info,
)
from src.ui.features.workspace.dialogs.save_template_dialog import SaveTemplateDialog
from src.ui.features.workspace.dialogs.version_register_dialog import VersionRegisterDialog
from src.ui.styles import SPACING
from src.ui.controllers.app_state import AppState
from src.ui.features.workspace.commands.project_commands import ProjectCommands
from src.ui.features.workspace.viewmodels.workspace_viewmodel import WorkspaceViewModel
from src.ui.features.workspace.components.section_editor_panel import SectionEditorPanel
from src.ui.features.workspace.components.workspace_export_flow import (
    apply_export_validation_banner,
    run_workspace_export,
)
from src.ui.features.workspace.components.workspace_preview_chrome import (
    build_workspace_action_bar,
    build_workspace_preview_column,
    build_workspace_project_tabs_strip,
)
from src.ui.shared.report_editor.editor_shell import build_editor_stack, create_three_column_splitter
from src.ui.shared.report_editor.preview_panel import PreviewPanel


class WorkspaceView(QWidget):
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
        self._project_tabs.setExpanding(False)
        self._project_tabs.currentChanged.connect(self._on_project_tab_changed)

        self._add_pdf_btn = QPushButton("Adicionar PDF")
        self._add_pdf_btn.setObjectName("WorkspaceAddPdfTab")
        self._add_pdf_btn.setIcon(icon_plus())
        self._add_pdf_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._add_pdf_btn.setToolTip("Incluir mais relatórios ZEISS no projeto")
        self._add_pdf_btn.clicked.connect(self._on_add_pdf_clicked)

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

    def refresh_appearance(self) -> None:
        self._banner.refresh_appearance()
        if hasattr(self, "_export_btn"):
            self._export_btn.refresh_appearance()
        if hasattr(self, "_more_btn"):
            self._more_btn.refresh_appearance()
        self._section_editor.refresh_appearance()
        self._preview_panel.refresh_appearance()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        (
            self._project_tabs_strip,
            self._preview_status_label,
            self._data_dirty_label,
            self._more_btn,
            self._export_btn,
            self._preview_menu,
        ) = build_workspace_project_tabs_strip(
            self._project_tabs,
            self._add_pdf_btn,
            on_more_clicked=self._show_preview_menu,
            on_export_clicked=self._on_export_clicked,
            on_save_layout=self._on_save_template_clicked,
            on_change_layout=self._focus_template_combo,
        )
        self._save_layout_action = self._project_tabs_strip._save_layout_action
        self._export_individual_action = self._project_tabs_strip._export_individual_action
        self._export_merged_action = self._project_tabs_strip._export_merged_action
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
        self._section_editor.image_dropped.connect(self._on_image_dropped)
        self._section_editor.image_remove_requested.connect(self._on_image_remove)
        self._section_editor.image_caption_changed.connect(self._on_image_caption_changed)
        self._section_editor.image_selected.connect(self._on_image_selected)
        self._section_editor.tool_selected.connect(self._on_tool_selected)

        self._vm.project_loaded.connect(self._on_project_loaded)
        self._vm.sections_summary_ready.connect(self._on_sections_summary_ready)
        self._vm.preview_ready.connect(self._preview_panel.render_pages)
        self._vm.preview_generating.connect(self._on_preview_generating)
        self._vm.global_fields_ready.connect(self._on_global_fields_ready)
        self._vm.error_occurred.connect(
            lambda title, msg, details: show_friendly_error(self, title, msg, details)
        )
        self._vm.export_finished.connect(self._on_export_finished)
        self._vm.layout_dirty_changed.connect(self._on_layout_dirty_changed)
        self._vm.data_dirty_changed.connect(self._on_data_dirty_changed)
        self._vm.template_dirty_changed.connect(self._on_layout_dirty_changed)
        self._vm.templates_list_ready.connect(self._populate_template_combo)
        self._vm.preview_metadata_ready.connect(self._on_preview_metadata)
        self._preview_panel.page_clicked.connect(self._on_preview_page_clicked)
        self._vm.export_validation_ready.connect(self._on_export_validation)

    def _setup_shortcuts(self) -> None:
        export_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        export_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        export_shortcut.activated.connect(self._on_export_clicked)

    def _show_preview_menu(self) -> None:
        self._preview_menu.popup(
            self._more_btn.mapToGlobal(QPoint(0, self._more_btn.height()))
        )

    def _populate_template_combo(self, templates: list[dict]) -> None:
        session = self._app_state.project_session
        current_id = session.template_id if session else "default"
        self._template_combo.blockSignals(True)
        self._template_combo.clear()
        for template in templates:
            self._template_combo.addItem(template["name"], template["id"])
        index = self._template_combo.findData(current_id)
        if index >= 0:
            self._template_combo.setCurrentIndex(index)
        self._template_combo.blockSignals(False)

    def _on_template_changed(self, index: int) -> None:
        if index < 0:
            return
        template_id = self._template_combo.itemData(index)
        session = self._app_state.project_session
        if session is None or template_id == session.template_id:
            return
        if self._vm.is_layout_dirty():
            if not confirm_action(
                self,
                "Alterar template?",
                "Há alterações no layout atual. Trocar o template vai substituí-las pelos defaults salvos.",
            ):
                self._populate_template_combo(self._vm.list_templates())
                return
        self._vm.change_template(template_id)

    def _on_layout_dirty_changed(self, dirty: bool) -> None:
        suffix = " ●" if dirty else ""
        self._save_layout_action.setEnabled(dirty)
        self._save_layout_action.setText(f"Salvar layout…{suffix}")
        self._template_selector.set_layout_dirty(dirty)

    def _on_data_dirty_changed(self, dirty: bool) -> None:
        self._data_dirty_label.setText("● Dados não salvos no PDF" if dirty else "")

    def _focus_template_combo(self) -> None:
        self._template_combo.setFocus()
        self._template_combo.showPopup()

    def _on_save_template_clicked(self) -> None:
        document = self._app_state.active_document
        session = self._app_state.project_session
        if document is None or session is None:
            return
        dialog = SaveTemplateDialog(
            self._vm.list_templates(),
            document.template_id,
            self,
        )
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        template_id = self._vm.save_current_as_template(
            dialog.template_name,
            dialog.create_new,
        )
        if template_id:
            show_info(self, "Template salvo", f"Layout salvo como “{dialog.template_name}”.")
            self._populate_template_combo(self._vm.list_templates())

    def _update_export_options_visibility(self) -> None:
        session = self._app_state.project_session
        multi = session is not None and len(session.documents) > 1
        self._export_individual_action.setVisible(multi)
        self._export_merged_action.setVisible(multi)

    def _on_project_loaded(self, session) -> None:
        self._project_tabs.blockSignals(True)
        while self._project_tabs.count():
            self._project_tabs.removeTab(0)
        for index, slot in enumerate(session.documents):
            base = slot.evaluated_component[:20] or slot.source_pdf_path.stem[:20]
            kind = getattr(slot, "source_kind", "") or (
                slot.document.source_kind if slot.document else ""
            )
            badge = "Tomo" if kind == "insp_ect" else "MMC"
            label = f"{base} [{badge}]"
            self._project_tabs.addTab(label)
            path = slot.source_pdf_path.resolve()
            tip = f"{path.name}\n{path}\nOrigem: {kind or 'desconhecida'}"
            if slot.template_id:
                tip += f"\nTemplate: {slot.template_id}"
            self._project_tabs.setTabToolTip(index, tip)
        self._project_tabs.setCurrentIndex(session.active_index)
        self._project_tabs.blockSignals(False)
        self._update_export_options_visibility()

    def _on_project_changed(self, session) -> None:
        if session is None:
            while self._project_tabs.count():
                self._project_tabs.removeTab(0)
        self._update_export_options_visibility()

    def _on_project_tab_changed(self, index: int) -> None:
        if index < 0:
            return
        self._vm.switch_document(index)

    def _on_document_changed(self, document: ReportDocument | None) -> None:
        if document is None:
            self._document_title_label.setText("Nenhum documento carregado")
            self._active_section_label.setText("")
            self._sync_section_meta_row()
            self._clear_preview_pages()
            self._section_editor.update_document_context(None)
            return
        self._document_title_label.setText(
            f"{document.client_project} — {document.evaluated_component}"
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

    def _on_preview_generating(self, generating: bool) -> None:
        self._preview_status_label.setText("Atualizando preview…" if generating else "")
        self._preview_panel.set_status_text("Atualizando preview…" if generating else "")

    def _on_edit_visibility_changed(self, visible: bool) -> None:
        self._edit_stack.setCurrentIndex(1 if visible else 0)
        self._edit_container.setVisible(visible)
        if visible:
            self._main_splitter.setSizes([240, 320, 800])
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
        title = anchor.get("title", section_id) if isinstance(anchor, dict) else section_id
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
        if section_id:
            self._active_section_id = section_id
            self._section_editor.open_edit_for_section(section_id)
            self._active_section_label.setText("Seção: Nova seção")
            self._sync_section_meta_row()

    def _on_image_dropped(self, image_path: Path) -> None:
        # Preferir a seção em edição — evita gravar foto na seção errada.
        section_id = self._section_editor.editing_section_id() or self._active_section_id
        if section_id is None:
            show_friendly_error(
                self,
                "Selecione uma seção",
                "Abra a edição de uma seção antes de associar uma fotografia.",
            )
            return
        self._active_section_id = section_id
        self._vm.add_image_to_section(image_path, section_id)

    def _on_image_remove(self, image) -> None:
        self._vm.remove_image(image)

    def _on_image_caption_changed(self, image, caption: str) -> None:
        self._vm.update_image_caption(image, caption)

    def _on_image_selected(self, image) -> None:
        self._active_annotation_image = image

    def _on_tool_selected(self, tool_id: str) -> None:
        self._active_annotation_tool = tool_id
        target = getattr(self._active_annotation_image, "image_path", None)
        name = Path(target).name if target else "nenhuma foto"
        self._preview_panel.scroll_area().setToolTip(
            f"Ferramenta: {tool_id} · foto: {name}. Clique na preview para aplicar (MVP)."
        )

    def _refresh_images(self) -> None:
        document = self._app_state.active_document
        if document is not None:
            self._section_editor.render_images(document.images)

    def _refresh_versions(self) -> None:
        document = self._app_state.active_document
        if document is not None:
            self._section_editor.render_versions(document.version_history)

    def _on_sections_summary_ready(self, sections: list[dict]) -> None:
        self._section_anchor_map = {s["id"]: s for s in sections}
        self._preview_panel.set_anchor_map(self._section_anchor_map)
        for section in sections:
            section.setdefault("subtitle", "")
            section.setdefault("body", "")
        self._section_editor.render_sections(sections)
        if self._active_section_id:
            self._section_editor.set_active_section(self._active_section_id)
            self._focus_preview_section(self._active_section_id)

    def _on_preview_page_clicked(self, page_number: int) -> None:
        section_id = self._preview_panel.section_id_for_page(page_number)
        if section_id:
            self._section_editor.navigate_to_section(section_id)

    def _on_preview_metadata(self, anchor_map: dict) -> None:
        self._preview_panel.update_anchor_map(anchor_map)
        for section_id, info in anchor_map.items():
            if section_id in self._section_anchor_map:
                self._section_anchor_map[section_id]["page_start"] = info.get("page")
                self._section_anchor_map[section_id]["anchor_rect"] = info

    def _on_export_validation(self, issues: list[dict]) -> None:
        apply_export_validation_banner(self._banner, issues)

    def _clear_preview_pages(self) -> None:
        self._preview_panel.clear()

    def _focus_preview_section(self, section_id: str) -> None:
        self._preview_panel.focus_section(section_id)

    def _on_add_pdf_clicked(self) -> None:
        document = self._app_state.active_document
        default_component = document.evaluated_component if document else "Componente"
        paths, _ = QFileDialog.getOpenFileNames(self, "Adicionar PDFs ao projeto", "", "PDF (*.pdf)")
        if paths:
            self._vm.append_pdfs_to_project([Path(p) for p in paths], default_component)

    def _on_register_version(self) -> None:
        document = self._app_state.active_document
        if document is None:
            return
        default_responsible = ""
        if document.control_info is not None:
            default_responsible = document.control_info.measured_by or ""
        dialog = VersionRegisterDialog(default_responsible, self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        responsible, description = dialog.get_values()
        self._vm.register_new_version(responsible, description)

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
