"""Campos globais do relatório — reutilizável no workspace e no editor de templates."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.core.domain.report_field_registry import GLOBAL_FIELDS, GlobalFieldDef
from src.ui.shared.report_editor.sidebar_chrome import sidebar_section_header
from src.ui.styles import SPACING, caption_style, sidebar_panel_style


class _GlobalFieldRow(QFrame):
    value_changed = pyqtSignal(str, str)
    restore_requested = pyqtSignal(str)

    def __init__(
        self,
        field_def: GlobalFieldDef,
        value: str,
        used_count: int,
        overridden: bool,
        show_restore: bool = True,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("GlobalFieldCard")
        self.setMinimumWidth(0)
        self._key = field_def.key

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        layout.setSpacing(SPACING.xs)

        label = QLabel(field_def.label)
        label.setObjectName("GlobalFieldLabel")
        label.setWordWrap(True)
        layout.addWidget(label)

        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)
        meta_row.setSpacing(SPACING.xs)
        meta_parts: list[str] = []
        if used_count > 0:
            meta_parts.append(f"Usado em {used_count} seção(ões)")
        if overridden:
            meta_parts.append("● alterado")
        meta = QLabel(" · ".join(meta_parts) if meta_parts else "")
        meta.setObjectName("GlobalFieldMeta")
        meta.setWordWrap(True)
        meta_row.addWidget(meta, stretch=1)
        if overridden and show_restore:
            restore = QLabel('<a href="restore">Restaurar</a>')
            restore.setObjectName("FieldRestoreLink")
            restore.setTextFormat(Qt.TextFormat.RichText)
            restore.setOpenExternalLinks(False)
            restore.setCursor(Qt.CursorShape.PointingHandCursor)
            restore.linkActivated.connect(lambda _href: self.restore_requested.emit(self._key))
            meta_row.addWidget(restore, alignment=Qt.AlignmentFlag.AlignRight)
        if meta_parts or overridden:
            layout.addLayout(meta_row)

        self._input = QLineEdit(value)
        self._input.setObjectName("GlobalFieldInput")
        self._input.setPlaceholderText(f"Editar {field_def.label.lower()}…")
        self._input.setMinimumWidth(0)
        self._input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._input.setMinimumHeight(36)
        self._input.editingFinished.connect(
            lambda: self.value_changed.emit(self._key, self._input.text())
        )
        layout.addWidget(self._input)

    def set_value(self, value: str) -> None:
        self._input.setText(value)


class GlobalFieldsPanel(QFrame):
    """Campos globais editáveis — propagam para todo o template/relatório."""

    field_changed = pyqtSignal(str, str)
    restore_field_requested = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("GlobalFieldsPanel")
        self.setMinimumWidth(0)
        self._rows: dict[str, _GlobalFieldRow] = {}

        self._hint = QLabel(
            "Alterações aqui refletem em todas as seções do PDF que usam este valor."
        )
        self._hint.setObjectName("SidebarHint")
        self._hint.setWordWrap(True)

        self._fields_host = QWidget()
        self._fields_host.setMinimumWidth(0)
        self._fields_layout = QVBoxLayout(self._fields_host)
        self._fields_layout.setContentsMargins(0, 0, 0, 0)
        self._fields_layout.setSpacing(SPACING.sm)

        scroll = QScrollArea()
        scroll.setObjectName("GlobalFieldsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(self._fields_host)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(SPACING.md, SPACING.xs, SPACING.md, SPACING.md)
        inner_layout.setSpacing(SPACING.sm)
        inner_layout.addWidget(self._hint)
        inner_layout.addWidget(scroll, stretch=1)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(sidebar_section_header("Dados do relatório"))
        outer.addWidget(inner, stretch=1)

    def refresh_appearance(self) -> None:
        self.setStyleSheet(sidebar_panel_style())
        self._hint.setStyleSheet(caption_style())

    def render_fields(
        self,
        values: dict[str, str],
        overridden_keys: set[str],
        *,
        show_restore: bool = True,
    ) -> None:
        while self._fields_layout.count():
            item = self._fields_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._rows.clear()

        for field_def in GLOBAL_FIELDS:
            value = values.get(field_def.key, "")
            used_count = len(field_def.used_in_sections)
            row = _GlobalFieldRow(
                field_def,
                value,
                used_count,
                field_def.key in overridden_keys,
                show_restore=show_restore,
            )
            row.value_changed.connect(self.field_changed.emit)
            row.restore_requested.connect(self.restore_field_requested.emit)
            self._rows[field_def.key] = row
            self._fields_layout.addWidget(row)
