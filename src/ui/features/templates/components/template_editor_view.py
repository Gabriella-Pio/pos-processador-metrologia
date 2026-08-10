"""
Editor de templates full-page — shell espelhando o workspace.
"""
from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from src.ui.components.buttons import ChromeIconButton, PrimaryButton
from src.ui.components.feedback import confirm_action, show_friendly_error, show_info
from src.ui.components.icons import icon_ellipsis, icon_edit
from src.ui.features.templates.components.template_sidebar_panel import TemplateSidebarPanel
from src.ui.features.templates.viewmodels.template_editor_viewmodel import TemplateEditorViewModel
from src.ui.shared.report_editor.editor_shell import build_editor_column, create_three_column_splitter
from src.ui.shared.report_editor.preview_panel import PreviewPanel
from src.ui.styles import SPACING, caption_style


class TemplateEditorView(QWidget):
    """Tela full-page para editar estrutura e defaults de templates."""

    saved = pyqtSignal(str)

    def __init__(self, view_model: TemplateEditorViewModel, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("TemplateEditorSurface")
        self._vm = view_model
        self._active_section_id: str | None = None
        self._section_anchor_map: dict[str, dict] = {}

        self._sidebar = TemplateSidebarPanel()
        self._preview_panel = PreviewPanel()

        self._name_field = QLineEdit()
        self._name_field.setObjectName("TemplateNameInput")
        self._name_field.setPlaceholderText("Nome do template")
        self._dirty_label = QLabel("")
        self._dirty_label.setObjectName("WorkspaceDataDirty")

        self._edit_placeholder = QLabel("Selecione uma seção no sumário para editar os defaults.")
        self._edit_placeholder.setObjectName("SidebarHint")
        self._edit_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._edit_placeholder.setWordWrap(True)

        self._section_title_label = QLabel("")
        self._section_title_label.setObjectName("WorkspaceActiveSection")

        self._build_ui()
        self._sidebar.bind_view_model(self._vm)
        self._connect_signals()

    def refresh_appearance(self) -> None:
        self._sidebar.refresh_appearance()
        self._preview_panel.refresh_appearance()
        if hasattr(self, "_more_btn"):
            self._more_btn.refresh_appearance()
        if hasattr(self, "_save_btn"):
            self._save_btn.refresh_appearance()
        self._edit_placeholder.setStyleSheet(caption_style())

    def load_template(self, template_id: str) -> None:
        self._vm.load(template_id)

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._build_global_strip())

        context = QWidget()
        context.setObjectName("WorkspacePreviewContextBar")
        context_layout = QHBoxLayout(context)
        context_layout.setContentsMargins(SPACING.lg, SPACING.sm, SPACING.lg, SPACING.sm)
        context_layout.addWidget(self._section_title_label)
        context_layout.addStretch(1)

        self._edit_container, self._edit_stack = build_editor_column(
            self._edit_placeholder,
            self._sidebar.edit_view,
            header=context,
        )
        self._edit_container.setVisible(False)

        splitter = create_three_column_splitter(
            self._sidebar,
            self._edit_container,
            self._build_preview_column(),
        )
        self._main_splitter = splitter
        outer.addWidget(splitter, stretch=1)

    def _build_global_strip(self) -> QWidget:
        strip = QWidget()
        strip.setObjectName("WorkspaceGlobalStrip")
        layout = QHBoxLayout(strip)
        layout.setContentsMargins(SPACING.lg, SPACING.sm, SPACING.lg, SPACING.sm)
        layout.setSpacing(SPACING.md)

        name_icon = QLabel()
        name_icon.setPixmap(icon_edit().pixmap(16, 16))
        layout.addWidget(name_icon)
        layout.addWidget(self._name_field, stretch=1)
        layout.addWidget(self._dirty_label)
        layout.addStretch(1)

        self._more_btn = ChromeIconButton(icon_ellipsis(), "Mais opções")
        self._more_btn.clicked.connect(self._show_menu)
        self._save_btn = PrimaryButton("Salvar")
        self._save_btn.clicked.connect(self._on_save)
        layout.addWidget(self._more_btn)
        layout.addWidget(self._save_btn)
        self._build_menu()
        return strip

    def _build_menu(self) -> None:
        self._menu = QMenu(self)
        self._discard_action = self._menu.addAction("Descartar alterações")
        self._discard_action.triggered.connect(self._on_discard)

    def _show_menu(self) -> None:
        self._discard_action.setEnabled(self._vm.is_dirty())
        self._menu.popup(self._more_btn.mapToGlobal(QPoint(0, self._more_btn.height())))

    def _build_preview_column(self) -> QWidget:
        container = QWidget()
        container.setObjectName("WorkspacePreviewPanel")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("WorkspacePreviewHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(SPACING.lg, SPACING.sm, SPACING.lg, SPACING.sm)
        title = QLabel("Preview do template")
        title.setObjectName("WorkspaceDocTitleCompact")
        header_layout.addWidget(title)
        layout.addWidget(header)
        layout.addWidget(self._preview_panel, stretch=1)
        return container

    def _connect_signals(self) -> None:
        self._name_field.editingFinished.connect(
            lambda: self._vm.set_template_name(self._name_field.text())
        )
        self._sidebar.edit_visibility_changed.connect(self._on_edit_visibility_changed)
        self._sidebar.section_edit_requested.connect(self._on_section_selected)
        self._sidebar.section_enabled_changed.connect(self._vm.set_section_enabled)
        self._sidebar.add_custom_section_requested.connect(self._on_add_custom_section)
        self._sidebar.section_delete_requested.connect(self._on_delete_custom_section)
        self._sidebar.sections_reordered.connect(self._vm.reorder_sections)
        self._preview_panel.page_clicked.connect(self._on_preview_page_clicked)
        self._preview_panel.section_clicked.connect(self._on_preview_section_clicked)

        self._vm.template_name_changed.connect(self._name_field.setText)
        self._vm.dirty_changed.connect(self._on_dirty_changed)
        self._vm.sections_summary_ready.connect(self._on_sections_summary)
        self._vm.global_fields_ready.connect(self._sidebar.render_global_fields)
        self._vm.preview_ready.connect(self._preview_panel.render_pages)
        self._vm.preview_generating.connect(
            lambda generating: self._preview_panel.set_status_text(
                "Atualizando preview…" if generating else ""
            )
        )
        self._vm.preview_metadata_ready.connect(
            lambda metadata: self._preview_panel.update_anchor_map(metadata.get("sections", metadata))
        )
        self._vm.saved.connect(self.saved.emit)
        self._vm.error_occurred.connect(
            lambda title, msg, details: show_friendly_error(self, title, msg, details)
        )

    def _on_edit_visibility_changed(self, visible: bool) -> None:
        self._edit_stack.setCurrentIndex(1 if visible else 0)
        self._edit_container.setVisible(visible)
        if visible:
            self._main_splitter.setSizes([240, 320, 800])
            QTimer.singleShot(0, self._preview_panel.center_horizontal_scroll)
        else:
            self._main_splitter.setSizes([240, 0, 1120])
            self._section_title_label.setText("")

    def _on_section_selected(self, section_id: str) -> None:
        self._active_section_id = section_id
        self._vm.set_active_section(section_id)
        section = self._section_anchor_map.get(section_id, {})
        title = section.get("display_title") or section.get("title", section_id)
        self._section_title_label.setText(f"Seção: {title}")
        self._preview_panel.focus_section(section_id)

    def _on_add_custom_section(self) -> None:
        section_id = self._vm.add_custom_section("Nova seção")
        if section_id:
            self._sidebar.open_edit_for_section(section_id)
            self._on_section_selected(section_id)

    def _on_delete_custom_section(self, section_id: str) -> None:
        if not confirm_action(
            self,
            "Excluir seção",
            "Deseja remover esta seção personalizada do template?",
        ):
            return
        if self._vm.delete_custom_section(section_id):
            if self._active_section_id == section_id:
                self._active_section_id = None
                self._section_title_label.setText("")
                self._sidebar.close_edit()

    def _on_sections_summary(self, sections: list[dict]) -> None:
        self._section_anchor_map = {s["id"]: s for s in sections}
        self._sidebar.render_sections(sections)
        if self._active_section_id:
            self._sidebar.set_active_section(self._active_section_id)
            section = self._section_anchor_map.get(self._active_section_id, {})
            title = section.get("display_title") or section.get("title", self._active_section_id)
            self._section_title_label.setText(f"Seção: {title}")

    def _on_dirty_changed(self, dirty: bool) -> None:
        self._dirty_label.setText("● não salvo" if dirty else "")

    def _on_save(self) -> None:
        if self._vm.save():
            show_info(self, "Template salvo", "Estrutura e defaults atualizados com sucesso.")

    def _on_discard(self) -> None:
        if not self._vm.is_dirty():
            return
        if not confirm_action(
            self,
            "Descartar alterações?",
            "As mudanças não salvas serão perdidas.",
        ):
            return
        self._vm.load(self._vm.template_id)

    def _on_preview_page_clicked(self, page_number: int) -> None:
        section_id = self._preview_panel.section_id_for_page(page_number)
        if section_id:
            self._on_preview_section_clicked(section_id)

    def _on_preview_section_clicked(
        self,
        section_id: str,
        focus_target: str = "section_title",
        image_path: str = "",
    ) -> None:
        self._active_section_id = section_id
        self._vm.set_active_section(section_id)
        self._sidebar.open_edit_for_section(section_id)
        self._on_section_selected(section_id)
        if focus_target == "section_title":
            QTimer.singleShot(0, self._sidebar.edit_view.focus_section_title)
