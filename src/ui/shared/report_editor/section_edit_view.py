"""Formulário de edição de seção — título, blocos agrupados, mídia e placeholders."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.core.domain.report_field_registry import get_edit_fields, get_media_blocks
from src.core.application.interpretacao_edit import interpretacao_field_defs
from src.core.domain.ports import ReportImage, VersionEntry
from src.core.domain.table_row_registry import (
    INTRODUCAO_BLOCK_TITLES,
    SECTION_HEADING_DEFAULTS,
    TABLE_SECTIONS,
)
from src.core.domain.section_schema import is_custom_section_id
from src.ui.components.buttons import IconButton, SecondaryButton
from src.ui.components.icons import icon_close, icon_help
from src.ui.components.panels import ImageManagerPanel
from src.ui.components.panels.image_annotation_dialog import ImageAnnotationDialog
from src.ui.components.placeholder_field import PlaceholderTextEdit
from src.ui.shared.report_editor.sidebar_chrome import editor_panel_header
from src.ui.styles import SPACING, caption_style, sidebar_panel_style
from src.ui.shared.report_editor.draggable_table_rows_editor import DraggableTableRowsEditor
from src.ui.shared.report_editor.section_form_builder import SectionFormBuilder
from src.ui.shared.report_editor.section_tabs_builder import SectionTabPages, SectionTabsBuilder
from src.ui.shared.report_editor.template_layout_panel import TemplateLayoutPanel
from src.ui.features.workspace.components.edit_help import build_help_text
from src.ui.features.workspace.components.medicoes_table_editor import MedicoesTableEditor
from src.ui.features.workspace.components.section_field_schema import default_field_values


class SectionEditView(QFrame):
    back_requested = pyqtSignal()
    section_field_changed = pyqtSignal(str, str, str)
    section_field_restore_requested = pyqtSignal(str, str)
    table_rows_changed = pyqtSignal(str, list)
    table_rows_restore_requested = pyqtSignal(str)
    itens_medicao_changed = pyqtSignal(list)
    itens_medicao_restore_requested = pyqtSignal()
    image_dropped = pyqtSignal(Path)
    image_remove_requested = pyqtSignal(object)
    image_caption_changed = pyqtSignal(object, str)
    image_selected = pyqtSignal(object)
    image_edits_changed = pyqtSignal(object)
    bosello_picker_requested = pyqtSignal()
    tool_selected = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    section_restore_requested = pyqtSignal(str)
    media_kinds_changed = pyqtSignal(str, list)
    manage_versions_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("WorkspaceEditorView")
        self._section_id: str | None = None
        self._loading = False
        self._defaults_mode = False
        self._section_overrides: dict = {}
        self._version_entries: list[VersionEntry] = []
        self._locked_media_kinds: list[str] = []
        self._field_widgets: dict[str, PlaceholderTextEdit | QLineEdit] = {}
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(600)
        self._debounce.timeout.connect(self._flush_textarea_pending)
        self._pending_textarea_key: str | None = None

        header, self._header_title, actions_host = editor_panel_header()
        actions_layout = actions_host.layout()

        self._close_btn = IconButton(icon_close(), "Fechar edição")
        self._close_btn.clicked.connect(self.back_requested.emit)
        self._help_btn = IconButton(icon_help(), "Ajuda desta seção")
        self._help_btn.clicked.connect(self._show_help)
        actions_layout.addWidget(self._help_btn)
        actions_layout.addWidget(self._close_btn)

        self._section_title_edit = PlaceholderTextEdit(multiline=False)
        self._section_title_edit.text_changed.connect(self._on_section_title_changed)
        section_title_header = QLabel("Título da seção")
        section_title_header.setObjectName("GlobalFieldLabel")
        title_card = QFrame()
        title_card.setObjectName("GlobalFieldCard")
        title_card_layout = QVBoxLayout(title_card)
        title_card_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        title_card_layout.setSpacing(SPACING.xs)
        title_card_layout.addWidget(section_title_header)
        title_card_layout.addWidget(self._section_title_edit)
        self._section_title_host = title_card

        self._table_rows_editor = DraggableTableRowsEditor(
            "Linhas da tabela (como no preview)",
            allow_add_remove=True,
        )
        self._table_rows_editor.rows_changed.connect(self._on_table_rows_changed)
        self._table_rows_editor.restore_requested.connect(self._on_table_rows_restore)

        self._fields_host = QWidget()
        self._fields_layout = QVBoxLayout(self._fields_host)
        self._fields_layout.setContentsMargins(0, 0, 0, 0)
        self._fields_layout.setSpacing(SPACING.sm)
        self._form_builder = SectionFormBuilder(
            self._fields_host,
            self._fields_layout,
            defaults_mode=False,
            on_field_changed=self._on_field_changed,
            on_line_finished=self._on_line_finished,
            on_field_restore=lambda sid, key: self.section_field_restore_requested.emit(sid, key),
            on_manage_versions=self.manage_versions_requested.emit,
        )

        self._medicoes_editor = MedicoesTableEditor()
        self._medicoes_editor.rows_changed.connect(self.itens_medicao_changed.emit)
        self._medicoes_editor.restore_requested.connect(self.itens_medicao_restore_requested.emit)

        self._active_image: ReportImage | None = None
        self._section_images: list[ReportImage] = []
        self._image_panel = ImageManagerPanel(show_header=False, show_caption=False, expand_list=True)
        self._image_panel.image_dropped.connect(self.image_dropped.emit)
        self._image_panel.image_remove_requested.connect(self.image_remove_requested.emit)
        self._image_panel.image_caption_changed.connect(self.image_caption_changed.emit)
        self._image_panel.image_selected.connect(self._on_image_selected)
        self._image_panel.image_edit_requested.connect(self._open_annotation_editor)
        self._image_panel.choose_file_requested.connect(self._on_insert_photo)
        self._image_panel.bosello_picker_requested.connect(self.bosello_picker_requested.emit)

        self._annotation_dialog = ImageAnnotationDialog(self)
        self._annotation_dialog.edits_changed.connect(self._on_annotation_dialog_edits_changed)
        self._annotation_dialog.caption_changed.connect(self.image_caption_changed.emit)
        self._annotation_dialog.photo_navigated.connect(self._on_dialog_photo_navigated)

        self._edit_photo_btn = SecondaryButton("Editar legenda, marcações e crop…")
        self._edit_photo_btn.setEnabled(False)
        self._edit_photo_btn.clicked.connect(lambda: self._open_annotation_editor())

        self._photos_page = QWidget()
        photos_layout = QVBoxLayout(self._photos_page)
        photos_layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        photos_layout.setSpacing(SPACING.sm)
        self._photos_hint = QLabel(
            "Fotos desta seção. Duplo clique na lista ou use o botão abaixo para editar. "
            "No editor: ← → troca de foto."
        )
        self._photos_hint.setWordWrap(True)
        self._photos_hint.setObjectName("SidebarHint")
        self._photos_hint.setStyleSheet(caption_style())
        photos_layout.addWidget(self._photos_hint)
        photos_layout.addWidget(self._image_panel, stretch=1)
        photos_layout.addWidget(self._edit_photo_btn, stretch=0)

        self._graphics_page = QWidget()
        graphics_layout = QVBoxLayout(self._graphics_page)
        graphics_layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        graphics_stub = QLabel("Integração com gráficos Calypso em breve.")
        graphics_stub.setWordWrap(True)
        graphics_stub.setObjectName("SidebarHint")
        graphics_layout.addWidget(graphics_stub)
        graphics_layout.addStretch(1)

        self._tables_page = QWidget()
        self._tables_layout = QVBoxLayout(self._tables_page)
        self._tables_layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        self._tables_layout.setSpacing(SPACING.sm)
        self._tables_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._layout_panel = TemplateLayoutPanel()
        self._layout_panel.kinds_changed.connect(self._on_template_media_kinds_changed)
        self._layout_panel.blocked_action.connect(self._on_layout_blocked)
        self._tabs_builder = SectionTabsBuilder()

        self._delete_btn = SecondaryButton("Excluir seção")
        self._delete_btn.clicked.connect(self._on_delete)
        self._restore_section_btn = SecondaryButton("Restaurar seção inteira")
        self._restore_section_btn.clicked.connect(self._on_restore_section)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        scroll_layout.setSpacing(SPACING.sm)
        scroll_layout.addWidget(self._section_title_host)
        scroll_layout.addWidget(self._fields_host)
        scroll_layout.addWidget(self._restore_section_btn)
        scroll_layout.addWidget(self._delete_btn)
        scroll_layout.addStretch(1)

        self._content_scroll = QScrollArea()
        self._content_scroll.setObjectName("SectionEditorScroll")
        self._content_scroll.setWidgetResizable(True)
        self._content_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._content_scroll.setWidget(scroll_content)

        self._tabs = QTabWidget()
        self._tabs.setObjectName("SectionEditorTabs")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(header)
        outer.addWidget(self._tabs, stretch=1)

    def set_defaults_mode(self, enabled: bool) -> None:
        self._defaults_mode = enabled
        self._form_builder.set_defaults_mode(enabled)
        self._delete_btn.setVisible(not enabled)
        self._restore_section_btn.setVisible(not enabled)
        self._close_btn.setToolTip("Fechar edição" if not enabled else "Voltar ao sumário")

    def reset_breadcrumb(self) -> None:
        self._header_title.setText("EDITAR SEÇÃO")

    def has_pending_textarea(self) -> bool:
        return self._pending_textarea_key is not None or self._debounce.isActive()

    def has_focused_editor(self) -> bool:
        """True se o usuário está digitando em algum PlaceholderTextEdit desta view."""
        if self._section_title_edit.has_editor_focus():
            return True
        if self._image_panel.is_caption_editing():
            return True
        if self._annotation_dialog.is_caption_editing():
            return True
        for widget in self._field_widgets.values():
            if isinstance(widget, PlaceholderTextEdit) and widget.has_editor_focus():
                return True
        return False

    def refresh_appearance(self) -> None:
        self.setStyleSheet(sidebar_panel_style())
        self._close_btn.refresh_appearance()
        self._help_btn.refresh_appearance()
        self._delete_btn.refresh_appearance()
        self._image_panel.refresh_appearance()
        self._edit_photo_btn.refresh_appearance()
        self._annotation_dialog.refresh_appearance()

    def open_section(
        self,
        section_id: str,
        section: dict,
        overrides: dict,
        table_rows: list[dict[str, str]] | None = None,
        itens_medicao: list[dict[str, str]] | None = None,
        version_entries: list[VersionEntry] | None = None,
        locked_media_kinds: list[str] | None = None,
    ) -> None:
        # Interpretação muda de quantidade por PDF — se os campos diferem, reconstrói.
        if (
            self._section_id == section_id
            and self._field_widgets
            and not self._needs_field_rebuild(section_id, overrides)
        ):
            self.patch_section(overrides, table_rows, itens_medicao, section)
            return
        self._loading = True
        scroll_pos = self._content_scroll.verticalScrollBar().value()
        self._section_id = section_id
        self._section_overrides = dict(overrides)
        if version_entries is not None:
            self._version_entries = list(version_entries)
        if locked_media_kinds is not None:
            self._locked_media_kinds = list(locked_media_kinds)
        # Limpa fotos da seção anterior até o painel reaplicar o filtro.
        self._image_panel.render_images([])
        is_custom = section.get("custom", False) or section_id.startswith("custom_")
        self._delete_btn.setVisible(is_custom and not self._defaults_mode)
        self._restore_section_btn.setVisible(not is_custom and not self._defaults_mode)

        self._rebuild_section_title(section_id, overrides)
        self._rebuild_table_rows(section_id, table_rows or [])
        self._rebuild_fields(section_id, overrides, is_custom)
        self._rebuild_editor_tabs(section_id)
        self._update_photos_hint(section)

        if section_id == "resultados" and itens_medicao is not None:
            self._medicoes_editor.set_rows(itens_medicao)
        self._loading = False
        self._content_scroll.verticalScrollBar().setValue(scroll_pos)
        self._update_breadcrumb(section)

    def _needs_field_rebuild(self, section_id: str, overrides: dict) -> bool:
        if section_id == "interpretacao":
            expected = {f.key for f in interpretacao_field_defs(overrides)}
            current = set(self._field_widgets.keys())
            return expected != current
        return False

    def patch_section(
        self,
        overrides: dict,
        table_rows: list[dict[str, str]] | None = None,
        itens_medicao: list[dict[str, str]] | None = None,
        section: dict | None = None,
    ) -> None:
        if self._section_id is None:
            return
        if self._needs_field_rebuild(self._section_id, overrides):
            self.open_section(
                self._section_id,
                section or {"id": self._section_id},
                overrides,
                table_rows,
                itens_medicao,
            )
            return
        self._loading = True
        scroll_pos = self._content_scroll.verticalScrollBar().value()
        section_id = self._section_id
        self._section_overrides = dict(overrides)

        default = SECTION_HEADING_DEFAULTS.get(section_id, overrides.get("title", section_id))
        self._section_title_edit.set_text(overrides.get("section_title", default))

        defaults = default_field_values(section_id)
        for key, widget in self._field_widgets.items():
            if key.startswith("title_"):
                value = overrides.get(key, INTRODUCAO_BLOCK_TITLES.get(key, ""))
            else:
                value = overrides.get(key, defaults.get(key, ""))
            if isinstance(widget, PlaceholderTextEdit):
                widget.set_text(value)
            elif isinstance(widget, QLineEdit):
                widget.setText(value)

        if (section_id in TABLE_SECTIONS or is_custom_section_id(section_id)) and table_rows is not None:
            self._table_rows_editor.set_rows(table_rows)
        if section_id == "resultados" and itens_medicao is not None:
            self._medicoes_editor.set_rows(itens_medicao)

        if section is not None:
            self._update_breadcrumb(section)
        self._loading = False
        self._content_scroll.verticalScrollBar().setValue(scroll_pos)

    def _update_breadcrumb(self, section: dict) -> None:
        # Cabeçalho compacto — o título longo é editável na aba Conteúdo.
        _ = section
        self._header_title.setText("EDITAR SEÇÃO")

    def set_itens_medicao(self, rows: list[dict[str, str]]) -> None:
        if self._section_id == "resultados":
            self._medicoes_editor.set_rows(rows)

    def _rebuild_section_title(self, section_id: str, overrides: dict) -> None:
        default = SECTION_HEADING_DEFAULTS.get(section_id, overrides.get("title", section_id))
        self._section_title_edit.set_text(overrides.get("section_title", default))

    def _rebuild_table_rows(self, section_id: str, rows: list[dict[str, str]]) -> None:
        if section_id not in TABLE_SECTIONS and not is_custom_section_id(section_id):
            return
        self._table_rows_editor.set_rows(rows)

    def set_locked_media_kinds(self, kinds: list[str]) -> None:
        self._locked_media_kinds = list(kinds)
        if self._section_id is not None:
            self._rebuild_editor_tabs(self._section_id)

    def set_version_entries(self, entries: list[VersionEntry]) -> None:
        self._version_entries = list(entries)
        if self._section_id == "historico_versoes" and not self._defaults_mode:
            self._field_widgets = self._form_builder.rebuild(
                self._section_id,
                self._section_overrides,
                False,
                version_entries=self._version_entries,
            )

    def _rebuild_fields(self, section_id: str, overrides: dict, is_custom: bool) -> None:
        self._field_widgets = self._form_builder.rebuild(
            section_id,
            overrides,
            is_custom,
            version_entries=self._version_entries,
        )

    def _rebuild_editor_tabs(self, section_id: str) -> None:
        self._tabs_builder.rebuild(
            self._tabs,
            section_id=section_id,
            section_overrides=self._section_overrides,
            defaults_mode=self._defaults_mode,
            pages=SectionTabPages(
                content_scroll=self._content_scroll,
                layout_panel=self._layout_panel,
                photos_page=self._photos_page,
                graphics_page=self._graphics_page,
                tables_page=self._tables_page,
                tables_layout=self._tables_layout,
                table_rows_editor=self._table_rows_editor,
                medicoes_editor=self._medicoes_editor,
            ),
            locked_media_kinds=self._locked_media_kinds,
        )

    def _current_overrides(self) -> dict:
        if self._section_id is None:
            return {}
        values: dict = {}
        if self._section_id:
            default = SECTION_HEADING_DEFAULTS.get(self._section_id, "")
            values["section_title"] = self._section_title_edit.get_text()
        for key, widget in self._field_widgets.items():
            if isinstance(widget, PlaceholderTextEdit):
                values[key] = widget.get_text()
            elif isinstance(widget, QLineEdit):
                values[key] = widget.text()
        return values

    def _on_layout_blocked(self, message: str) -> None:
        self._layout_panel.show_blocked_notice(message)

    def _on_template_media_kinds_changed(self, kinds: list[str]) -> None:
        if self._section_id is None:
            return
        if self._defaults_mode and self._section_id in TABLE_SECTIONS:
            if "tables" in kinds:
                self._layout_panel.set_table_widget(self._table_rows_editor)
            else:
                self._layout_panel.set_table_widget(None)
        if not self._defaults_mode:
            removed_locked = set(self._locked_media_kinds) - set(kinds)
            if removed_locked:
                self._layout_panel.show_blocked_notice(
                    "Este bloco faz parte do layout padrão da seção e não pode ser desativado aqui. "
                    "Para um relatório diferente, crie uma seção personalizada."
                )
                kinds = list(dict.fromkeys([*self._locked_media_kinds, *kinds]))
        self.media_kinds_changed.emit(self._section_id, kinds)
        if not self._defaults_mode:
            merged = list(dict.fromkeys([*self._locked_media_kinds, *kinds]))
            self._section_overrides = dict(self._section_overrides)
            self._section_overrides["media_kinds"] = merged
            self._rebuild_editor_tabs(self._section_id)

    def _on_insert_photo(self) -> None:
        from PyQt6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Inserir fotografia",
            "",
            "Imagens (*.png *.jpg *.jpeg)",
        )
        if path:
            self.image_dropped.emit(Path(path))

    def _show_help(self) -> None:
        section_id = self._section_id or ""
        blocks = get_media_blocks(section_id)
        text = build_help_text(
            section_id,
            has_table=any(b.kind == "tables" for b in blocks),
            has_media=any(b.kind in ("photos", "graphics") for b in blocks),
        )
        dlg = QDialog(self)
        dlg.setWindowTitle("Ajuda — edição de seção")
        dlg.setMinimumWidth(420)
        body = QTextEdit()
        body.setReadOnly(True)
        body.setMarkdown(text)
        layout = QVBoxLayout(dlg)
        layout.addWidget(body)
        close = SecondaryButton("Fechar")
        close.clicked.connect(dlg.accept)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(close)
        layout.addLayout(row)
        dlg.exec()

    def current_section_id(self) -> str | None:
        return self._section_id

    def focus_tab_for_kind(self, kind: str) -> None:
        targets = {
            "content": self._content_scroll,
            "layout": self._layout_panel,
            "photos": self._photos_page,
            "graphics": self._graphics_page,
            "tables": self._tables_page,
        }
        widget = targets.get(kind)
        if widget is None:
            return
        index = self._tabs.indexOf(widget)
        if index >= 0:
            self._tabs.setCurrentIndex(index)

    def focus_section_title(self) -> None:
        """Foca o campo editável do título na aba Conteúdo."""
        content_index = self._tabs.indexOf(self._content_scroll)
        if content_index >= 0:
            self._tabs.setCurrentIndex(content_index)
        QTimer.singleShot(80, self._focus_section_title_editor)

    def _focus_section_title_editor(self) -> None:
        self._content_scroll.ensureWidgetVisible(self._section_title_host, 0, 40)
        self._section_title_edit.focus_editor(select_all=True)

    def _update_photos_hint(self, section: dict | None = None) -> None:
        title = ""
        if section:
            title = section.get("display_title") or section.get("title") or ""
        if title:
            self._photos_hint.setText(
                f"Fotos desta seção ({title}). Duplo clique na lista ou use o botão abaixo. "
                "No editor: ← → troca de foto."
            )
        else:
            self._photos_hint.setText(
                "Fotos desta seção. Duplo clique na lista ou use o botão abaixo para editar. "
                "No editor: ← → troca de foto."
            )

    def render_images(self, images: list[ReportImage]) -> None:
        section_id = self._section_id
        if section_id is None:
            self._image_panel.render_images([])
            self._image_panel.set_bosello_captures_available(False)
            return
        filtered = [img for img in images if img.section_id == section_id]
        self._section_images = filtered
        self._image_panel.render_images(filtered)

    def set_bosello_captures_available(self, available: bool) -> None:
        self._image_panel.set_bosello_captures_available(available)

    def _on_image_selected(self, image: ReportImage | None) -> None:
        self._active_image = image
        self._edit_photo_btn.setEnabled(image is not None)
        self.image_selected.emit(image)

    def _open_annotation_editor(self, image: ReportImage | None = None) -> None:
        target = image if image is not None else self._image_panel.selected_image()
        if target is None:
            return
        self._annotation_dialog.open_for(target, gallery=self._section_images)

    def _on_dialog_photo_navigated(self, image: ReportImage) -> None:
        self._image_panel.select_image_by_path(str(image.image_path))

    def _on_annotation_dialog_edits_changed(self, image: ReportImage) -> None:
        self.image_edits_changed.emit(image)

    def _on_section_title_changed(self, text: str) -> None:
        if self._loading or self._section_id is None:
            return
        self.section_field_changed.emit(self._section_id, "section_title", text)

    def _on_field_changed(self, key: str, text: str) -> None:
        if self._loading or self._section_id is None or not key:
            return
        textarea_keys = {f.key for f in get_edit_fields(self._section_id) if f.field_type == "textarea"}
        if key in textarea_keys:
            self._pending_textarea_key = key
            self._debounce.start()
        else:
            self.section_field_changed.emit(self._section_id, key, text)

    def _on_line_finished(self, key: str, widget: QLineEdit) -> None:
        if self._loading or self._section_id is None:
            return
        self.section_field_changed.emit(self._section_id, key, widget.text())

    def _flush_textarea_pending(self) -> None:
        if self._section_id is None or self._pending_textarea_key is None:
            return
        key = self._pending_textarea_key
        widget = self._field_widgets.get(key)
        if isinstance(widget, PlaceholderTextEdit):
            self.section_field_changed.emit(self._section_id, key, widget.get_text())

    def _on_table_rows_changed(self, rows: list) -> None:
        if self._loading or self._section_id is None:
            return
        self.table_rows_changed.emit(self._section_id, rows)

    def _on_table_rows_restore(self) -> None:
        if self._section_id is not None:
            self.table_rows_restore_requested.emit(self._section_id)

    def _on_restore_section(self) -> None:
        if self._section_id is not None:
            self.section_restore_requested.emit(self._section_id)

    def _on_delete(self) -> None:
        if self._section_id is not None:
            self.delete_requested.emit(self._section_id)
