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
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.core.domain.ports import ReportImage
from src.core.domain.report_field_registry import (
    INTRODUCAO_CONTENT_BLOCKS,
    INTRODUCAO_HEADER_ONLY_BLOCKS,
)
from src.core.domain.table_row_registry import INTRODUCAO_BLOCK_TITLES, SECTION_HEADING_DEFAULTS
from src.ui.components.buttons import SecondaryButton
from src.ui.components.icons import icon_chart, icon_image, icon_table
from src.ui.components.panels import AnnotationToolbar, ImageManagerPanel
from src.ui.components.placeholder_field import PlaceholderTextEdit
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, caption_style, heading_style
from src.ui.features.workspace.components.draggable_table_rows_editor import DraggableTableRowsEditor
from src.ui.features.workspace.components.edit_help import build_help_text
from src.ui.features.workspace.components.medicoes_table_editor import MedicoesTableEditor
from src.ui.features.workspace.components.section_field_schema import (
    default_field_values,
    get_edit_fields,
    get_media_blocks,
)


class _CollapsibleMediaBlock(QFrame):
    kind: str

    def __init__(self, kind: str, label: str, parent=None) -> None:
        super().__init__(parent)
        self.kind = kind
        self._expanded = False

        icons = {"photos": icon_image, "graphics": icon_chart, "tables": icon_table}
        icon_fn = icons.get(kind, icon_image)

        self._header = QToolButton()
        self._header.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self._header.setIcon(icon_fn())
        self._header.setText(label)
        self._header.setCheckable(True)
        self._header.setAutoRaise(True)
        self._header.clicked.connect(self._toggle)
        self._header.setStyleSheet(
            f"QToolButton {{ color: {PALETTE.text_primary}; font-weight: {TYPOGRAPHY.weight_medium}; "
            f"padding: {SPACING.xs}px; background: transparent; border: none; }}"
        )

        self._body = QWidget()
        self._body.setVisible(False)
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(SPACING.md, 0, 0, SPACING.sm)
        self._body_layout.setSpacing(SPACING.xs)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._header)
        layout.addWidget(self._body)

    def set_content(self, widget: QWidget) -> None:
        while self._body_layout.count():
            item = self._body_layout.takeAt(0)
            w = item.widget()
            if w is not None and w is not widget:
                w.setParent(None)
        if widget.parent() != self._body:
            self._body_layout.addWidget(widget)

    def set_count_hint(self, count: int) -> None:
        base = self._header.text().split(" (")[0]
        suffix = f" ({count})" if count > 0 else ""
        self._header.setText(f"{base}{suffix}")

    def _toggle(self) -> None:
        self._expanded = not self._expanded
        self._body.setVisible(self._expanded)
        self._header.setChecked(self._expanded)

    def expand(self) -> None:
        self._expanded = True
        self._body.setVisible(True)
        self._header.setChecked(True)


