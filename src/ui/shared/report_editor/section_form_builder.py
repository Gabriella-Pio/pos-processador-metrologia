"""Montagem dinâmica de campos de formulário por seção."""
from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from src.core.application.interpretacao_edit import interpretacao_field_defs
from src.core.domain.ports import VersionEntry
from src.core.domain.report_field_registry import INTRODUCAO_BODY_TITLE_KEYS, get_edit_fields
from src.core.domain.table_row_registry import INTRODUCAO_BLOCK_TITLES
from src.ui.components.buttons import SecondaryButton
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
        on_manage_versions: Callable[[], None] | None = None,
    ) -> None:
        self._fields_host = fields_host
        self._fields_layout = fields_layout
        self._defaults_mode = defaults_mode
        self._on_field_changed = on_field_changed
        self._on_line_finished = on_line_finished
        self._on_field_restore = on_field_restore
        self._on_manage_versions = on_manage_versions
        self._fields_host_ref = fields_host

    def _on_prose_field_height_changed(self) -> None:
        self._fields_host_ref.updateGeometry()

    def set_defaults_mode(self, enabled: bool) -> None:
        self._defaults_mode = enabled

    def rebuild(
        self,
        section_id: str,
        overrides: dict,
        is_custom: bool,
        *,
        version_entries: list[VersionEntry] | None = None,
    ) -> dict[str, PlaceholderTextEdit | QLineEdit]:
        while self._fields_layout.count():
            item = self._fields_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        field_widgets: dict[str, PlaceholderTextEdit | QLineEdit] = {}

        if section_id == "historico_versoes" and not self._defaults_mode:
            return self._build_historico_panel(overrides, version_entries or [])

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
            field_widgets[field_def.key] = self._add_field_card(
                section_id,
                field_def,
                overrides,
                defaults,
                is_custom,
                field_widgets,
            )

        return field_widgets

    def _add_field_card(
        self,
        section_id: str,
        field_def,
        overrides: dict,
        defaults: dict,
        is_custom: bool,
        field_widgets: dict[str, PlaceholderTextEdit | QLineEdit],
    ) -> PlaceholderTextEdit | QLineEdit:
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
            widget = PlaceholderTextEdit(
                multiline=field_def.field_type == "textarea",
                supports_formatting=field_def.supports_formatting,
            )
            widget.set_text(value)
            widget.text_changed.connect(
                lambda text, k=field_def.key: self._on_field_changed(k, text)
            )
            if field_def.supports_formatting:
                widget.height_changed.connect(self._on_prose_field_height_changed)
        row_layout.addWidget(widget)
        self._fields_layout.addWidget(card)
        return widget

    def _build_historico_panel(
        self,
        overrides: dict,
        version_entries: list[VersionEntry],
    ) -> dict[str, PlaceholderTextEdit | QLineEdit]:
        self._fields_host.setVisible(True)
        field_widgets: dict[str, PlaceholderTextEdit | QLineEdit] = {}
        defaults = default_field_values("historico_versoes")
        fields = list(get_edit_fields("historico_versoes"))

        prose_header = QLabel("Blocos de texto")
        prose_header.setObjectName("GlobalFieldLabel")
        self._fields_layout.addWidget(prose_header)

        for field_def in fields:
            if field_def.key == "nota":
                self._append_historico_table_preview(version_entries)
            field_widgets[field_def.key] = self._add_field_card(
                "historico_versoes",
                field_def,
                overrides,
                defaults,
                False,
                field_widgets,
            )

        return field_widgets

    def _append_historico_table_preview(self, version_entries: list[VersionEntry]) -> None:
        header = QLabel("Tabela de versões (automática)")
        header.setObjectName("GlobalFieldLabel")
        self._fields_layout.addWidget(header)

        hint = QLabel(
            "Gerada a partir das versões registradas (Ctrl+S ou aba Histórico). "
            "Para registrar ou restaurar versões, use a timeline lateral."
        )
        hint.setWordWrap(True)
        hint.setObjectName("SidebarHint")
        hint.setStyleSheet(caption_style())
        self._fields_layout.addWidget(hint)

        table_card = QFrame()
        table_card.setObjectName("GlobalFieldCard")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        table_layout.setSpacing(SPACING.xs)

        if not version_entries:
            empty = QLabel("Nenhuma versão registrada ainda.")
            empty.setWordWrap(True)
            empty.setObjectName("SidebarHint")
            table_layout.addWidget(empty)
        else:
            for entry in version_entries:
                row = QLabel(
                    f"<b>v{entry.version_number}</b> · "
                    f"{entry.timestamp.strftime('%d/%m/%Y %H:%M')} · "
                    f"{entry.responsible_name}<br/>{entry.description}"
                )
                row.setWordWrap(True)
                row.setTextFormat(Qt.TextFormat.RichText)
                table_layout.addWidget(row)

        self._fields_layout.addWidget(table_card)

        if self._on_manage_versions is not None:
            manage_btn = SecondaryButton("Gerenciar versões")
            manage_btn.clicked.connect(self._on_manage_versions)
            self._fields_layout.addWidget(manage_btn)
