"""
Workspace — editor à esquerda, preview à direita, abas por PDF do projeto.
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QKeySequence, QPixmap, QShortcut
from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QTabBar,
    QVBoxLayout,
    QWidget,
)

from src.core.domain.ports import ReportDocument
from src.ui.components.buttons import ChromeIconButton, PrimaryButton
from src.ui.components.inputs import LayoutTemplateSelector
from src.ui.components.icons import icon_ellipsis, icon_export, icon_plus
from src.ui.components.feedback import (
    FeedbackLevel,
    InlineBanner,
    confirm_action,
    show_friendly_error,
    show_info,
)
from src.ui.features.workspace.dialogs.custom_section_dialog import CustomSectionDialog
from src.ui.features.workspace.dialogs.save_template_dialog import SaveTemplateDialog
from src.ui.features.workspace.dialogs.version_register_dialog import VersionRegisterDialog
from src.ui.styles import SPACING, caption_style
from src.ui.controllers.app_state import AppState
from src.ui.features.workspace.viewmodels.workspace_viewmodel import WorkspaceViewModel
from src.ui.features.workspace.components.section_editor_panel import SectionEditorPanel


class WorkspaceView(QWidget):
    def __init__(self, app_state: AppState, view_model: WorkspaceViewModel, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("WorkspaceSurface")
        self._app_state = app_state
        self._vm = view_model
        self._active_section_id: str | None = None
        self._active_annotation_tool: str | None = None
        self._preview_page_items: list[dict] = []
        self._section_anchor_map: dict[str, dict] = {}
        self._active_preview_page: int | None = None
        self._active_preview_anchor: dict | None = None

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
        self._preview_scroll = QScrollArea()
        self._preview_scroll.setObjectName("WorkspacePreviewScroll")
        self._preview_pages_widget = QWidget()
        self._preview_pages_layout = QVBoxLayout(self._preview_pages_widget)
        self._banner = InlineBanner("", level=FeedbackLevel.INFO)
        self._banner.sync_visibility()

        self._export_individual_cb = QCheckBox("Exportar PDFs individuais")
        self._export_individual_cb.setChecked(True)
        self._export_merged_cb = QCheckBox("Exportar um único PDF")
        self._export_merged_cb.setChecked(True)
        self._export_merged_cb.setEnabled(False)
        self._export_merged_cb.setToolTip("Em breve — mescla seções institucionais")

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
        self._refresh_preview_page_styles()

    def _refresh_preview_page_styles(self) -> None:
        for item in self._preview_page_items:
            page_label = item.get("page_label")
            image_label = item.get("image_label")
            if page_label is not None:
                page_label.setStyleSheet("")
            if image_label is not None:
                image_label.setStyleSheet("")

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._project_tabs_strip = self._build_project_tabs_row()
        outer.addWidget(self._project_tabs_strip)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._section_editor)
        splitter.addWidget(self._build_editor_column())
        splitter.addWidget(self._build_preview_panel())
        splitter.setSizes([260, 420, 680])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setStretchFactor(2, 3)
        self._main_splitter = splitter
        self._edit_container.setVisible(False)
        outer.addWidget(splitter, stretch=1)

    def _build_project_tabs_row(self) -> QWidget:
        row = QWidget()
        row.setObjectName("WorkspaceProjectTabsStrip")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(SPACING.md, SPACING.xs, SPACING.md, SPACING.xs)
        layout.setSpacing(SPACING.sm)
        layout.addWidget(self._project_tabs)
        layout.addWidget(self._add_pdf_btn)
        layout.addStretch(1)

        self._preview_status_label = QLabel("")
        self._preview_status_label.setObjectName("WorkspacePreviewStatus")
        layout.addWidget(self._preview_status_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._data_dirty_label = QLabel("")
        self._data_dirty_label.setObjectName("WorkspaceDataDirty")
        layout.addWidget(self._data_dirty_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._more_btn = ChromeIconButton(icon_ellipsis(), "Mais ações do projeto")
        self._more_btn.clicked.connect(self._show_preview_menu)
        layout.addWidget(self._more_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._export_btn = PrimaryButton("Exportar", icon=icon_export())
        self._export_btn.setToolTip("Exportar PDF (Ctrl+E)")
        self._export_btn.clicked.connect(self._on_export_clicked)
        layout.addWidget(self._export_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._build_preview_menu()
        return row

    def _build_preview_menu(self) -> None:
        self._preview_menu = QMenu(self)
        self._save_layout_action = self._preview_menu.addAction("Salvar layout…")
        self._save_layout_action.triggered.connect(self._on_save_template_clicked)
        self._change_layout_action = self._preview_menu.addAction("Alterar layout…")
        self._change_layout_action.triggered.connect(self._focus_template_combo)
        self._preview_menu.addSeparator()
        self._export_individual_action = self._preview_menu.addAction("Exportar PDFs individuais")
        self._export_individual_action.setCheckable(True)
        self._export_individual_action.setChecked(True)
        self._export_individual_action.toggled.connect(self._export_individual_cb.setChecked)
        self._export_merged_action = self._preview_menu.addAction("Exportar um único PDF")
        self._export_merged_action.setCheckable(True)
        self._export_merged_action.setChecked(True)
        self._export_merged_action.setEnabled(False)
        self._export_merged_action.setToolTip("Em breve — mescla seções institucionais")
        self._export_merged_action.toggled.connect(self._export_merged_cb.setChecked)
        self._export_individual_cb.toggled.connect(self._export_individual_action.setChecked)
        self._export_merged_cb.toggled.connect(self._export_merged_action.setChecked)

    def _build_action_bar(self) -> QWidget:
        self._action_bar = QWidget()
        self._action_bar.setObjectName("WorkspacePreviewContext")
        row = QHBoxLayout(self._action_bar)
        row.setContentsMargins(0, SPACING.xs, 0, SPACING.xs)
        row.setSpacing(SPACING.xs)
        row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        row.addWidget(self._document_title_label)
        self._meta_sep_before_section = QLabel("·")
        self._meta_sep_before_section.setObjectName("WorkspaceMetaSeparator")
        row.addWidget(self._meta_sep_before_section)
        row.addWidget(self._active_section_label)
        self._meta_sep_before_layout = QLabel("·")
        self._meta_sep_before_layout.setObjectName("WorkspaceMetaSeparator")
        row.addWidget(self._meta_sep_before_layout)

        self._template_selector = LayoutTemplateSelector()
        self._template_combo = self._template_selector.combo
        self._template_combo.currentIndexChanged.connect(self._on_template_changed)
        row.addWidget(self._template_selector)
        row.addStretch(1)

        self._export_options = QWidget()
        export_opts_layout = QHBoxLayout(self._export_options)
        export_opts_layout.setContentsMargins(0, 0, 0, 0)
        export_opts_layout.setSpacing(SPACING.md)
        export_opts_layout.addWidget(self._export_individual_cb)
        export_opts_layout.addWidget(self._export_merged_cb)
        return self._action_bar

    def _build_editor_column(self) -> QWidget:
        self._edit_container = QFrame()
        self._edit_container.setObjectName("WorkspaceEditorPanel")
        layout = QVBoxLayout(self._edit_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._edit_placeholder = QLabel(
            "Selecione uma seção no sumário.\n"
            "Duplo-clique ou use o ícone de edição para abrir o formulário."
        )
        self._edit_placeholder.setObjectName("WorkspaceEditorPlaceholder")
        self._edit_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._edit_placeholder.setWordWrap(True)

        self._edit_stack = QStackedWidget()
        self._edit_stack.setObjectName("WorkspaceEditorStack")
        self._edit_stack.addWidget(self._edit_placeholder)
        self._edit_stack.addWidget(self._section_editor.edit_view)
        layout.addWidget(self._edit_stack)
        return self._edit_container

    def _build_preview_panel(self) -> QWidget:
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
        header_layout.addWidget(self._build_action_bar())
        layout.addWidget(header)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(SPACING.lg, SPACING.md, SPACING.lg, SPACING.lg)
        body_layout.setSpacing(SPACING.sm)

        self._preview_scroll.setWidgetResizable(True)
        self._preview_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._preview_scroll.setWidget(self._preview_pages_widget)
        self._preview_pages_layout.setContentsMargins(0, 0, 0, 0)
        self._preview_pages_layout.setSpacing(SPACING.lg)

        body_layout.addWidget(self._banner)
        body_layout.addWidget(self._preview_scroll, stretch=1)
        layout.addWidget(body, stretch=1)
        return container

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
        self._section_editor.tool_selected.connect(self._on_tool_selected)

        self._vm.project_loaded.connect(self._on_project_loaded)
        self._vm.sections_summary_ready.connect(self._on_sections_summary_ready)
        self._vm.preview_ready.connect(self._render_preview_pages)
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
            label = slot.evaluated_component[:24] or slot.source_pdf_path.stem[:24]
            self._project_tabs.addTab(label)
            path = slot.source_pdf_path.resolve()
            self._project_tabs.setTabToolTip(index, f"{path.name}\n{path}")
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
        if session and len(session.documents) > 1:
            paths = [s.source_pdf_path for s in session.documents]
            self._section_editor.set_source_attachments(paths)
        else:
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

    def _on_edit_visibility_changed(self, visible: bool) -> None:
        self._edit_stack.setCurrentIndex(1 if visible else 0)
        self._edit_container.setVisible(visible)
        if visible:
            self._main_splitter.setSizes([260, 420, 680])
        else:
            self._main_splitter.setSizes([260, 0, 1100])

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
        dialog = CustomSectionDialog(self)
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        section_id = self._vm.add_custom_section(dialog.get_title())
        if section_id:
            self._active_section_id = section_id
            self._section_editor.open_edit_for_section(section_id)
            anchor = self._section_anchor_map.get(section_id, {})
            title = anchor.get("title", section_id) if isinstance(anchor, dict) else section_id
            self._active_section_label.setText(f"Seção: {title}")
            self._sync_section_meta_row()

    def _on_image_dropped(self, image_path: Path) -> None:
        if self._active_section_id is None:
            show_friendly_error(
                self,
                "Selecione uma seção",
                "Escolha uma seção no sumário antes de associar uma fotografia.",
            )
            return
        self._vm.add_image_to_section(image_path, self._active_section_id)

    def _on_tool_selected(self, tool_id: str) -> None:
        self._active_annotation_tool = tool_id
        self._preview_scroll.setToolTip(
            f"Ferramenta ativa: {tool_id}. Clique na preview para aplicar (MVP)."
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
        for section in sections:
            section.setdefault("subtitle", "")
            section.setdefault("body", "")
        self._section_editor.render_sections(sections)
        if self._active_section_id:
            self._section_editor.set_active_section(self._active_section_id)
            self._focus_preview_section(self._active_section_id)

    def _render_preview_pages(self, pages_png: list[bytes]) -> None:
        scroll_pos = self._preview_scroll.verticalScrollBar().value()
        prev_count = len(self._preview_page_items)
        self._clear_preview_pages()
        if not pages_png:
            empty = QLabel("Nenhuma página disponível para preview.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setObjectName("SidebarHint")
            empty.setStyleSheet(caption_style())
            self._preview_pages_layout.addWidget(empty)
            return

        self._preview_page_items = []
        for index, page_png in enumerate(pages_png, start=1):
            page_container = QWidget()
            page_layout = QVBoxLayout(page_container)
            page_layout.setContentsMargins(0, 0, 0, 0)

            page_label = QLabel(f"Página {index}")
            page_label.setObjectName("WorkspacePageLabel")
            page_label.setCursor(Qt.CursorShape.PointingHandCursor)
            page_label.mousePressEvent = lambda event, pn=index: self._on_preview_page_clicked(pn)  # type: ignore[method-assign]
            image_label = QLabel()
            image_label.setObjectName("WorkspacePreviewPage")
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pixmap = QPixmap()
            pixmap.loadFromData(page_png)
            image_label.setPixmap(pixmap)

            page_layout.addWidget(page_label)
            page_layout.addWidget(image_label)
            self._preview_pages_layout.addWidget(page_container)
            self._preview_page_items.append({
                "page_number": index,
                "container": page_container,
                "page_label": page_label,
                "image_label": image_label,
                "base_pixmap": pixmap,
            })

        self._preview_pages_layout.addStretch(1)
        if abs(len(pages_png) - prev_count) <= 1:
            self._preview_scroll.verticalScrollBar().setValue(scroll_pos)

    def _on_preview_page_clicked(self, page_number: int) -> None:
        for section_id, info in self._section_anchor_map.items():
            page = (info or {}).get("page_start") or (info or {}).get("page")
            if page == page_number:
                self._section_editor.navigate_to_section(section_id)
                return

    def _on_preview_metadata(self, anchor_map: dict) -> None:
        for section_id, info in anchor_map.items():
            if section_id in self._section_anchor_map:
                self._section_anchor_map[section_id]["page_start"] = info.get("page")
                self._section_anchor_map[section_id]["anchor_rect"] = info

    def _on_export_validation(self, issues: list[dict]) -> None:
        errors = [i for i in issues if i.get("level") == "error"]
        warnings = [i for i in issues if i.get("level") == "warning"]
        if errors:
            self._banner.set_level(FeedbackLevel.DANGER)
            self._banner.set_message(errors[0]["message"])
        elif warnings:
            self._banner.set_level(FeedbackLevel.WARNING)
            self._banner.set_message(warnings[0]["message"])
        else:
            self._banner.set_level(FeedbackLevel.INFO)
            self._banner.set_message("")
            self._banner.sync_visibility()

    def _clear_preview_pages(self) -> None:
        while self._preview_pages_layout.count():
            item = self._preview_pages_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._preview_page_items = []

    def _focus_preview_section(self, section_id: str) -> None:
        section = self._section_anchor_map.get(section_id) or {}
        anchor = section.get("anchor_rect") if isinstance(section.get("anchor_rect"), dict) else section
        page_number = section.get("page_start") or (anchor or {}).get("page")
        if page_number is None or page_number < 1 or page_number > len(self._preview_page_items):
            return
        self._active_preview_anchor = anchor
        self._active_preview_page = page_number
        item = self._preview_page_items[page_number - 1]
        self._preview_scroll.ensureWidgetVisible(item["container"], 24, 24)

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
        session = self._app_state.project_session
        multi = session is not None and len(session.documents) > 1

        if multi and self._export_merged_cb.isChecked() and not self._export_merged_cb.isEnabled():
            show_info(
                self,
                "Exportação unificada",
                "Em breve — mescla seções institucionais em um único PDF.",
            )

        if multi and self._export_individual_cb.isChecked():
            output_dir = QFileDialog.getExistingDirectory(
                self, "Pasta para exportação em lote"
            )
            if output_dir:
                paths = self._vm.export_all_documents(Path(output_dir))
                if paths:
                    show_info(self, "Exportação em lote", f"{len(paths)} PDF(s) exportado(s).")
            return

        output_path, _ = QFileDialog.getSaveFileName(self, "Exportar PDF", "", "PDF (*.pdf)")
        if output_path:
            self._vm.export_document(Path(output_path))

    def _on_export_finished(self, final_path: Path) -> None:
        show_info(self, "Exportação concluída", f"Relatório salvo em:\n{final_path}")