class _IntroBlockCard(QFrame):
    restore_requested = pyqtSignal(str, str)

    def __init__(
        self,
        label: str,
        title_key: str,
        body_key: str | None,
        title_value: str,
        body_value: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.title_key = title_key
        self.body_key = body_key

        self.setStyleSheet(
            f"QFrame {{ background: {PALETTE.bg_surface_alt}; border: 1px solid {PALETTE.border_subtle}; "
            f"border-radius: 8px; }}"
        )

        header = QHBoxLayout()
        title_lbl = QLabel(label)
        title_lbl.setStyleSheet(heading_style(4))
        header.addWidget(title_lbl, stretch=1)
        restore = SecondaryButton("Restaurar")
        restore.clicked.connect(
            lambda: self.restore_requested.emit(self.title_key, self.body_key or "")
        )
        header.addWidget(restore)

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

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._section_id: str | None = None
        self._loading = False
        self._field_widgets: dict[str, PlaceholderTextEdit | QLineEdit] = {}
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(600)
        self._debounce.timeout.connect(self._flush_textarea_pending)
        self._pending_textarea_key: str | None = None

        self._back_btn = SecondaryButton("Fechar edição")
        self._back_btn.clicked.connect(self.back_requested.emit)

        self._help_btn = QToolButton()
        self._help_btn.setText("?")
        self._help_btn.setToolTip("Ajuda desta seção")
        self._help_btn.setFixedSize(28, 28)
        self._help_btn.clicked.connect(self._show_help)

        self._media_toolbar = QHBoxLayout()
        self._media_toolbar.setSpacing(SPACING.xs)
        self._media_buttons: dict[str, QToolButton] = {}

        self._section_title_host = QWidget()
        self._section_title_layout = QVBoxLayout(self._section_title_host)
        self._section_title_layout.setContentsMargins(0, 0, 0, 0)
        self._section_title_layout.setSpacing(SPACING.xs)
        section_title_header = QLabel("Título da seção (como no preview)")
        section_title_header.setStyleSheet(heading_style(4))
        self._section_title_layout.addWidget(section_title_header)
        self._section_title_edit = PlaceholderTextEdit(multiline=False)
        self._section_title_edit.text_changed.connect(self._on_section_title_changed)
        self._section_title_layout.addWidget(self._section_title_edit)

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

        self._media_host = QWidget()
        self._media_layout = QVBoxLayout(self._media_host)
        self._media_layout.setContentsMargins(0, 0, 0, 0)
        self._media_layout.setSpacing(SPACING.xs)

        self._medicoes_editor = MedicoesTableEditor()
        self._medicoes_editor.rows_changed.connect(self.itens_medicao_changed.emit)
        self._medicoes_editor.restore_requested.connect(self.itens_medicao_restore_requested.emit)

        self._image_panel = ImageManagerPanel()
        self._image_panel.image_dropped.connect(self.image_dropped.emit)
        self._annotation_toolbar = AnnotationToolbar()
        self._annotation_toolbar.tool_selected.connect(self.tool_selected.emit)

        self._photos_block = _CollapsibleMediaBlock("photos", "Fotografias")
        self._photos_block.set_content(self._image_panel)
        self._insert_photo_btn = SecondaryButton("+ Inserir foto")
        self._insert_photo_btn.clicked.connect(self._on_insert_photo)
        photos_wrapper = QWidget()
        photos_layout = QVBoxLayout(photos_wrapper)
        photos_layout.setContentsMargins(0, 0, 0, 0)
        photos_layout.setSpacing(SPACING.xs)
        photos_layout.addWidget(self._insert_photo_btn)
        photos_layout.addWidget(self._image_panel)
        self._photos_block.set_content(photos_wrapper)
        self._graphics_block = _CollapsibleMediaBlock("graphics", "Gráficos")
        graphics_stub = QLabel("Integração com gráficos Calypso em breve.")
        graphics_stub.setWordWrap(True)
        graphics_stub.setStyleSheet(caption_style())
        self._graphics_block.set_content(graphics_stub)
        self._tables_block = _CollapsibleMediaBlock("tables", "Tabela")
        self._tables_block.set_content(self._medicoes_editor)

        self._media_blocks = {
            "photos": self._photos_block,
            "graphics": self._graphics_block,
            "tables": self._tables_block,
        }

        self._delete_btn = SecondaryButton("Excluir seção")
        self._delete_btn.clicked.connect(self._on_delete)
        self._restore_section_btn = SecondaryButton("Restaurar seção inteira")
        self._restore_section_btn.clicked.connect(self._on_restore_section)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        scroll_layout.setSpacing(SPACING.md)
        scroll_layout.addWidget(self._section_title_host)
        scroll_layout.addWidget(self._intro_blocks_host)
        scroll_layout.addWidget(self._fields_host)
        scroll_layout.addWidget(self._media_host)
        scroll_layout.addWidget(self._restore_section_btn)
        scroll_layout.addWidget(self._delete_btn)
        scroll_layout.addStretch(1)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setWidget(scroll_content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        top = QHBoxLayout()
        top.setContentsMargins(SPACING.sm, SPACING.xs, SPACING.sm, 0)
        top.addWidget(self._back_btn)
        top.addStretch(1)
        top.addWidget(self._help_btn)
        outer.addLayout(top)

        media_row_host = QWidget()
        media_row_host.setLayout(self._media_toolbar)
        outer.addWidget(media_row_host)

        toolbar_row = QHBoxLayout()
        toolbar_row.setContentsMargins(SPACING.sm, 0, SPACING.sm, SPACING.xs)
        toolbar_row.addWidget(self._annotation_toolbar)
        toolbar_row.addStretch(1)
        outer.addLayout(toolbar_row)

        outer.addWidget(self._scroll, stretch=1)

    def reset_breadcrumb(self) -> None:
        self._back_btn.setText("Fechar edição")

    def has_pending_textarea(self) -> bool:
        return self._pending_textarea_key is not None or self._debounce.isActive()

    def refresh_appearance(self) -> None:
        self._back_btn.refresh_appearance()
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
        scroll_pos = self._scroll.verticalScrollBar().value()
        self._section_id = section_id
        is_custom = section.get("custom", False) or section_id.startswith("custom_")
        self._delete_btn.setVisible(is_custom)
        self._restore_section_btn.setVisible(not is_custom)

        self._rebuild_section_title(section_id, overrides)
        self._rebuild_intro_blocks(section_id, overrides)
        self._rebuild_table_rows(section_id, table_rows or [])
        self._rebuild_fields(section_id, overrides, is_custom)
        self._rebuild_media_toolbar(section_id)
        self._rebuild_media_blocks(section_id)

        if section_id == "resultados" and itens_medicao is not None:
            self._medicoes_editor.set_rows(itens_medicao)
        self._loading = False
        self._scroll.verticalScrollBar().setValue(scroll_pos)
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
        scroll_pos = self._scroll.verticalScrollBar().value()
        section_id = self._section_id

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
        self._scroll.verticalScrollBar().setValue(scroll_pos)

    def _update_breadcrumb(self, section: dict) -> None:
        title = section.get("display_title") or section.get("title", self._section_id or "")
        self._back_btn.setText(f"Fechar edição — {title}")

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
            )
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

        fields = [f for f in get_edit_fields(section_id) if f.editable]
        if not fields:
            self._fields_host.setVisible(False)
            return
        self._fields_host.setVisible(True)

        prose_header = QLabel("Texto desta seção")
        prose_header.setStyleSheet(heading_style(4))
        self._fields_layout.addWidget(prose_header)

        defaults = default_field_values(section_id)
        for field_def in fields:
            row = QWidget()
            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(2)

            header = QHBoxLayout()
            label = QLabel(field_def.label)
            label.setStyleSheet(caption_style())
            header.addWidget(label, stretch=1)
            restore = SecondaryButton("Restaurar")
            fkey = field_def.key
            restore.clicked.connect(
                lambda _c=False, sid=section_id, k=fkey: self.section_field_restore_requested.emit(sid, k)
            )
            header.addWidget(restore)
            row_layout.addLayout(header)

            value = overrides.get(field_def.key, defaults.get(field_def.key, ""))
            if is_custom and field_def.field_type != "textarea":
                widget: PlaceholderTextEdit | QLineEdit = QLineEdit()
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
            self._fields_layout.addWidget(row)
            self._field_widgets[field_def.key] = widget

    def _rebuild_media_toolbar(self, section_id: str) -> None:
        while self._media_toolbar.count():
            item = self._media_toolbar.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._media_buttons.clear()

        blocks = get_media_blocks(section_id)
        labels = {"photos": "Fotografias", "graphics": "Gráficos", "tables": "Tabela"}
        icons = {"photos": icon_image, "graphics": icon_chart, "tables": icon_table}
        self._annotation_toolbar.setVisible(any(b.kind == "photos" for b in blocks))

        for media in blocks:
            btn = QToolButton()
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            btn.setIcon(icons[media.kind]())
            btn.setText(labels.get(media.kind, media.label))
            btn.setAutoRaise(True)
            kind = media.kind
            btn.clicked.connect(lambda _c=False, k=kind: self._on_media_toolbar_clicked(k))
            self._media_toolbar.addWidget(btn)
            self._media_buttons[kind] = btn

    def _rebuild_media_blocks(self, section_id: str) -> None:
        while self._media_layout.count():
            item = self._media_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

        blocks = get_media_blocks(section_id)
        if not blocks:
            self._media_host.setVisible(False)
            return
        self._media_host.setVisible(True)

        for media in blocks:
            block = self._media_blocks.get(media.kind)
            if block is None:
                continue
            if media.kind == "tables" and section_id == "identificacao":
                self._tables_block.set_content(self._table_rows_editor)
            elif media.kind == "tables":
                self._tables_block.set_content(self._medicoes_editor)
            self._media_layout.addWidget(block)

    def _on_media_toolbar_clicked(self, kind: str) -> None:
        block = self._media_blocks.get(kind)
        if block is not None:
            block.expand()
            self._scroll.ensureWidgetVisible(block)

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
        self._photos_block.set_count_hint(len(filtered))

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
