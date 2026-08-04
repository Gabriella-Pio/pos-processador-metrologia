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
    INTRODUCAO_CONTENT_BLOCKS,
    INTRODUCAO_HEADER_ONLY_BLOCKS,
    effective_media_kinds,
    get_edit_fields,
    get_media_blocks,
)
from src.core.domain.ports import ReportImage
from src.core.domain.table_row_registry import INTRODUCAO_BLOCK_TITLES, SECTION_HEADING_DEFAULTS
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


class _IntroBlockCard(QFrame):
    restore_requested = pyqtSignal(str, str)

    def __init__(
        self,
        label: str,
        title_key: str,
        body_key: str | None,
        title_value: str,
        body_value: str,
        show_restore: bool = True,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("GlobalFieldCard")
        self.title_key = title_key
        self.body_key = body_key

        title_lbl = QLabel(label)
        title_lbl.setObjectName("GlobalFieldLabel")

        header = QHBoxLayout()
        header.addWidget(title_lbl, stretch=1)
        if show_restore:
            restore = QLabel('<a href="restore">Restaurar</a>')
            restore.setObjectName("FieldRestoreLink")
            restore.setTextFormat(Qt.TextFormat.RichText)
            restore.setOpenExternalLinks(False)
            restore.linkActivated.connect(
                lambda _href: self.restore_requested.emit(self.title_key, self.body_key or "")
            )
            header.addWidget(restore, alignment=Qt.AlignmentFlag.AlignRight)

        self._title_edit = PlaceholderTextEdit(multiline=False)
        self._title_edit.set_text(title_value)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        layout.setSpacing(SPACING.xs)
        layout.addLayout(header)
        layout.addWidget(self._title_edit)
        if body_key:
            self._body_edit = PlaceholderTextEdit(multiline=True)
            self._body_edit.set_text(body_value)
            layout.addWidget(self._body_edit)
        else:
            self._body_edit = None

    def connect_signals(self, on_title, on_body) -> None:
        self._title_edit.text_changed.connect(on_title)
        if self._body_edit is not None and on_body is not None:
            self._body_edit.text_changed.connect(on_body)


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
    section_block_restore_requested = pyqtSignal(str, str, str)
    table_rows_changed = pyqtSignal(str, list)
    table_rows_restore_requested = pyqtSignal(str)
    itens_medicao_changed = pyqtSignal(list)
    itens_medicao_restore_requested = pyqtSignal()
    image_dropped = pyqtSignal(Path)
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
        section_title_header = QLabel("Título da seção (como no preview)")
        section_title_header.setObjectName("GlobalFieldLabel")
        title_card = QFrame()
        title_card.setObjectName("GlobalFieldCard")
        title_card_layout = QVBoxLayout(title_card)
        title_card_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        title_card_layout.setSpacing(SPACING.xs)
        title_card_layout.addWidget(section_title_header)
        title_card_layout.addWidget(self._section_title_edit)
        self._section_title_host = title_card

        self._intro_blocks_host = QWidget()
        self._intro_blocks_layout = QVBoxLayout(self._intro_blocks_host)
        self._intro_blocks_layout.setContentsMargins(0, 0, 0, 0)
        self._intro_blocks_layout.setSpacing(SPACING.sm)

        self._table_rows_editor = DraggableTableRowsEditor("Linhas da tabela (como no preview)")
        self._table_rows_editor.rows_changed.connect(self._on_table_rows_changed)
        self._table_rows_editor.restore_requested.connect(self._on_table_rows_restore)

        self._fields_host = QWidget()
        self._fields_layout = QVBoxLayout(self._fields_host)
        self._fields_layout.setContentsMargins(0, 0, 0, 0)
        self._fields_layout.setSpacing(SPACING.sm)

        self._medicoes_editor = MedicoesTableEditor()
        self._medicoes_editor.rows_changed.connect(self.itens_medicao_changed.emit)
        self._medicoes_editor.restore_requested.connect(self.itens_medicao_restore_requested.emit)

        self._image_panel = ImageManagerPanel()
        self._image_panel.image_dropped.connect(self.image_dropped.emit)
        self._annotation_toolbar = AnnotationToolbar()
        self._annotation_toolbar.tool_selected.connect(self.tool_selected.emit)

        self._insert_photo_btn = SecondaryButton("+ Inserir foto")
        self._insert_photo_btn.clicked.connect(self._on_insert_photo)

        self._photos_page = QWidget()
        photos_layout = QVBoxLayout(self._photos_page)
        photos_layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        photos_layout.setSpacing(SPACING.sm)
        photos_layout.addWidget(self._annotation_toolbar)
        photos_layout.addWidget(self._insert_photo_btn)
        photos_layout.addWidget(self._image_panel, stretch=1)

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
        scroll_layout.addWidget(self._intro_blocks_host)
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

    def refresh_appearance(self) -> None:
        self.setStyleSheet(sidebar_panel_style())
        self._close_btn.refresh_appearance()
        self._help_btn.refresh_appearance()
        self._delete_btn.refresh_appearance()
        self._insert_photo_btn.refresh_appearance()
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
        if self._section_id == section_id and self._field_widgets:
            self.patch_section(overrides, table_rows, itens_medicao, section)
            return
        self._loading = True
        scroll_pos = self._content_scroll.verticalScrollBar().value()
        self._section_id = section_id
        self._section_overrides = dict(overrides)
        is_custom = section.get("custom", False) or section_id.startswith("custom_")
        self._delete_btn.setVisible(is_custom and not self._defaults_mode)
        self._restore_section_btn.setVisible(not is_custom and not self._defaults_mode)

        self._rebuild_section_title(section_id, overrides)
        self._rebuild_intro_blocks(section_id, overrides)
        self._rebuild_table_rows(section_id, table_rows or [])
        self._rebuild_fields(section_id, overrides, is_custom)
        self._rebuild_editor_tabs(section_id)

        if section_id == "resultados" and itens_medicao is not None:
            self._medicoes_editor.set_rows(itens_medicao)
        self._loading = False
        self._content_scroll.verticalScrollBar().setValue(scroll_pos)
        self._update_breadcrumb(section)

    def patch_section(
        self,
        overrides: dict,
        table_rows: list[dict[str, str]] | None = None,
        itens_medicao: list[dict[str, str]] | None = None,
        section: dict | None = None,
    ) -> None:
        if self._section_id is None:
            return
        self._loading = True
        scroll_pos = self._content_scroll.verticalScrollBar().value()
        section_id = self._section_id
        self._section_overrides = dict(overrides)

        default = SECTION_HEADING_DEFAULTS.get(section_id, overrides.get("title", section_id))
        self._section_title_edit.set_text(overrides.get("section_title", default))

        if section_id == "introducao":
            for block in INTRODUCAO_CONTENT_BLOCKS + INTRODUCAO_HEADER_ONLY_BLOCKS:
                widget = self._field_widgets.get(block.title_key)
                if isinstance(widget, PlaceholderTextEdit):
                    title_default = INTRODUCAO_BLOCK_TITLES.get(block.title_key, block.label.upper())
                    widget.set_text(overrides.get(block.title_key, title_default))
                if block.body_key:
                    body_widget = self._field_widgets.get(block.body_key)
                    if isinstance(body_widget, PlaceholderTextEdit):
                        defaults = default_field_values("introducao")
                        body_widget.set_text(
                            overrides.get(block.body_key, defaults.get(block.body_key, ""))
                        )
        else:
            defaults = default_field_values(section_id)
            for key, widget in self._field_widgets.items():
                value = overrides.get(key, defaults.get(key, ""))
                if isinstance(widget, PlaceholderTextEdit):
                    widget.set_text(value)
                elif isinstance(widget, QLineEdit):
                    widget.setText(value)

        if section_id == "identificacao" and table_rows is not None:
            self._table_rows_editor.set_rows(table_rows)
        if section_id == "resultados" and itens_medicao is not None:
            self._medicoes_editor.set_rows(itens_medicao)

        if section is not None:
            self._update_breadcrumb(section)
        self._loading = False
        self._content_scroll.verticalScrollBar().setValue(scroll_pos)

    def _update_breadcrumb(self, section: dict) -> None:
        title = section.get("display_title") or section.get("title", self._section_id or "")
        self._header_title.setText(title)

    def set_itens_medicao(self, rows: list[dict[str, str]]) -> None:
        if self._section_id == "resultados":
            self._medicoes_editor.set_rows(rows)

    def _rebuild_section_title(self, section_id: str, overrides: dict) -> None:
        default = SECTION_HEADING_DEFAULTS.get(section_id, overrides.get("title", section_id))
        self._section_title_edit.set_text(overrides.get("section_title", default))

    def _rebuild_intro_blocks(self, section_id: str, overrides: dict) -> None:
        while self._intro_blocks_layout.count():
            item = self._intro_blocks_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._field_widgets.clear()

        if section_id != "introducao":
            self._intro_blocks_host.setVisible(False)
            return
        self._intro_blocks_host.setVisible(True)

        defaults = default_field_values("introducao")
        for block in INTRODUCAO_CONTENT_BLOCKS + INTRODUCAO_HEADER_ONLY_BLOCKS:
            title_default = INTRODUCAO_BLOCK_TITLES.get(block.title_key, block.label.upper())
            body_default = defaults.get(block.body_key, "") if block.body_key else ""
            card = _IntroBlockCard(
                block.label,
                block.title_key,
                block.body_key,
                overrides.get(block.title_key, title_default),
                overrides.get(block.body_key, body_default) if block.body_key else "",
                show_restore=not self._defaults_mode,
            )
            if not self._defaults_mode:
                card.restore_requested.connect(self._on_block_restore)
            body_key = block.body_key
            card.connect_signals(
                lambda text, k=block.title_key: self._on_field_changed(k, text),
                (lambda text, k=body_key: self._on_field_changed(k, text)) if body_key else None,
            )
            if body_key:
                self._field_widgets[body_key] = card._body_edit  # type: ignore[assignment]
            self._field_widgets[block.title_key] = card._title_edit
            self._intro_blocks_layout.addWidget(card)

    def _rebuild_table_rows(self, section_id: str, rows: list[dict[str, str]]) -> None:
        if section_id != "identificacao":
            return
        self._table_rows_editor.set_rows(rows)

    def _rebuild_fields(self, section_id: str, overrides: dict, is_custom: bool) -> None:
        while self._fields_layout.count():
            item = self._fields_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if section_id == "introducao":
            self._fields_host.setVisible(False)
            return

        fields = list(get_edit_fields(section_id, defaults_mode=self._defaults_mode))
        if not self._defaults_mode:
            fields = [f for f in fields if f.editable]
        if not fields:
            self._fields_host.setVisible(False)
            return
        self._fields_host.setVisible(True)

        prose_header = QLabel("Texto desta seção")
        prose_header.setObjectName("GlobalFieldLabel")
        self._fields_layout.addWidget(prose_header)

        defaults = default_field_values(section_id)
        for field_def in fields:
            card = QFrame()
            card.setObjectName("GlobalFieldCard")
            row_layout = QVBoxLayout(card)
            row_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
            row_layout.setSpacing(SPACING.xs)

            header = QHBoxLayout()
            label = QLabel(field_def.label)
            label.setObjectName("GlobalFieldLabel")
            header.addWidget(label, stretch=1)
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

            value = overrides.get(field_def.key, defaults.get(field_def.key, ""))
            if is_custom and field_def.field_type != "textarea":
                widget: PlaceholderTextEdit | QLineEdit = QLineEdit()
                widget.setObjectName("GlobalFieldInput")
                widget.setMinimumHeight(36)
                widget.setText(value)
                widget.editingFinished.connect(
                    lambda k=field_def.key, w=widget: self._on_line_finished(k, w)
                )
            elif is_custom:
                widget = PlaceholderTextEdit(multiline=True)
                widget.set_text(value)
                widget.text_changed.connect(
                    lambda text, k=field_def.key: self._on_field_changed(k, text)
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
            if section_id == "identificacao" and "tables" in self._layout_panel.current_kinds():
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
                if section_id == "identificacao":
                    self._tables_layout.addWidget(self._table_rows_editor)
                else:
                    self._tables_layout.addWidget(self._medicoes_editor)
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
        if self._section_id == "identificacao":
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

    def render_images(self, images: list[ReportImage]) -> None:
        section_id = self._section_id
        if section_id is None:
            self._image_panel.render_images([])
            return
        filtered = [img for img in images if img.section_id == section_id]
        self._image_panel.render_images(filtered)

    def _on_section_title_changed(self, text: str) -> None:
        if self._loading or self._section_id is None:
            return
        self.section_field_changed.emit(self._section_id, "section_title", text)

    def _on_field_changed(self, key: str, text: str) -> None:
        if self._loading or self._section_id is None or not key:
            return
        textarea_keys = {f.key for f in get_edit_fields(self._section_id) if f.field_type == "textarea"}
        textarea_keys |= {"objetivo", "escopo", "referencia"}
        if key in textarea_keys:
            self._pending_textarea_key = key
            self._debounce.start()
        else:
            self.section_field_changed.emit(self._section_id, key, text)

    def _on_block_restore(self, title_key: str, body_key: str) -> None:
        if self._section_id is None:
            return
        self.section_block_restore_requested.emit(self._section_id, title_key, body_key)

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
