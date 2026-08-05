"""Formulário de edição de seção — título, blocos agrupados, mídia e placeholders."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
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

from src.core.domain.report_field_registry import (
    INTRODUCAO_BODY_TITLE_KEYS,
    SectionFieldDef,
    effective_media_kinds,
    get_edit_fields,
    get_media_blocks,
)
from src.core.application.interpretacao_edit import interpretacao_field_defs
from src.core.domain.ports import ReportImage
from src.core.domain.table_row_registry import (
    INTRODUCAO_BLOCK_TITLES,
    SECTION_HEADING_DEFAULTS,
    TABLE_SECTIONS,
)
from src.ui.components.buttons import IconButton, SecondaryButton
from src.ui.components.icons import icon_chart, icon_close, icon_edit, icon_help, icon_image, icon_table
from src.ui.components.panels import AnnotationToolbar, ImageManagerPanel
from src.ui.components.placeholder_field import PlaceholderTextEdit
from src.ui.shared.report_editor.sidebar_chrome import editor_panel_header
from src.ui.styles import SPACING, caption_style, sidebar_panel_style
from src.ui.features.workspace.components.draggable_table_rows_editor import DraggableTableRowsEditor
from src.ui.features.workspace.components.edit_help import build_help_text
from src.ui.features.workspace.components.medicoes_table_editor import MedicoesTableEditor
from src.ui.features.workspace.components.section_field_schema import (
    default_field_values,
)


class _TemplateLayoutPanel(QFrame):
    """Configuração de layout — fotos, gráficos e tabelas no template."""

    kinds_changed = pyqtSignal(list)

    _OPTIONS = (
        ("photos", "Fotografias", "Reserva espaço para imagens nesta seção do PDF."),
        ("graphics", "Gráficos", "Reserva espaço para gráficos analíticos."),
        ("tables", "Tabela", "Inclui bloco de tabela nesta seção."),
    )

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._checkboxes: dict[str, QCheckBox] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        layout.setSpacing(SPACING.sm)

        hint = QLabel(
            "Marque os blocos que esta seção deve reservar no relatório. "
            "No workspace, o usuário preenche fotos, gráficos e dados reais."
        )
        hint.setWordWrap(True)
        hint.setObjectName("SidebarHint")
        hint.setStyleSheet(caption_style())
        layout.addWidget(hint)

        for kind, label, tooltip in self._OPTIONS:
            card = QFrame()
            card.setObjectName("GlobalFieldCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
            card_layout.setSpacing(SPACING.xs)
            cb = QCheckBox(label)
            cb.setToolTip(tooltip)
            cb.stateChanged.connect(self._emit_kinds)
            card_layout.addWidget(cb)
            self._checkboxes[kind] = cb
            layout.addWidget(card)

        self._tables_host = QWidget()
        self._tables_host_layout = QVBoxLayout(self._tables_host)
        self._tables_host_layout.setContentsMargins(0, 0, 0, 0)
        self._tables_host_layout.setSpacing(SPACING.sm)
        self._tables_host.setVisible(False)
        layout.addWidget(self._tables_host)
        layout.addStretch(1)

    def set_table_widget(self, widget: QWidget | None) -> None:
        while self._tables_host_layout.count():
            item = self._tables_host_layout.takeAt(0)
            child = item.widget()
            if child is not None:
                child.setParent(None)
        if widget is not None:
            self._tables_host_layout.addWidget(widget)
            self._tables_host.setVisible(True)
        else:
            self._tables_host.setVisible(False)

    def set_kinds(self, kinds: list[str]) -> None:
        active = set(kinds)
        for kind, cb in self._checkboxes.items():
            cb.blockSignals(True)
            cb.setChecked(kind in active)
            cb.blockSignals(False)

    def current_kinds(self) -> list[str]:
        return [kind for kind, cb in self._checkboxes.items() if cb.isChecked()]

    def _emit_kinds(self, *_args) -> None:
        self.kinds_changed.emit(self.current_kinds())


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
    tool_selected = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    section_restore_requested = pyqtSignal(str)
    media_kinds_changed = pyqtSignal(str, list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("WorkspaceEditorView")
        self._section_id: str | None = None
        self._loading = False
        self._defaults_mode = False
        self._section_overrides: dict = {}
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

        self._medicoes_editor = MedicoesTableEditor()
        self._medicoes_editor.rows_changed.connect(self.itens_medicao_changed.emit)
        self._medicoes_editor.restore_requested.connect(self.itens_medicao_restore_requested.emit)

        self._active_image: ReportImage | None = None
        self._image_panel = ImageManagerPanel(show_header=False)
        self._image_panel.image_dropped.connect(self.image_dropped.emit)
        self._image_panel.image_remove_requested.connect(self.image_remove_requested.emit)
        self._image_panel.image_caption_changed.connect(self.image_caption_changed.emit)
        self._image_panel.image_selected.connect(self._on_image_selected)
        self._image_panel.choose_file_requested.connect(self._on_insert_photo)
        self._annotation_toolbar = AnnotationToolbar()
        self._annotation_toolbar.tool_selected.connect(self.tool_selected.emit)

        self._photos_page = QWidget()
        photos_layout = QVBoxLayout(self._photos_page)
        photos_layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        photos_layout.setSpacing(SPACING.sm)
        self._photos_hint = QLabel(
            "Fotos só desta seção. Selecione uma para editar a legenda. "
            "Várias fotos aparecem lado a lado no PDF."
        )
        self._photos_hint.setWordWrap(True)
        self._photos_hint.setObjectName("SidebarHint")
        self._photos_hint.setStyleSheet(caption_style())
        photos_layout.addWidget(self._photos_hint)
        photos_layout.addWidget(self._image_panel, stretch=1)
        photos_layout.addWidget(self._annotation_toolbar)

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

        self._layout_panel = _TemplateLayoutPanel()
        self._layout_panel.kinds_changed.connect(self._on_template_media_kinds_changed)

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
        self._annotation_toolbar.refresh_appearance()

    def open_section(
        self,
        section_id: str,
        section: dict,
        overrides: dict,
        table_rows: list[dict[str, str]] | None = None,
        itens_medicao: list[dict[str, str]] | None = None,
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

        if section_id in TABLE_SECTIONS and table_rows is not None:
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
        if section_id not in TABLE_SECTIONS:
            return
        self._table_rows_editor.set_rows(rows)

    def _rebuild_fields(self, section_id: str, overrides: dict, is_custom: bool) -> None:
        while self._fields_layout.count():
            item = self._fields_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._field_widgets.clear()

        if section_id == "interpretacao":
            fields = list(interpretacao_field_defs(overrides))
        else:
            fields = list(get_edit_fields(section_id, defaults_mode=self._defaults_mode))
            if not self._defaults_mode:
                fields = [f for f in fields if f.editable]
        if not fields:
            self._fields_host.setVisible(False)
            return
        self._fields_host.setVisible(True)

        prose_header = QLabel("Blocos de texto")
        prose_header.setObjectName("GlobalFieldLabel")
        self._fields_layout.addWidget(prose_header)
        if section_id == "introducao":
            prose_hint = QLabel(
                "O título (ex.: OBJETIVO) e o texto de cada bloco aparecem no preview/PDF."
            )
            prose_hint.setWordWrap(True)
            prose_hint.setObjectName("SidebarHint")
            prose_hint.setStyleSheet(caption_style())
            self._fields_layout.addWidget(prose_hint)

        defaults = default_field_values(section_id)
        for field_def in fields:
            card = QFrame()
            card.setObjectName("GlobalFieldCard")
            row_layout = QVBoxLayout(card)
            row_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
            row_layout.setSpacing(SPACING.xs)

            title_key = INTRODUCAO_BODY_TITLE_KEYS.get(field_def.key) if section_id == "introducao" else None

            header = QHBoxLayout()
            if title_key is None:
                label = QLabel(field_def.label)
                label.setObjectName("GlobalFieldLabel")
                header.addWidget(label, stretch=1)
            else:
                title_caption = QLabel("Título no PDF")
                title_caption.setObjectName("GlobalFieldLabel")
                header.addWidget(title_caption, stretch=1)
            if not self._defaults_mode:
                restore = QLabel('<a href="restore">Restaurar</a>')
                restore.setObjectName("FieldRestoreLink")
                restore.setTextFormat(Qt.TextFormat.RichText)
                restore.setOpenExternalLinks(False)
                fkey = field_def.key
                restore.linkActivated.connect(
                    lambda _href, sid=section_id, k=fkey: self.section_field_restore_requested.emit(sid, k)
                )
                header.addWidget(restore, alignment=Qt.AlignmentFlag.AlignRight)
            row_layout.addLayout(header)

            if title_key is not None:
                title_default = INTRODUCAO_BLOCK_TITLES.get(title_key, field_def.label.upper())
                title_edit = PlaceholderTextEdit(multiline=False)
                title_edit.set_text(str(overrides.get(title_key, title_default)))
                title_edit.text_changed.connect(
                    lambda text, k=title_key: self._on_field_changed(k, text)
                )
                row_layout.addWidget(title_edit)
                self._field_widgets[title_key] = title_edit
                body_caption = QLabel("Texto")
                body_caption.setObjectName("GlobalFieldLabel")
                row_layout.addWidget(body_caption)

            value = overrides.get(field_def.key, defaults.get(field_def.key, ""))
            if is_custom and field_def.field_type != "textarea":
                widget: PlaceholderTextEdit | QLineEdit = QLineEdit()
                widget.setObjectName("GlobalFieldInput")
                widget.setMinimumHeight(36)
                widget.setText(value)
                widget.editingFinished.connect(
                    lambda k=field_def.key, w=widget: self._on_line_finished(k, w)
                )
            else:
                widget = PlaceholderTextEdit(multiline=field_def.field_type == "textarea")
                widget.set_text(value)
                widget.text_changed.connect(
                    lambda text, k=field_def.key: self._on_field_changed(k, text)
                )
            row_layout.addWidget(widget)
            self._fields_layout.addWidget(card)
            self._field_widgets[field_def.key] = widget

    def _rebuild_editor_tabs(self, section_id: str) -> None:
        while self._tabs.count():
            self._tabs.removeTab(0)

        self._tabs.addTab(self._content_scroll, "Conteúdo")
        self._tabs.setTabIcon(0, icon_edit())

        if self._defaults_mode:
            self._layout_panel.set_kinds(
                effective_media_kinds(section_id, self._section_overrides)
            )
            if section_id in TABLE_SECTIONS and "tables" in self._layout_panel.current_kinds():
                self._layout_panel.set_table_widget(self._table_rows_editor)
            else:
                self._layout_panel.set_table_widget(None)
            layout_index = self._tabs.addTab(self._layout_panel, "Layout")
            self._tabs.setTabIcon(layout_index, icon_image())
            self._tabs.tabBar().setVisible(True)
            return

        media_blocks = get_media_blocks(
            section_id,
            effective_media_kinds(section_id, self._section_overrides),
        )
        tab_defs: list[tuple[str, str, QWidget]] = []
        for media in media_blocks:
            if media.kind == "photos":
                tab_defs.append(("photos", "Fotografias", self._photos_page))
            elif media.kind == "graphics":
                tab_defs.append(("graphics", "Gráficos", self._graphics_page))
            elif media.kind == "tables":
                while self._tables_layout.count():
                    item = self._tables_layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.setParent(None)
                if section_id in TABLE_SECTIONS:
                    self._tables_layout.addWidget(self._table_rows_editor, 0)
                else:
                    self._tables_layout.addWidget(self._medicoes_editor, 0)
                self._tables_layout.addStretch(1)
                tab_defs.append(("tables", "Tabela", self._tables_page))

        icons = {"photos": icon_image, "graphics": icon_chart, "tables": icon_table}
        labels = {"photos": "Fotografias", "graphics": "Gráficos", "tables": "Tabela"}
        seen: set[str] = set()
        for kind, _label, page in tab_defs:
            if kind in seen:
                continue
            seen.add(kind)
            index = self._tabs.addTab(page, labels.get(kind, kind))
            self._tabs.setTabIcon(index, icons[kind]())

        has_photos = any(b.kind == "photos" for b in media_blocks)
        self._annotation_toolbar.setVisible(has_photos)
        self._tabs.tabBar().setVisible(self._tabs.count() > 1)

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

    def _on_template_media_kinds_changed(self, kinds: list[str]) -> None:
        if self._section_id is None:
            return
        if self._section_id in TABLE_SECTIONS:
            if "tables" in kinds:
                self._layout_panel.set_table_widget(self._table_rows_editor)
            else:
                self._layout_panel.set_table_widget(None)
        self.media_kinds_changed.emit(self._section_id, kinds)

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

    def _update_photos_hint(self, section: dict | None = None) -> None:
        title = ""
        if section:
            title = section.get("display_title") or section.get("title") or ""
        if title:
            self._photos_hint.setText(
                f"Fotos só desta seção ({title}). "
                "Não aparecem nas outras seções. Selecione uma para editar a legenda."
            )
        else:
            self._photos_hint.setText(
                "Fotos só desta seção. Selecione uma para editar a legenda. "
                "Várias fotos aparecem lado a lado no PDF."
            )

    def render_images(self, images: list[ReportImage]) -> None:
        section_id = self._section_id
        if section_id is None:
            self._image_panel.render_images([])
            return
        filtered = [img for img in images if img.section_id == section_id]
        self._image_panel.render_images(filtered)

    def _on_image_selected(self, image: ReportImage | None) -> None:
        self._active_image = image
        self._annotation_toolbar.set_tools_enabled(image is not None)
        self.image_selected.emit(image)

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
