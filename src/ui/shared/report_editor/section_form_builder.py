"""Montagem dinâmica de campos de formulário por seção."""
from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from src.core.application.interpretacao_edit import interpretacao_field_defs
from src.core.domain.report_field_registry import INTRODUCAO_BODY_TITLE_KEYS, get_edit_fields
from src.core.domain.table_row_registry import INTRODUCAO_BLOCK_TITLES
from src.ui.components.placeholder_field import PlaceholderTextEdit
from src.ui.features.workspace.components.section_field_schema import default_field_values
from src.ui.styles import SPACING, caption_style


class SectionFormBuilder:
    """Constrói widgets de campos de prosa para uma seção."""

    def __init__(
        self,
        fields_host: QWidget,
        fields_layout: QVBoxLayout,
        *,
        defaults_mode: bool,
        on_field_changed: Callable[[str, str], None],
        on_line_finished: Callable[[str, QLineEdit], None],
        on_field_restore: Callable[[str, str], None],
    ) -> None:
        self._fields_host = fields_host
        self._fields_layout = fields_layout
        self._defaults_mode = defaults_mode
        self._on_field_changed = on_field_changed
        self._on_line_finished = on_line_finished
        self._on_field_restore = on_field_restore

    def set_defaults_mode(self, enabled: bool) -> None:
        self._defaults_mode = enabled

    def rebuild(
        self,
        section_id: str,
        overrides: dict,
        is_custom: bool,
    ) -> dict[str, PlaceholderTextEdit | QLineEdit]:
        while self._fields_layout.count():
            item = self._fields_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        field_widgets: dict[str, PlaceholderTextEdit | QLineEdit] = {}

        if section_id == "interpretacao":
            fields = list(interpretacao_field_defs(overrides))
        else:
            fields = list(get_edit_fields(section_id, defaults_mode=self._defaults_mode))
            if not self._defaults_mode:
                fields = [f for f in fields if f.editable]
        if not fields:
            self._fields_host.setVisible(False)
            return field_widgets
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
                    lambda _href, sid=section_id, k=fkey: self._on_field_restore(sid, k)
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
                field_widgets[title_key] = title_edit
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
            field_widgets[field_def.key] = widget

        return field_widgets
