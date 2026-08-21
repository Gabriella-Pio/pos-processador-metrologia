"""Aba Conteúdo do editor de seção (título, campos, origem, ações)."""
from __future__ import annotations

from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.core.domain.ports import VersionEntry
from src.core.domain.section_schema import is_custom_section_id
from src.core.domain.table_row_registry import INTRODUCAO_BLOCK_TITLES, SECTION_HEADING_DEFAULTS
from src.ui.components.buttons import SecondaryButton
from src.ui.components.inputs import ThemedComboBox
from src.ui.components.placeholder_field import PlaceholderTextEdit
from src.ui.shared.report_editor.section_form_builder import SectionFormBuilder
from src.ui.styles import SPACING, caption_style, form_label_style
from src.core.domain.report_field_registry import get_edit_fields
from src.ui.features.workspace.components.section_field_schema import default_field_values


class SectionContentTab(QWidget):
    section_field_changed = pyqtSignal(str, str, str)
    section_field_restore_requested = pyqtSignal(str, str)
    section_restore_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    catalog_section_chosen = pyqtSignal(str)
    manage_versions_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._section_id: str | None = None
        self._loading = False
        self._defaults_mode = False
        self._section_overrides: dict = {}
        self._version_entries: list[VersionEntry] = []
        self._catalog_origin_options: list[dict[str, str]] = []
        self._field_widgets: dict[str, PlaceholderTextEdit | QLineEdit] = {}
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(600)
        self._debounce.timeout.connect(self._flush_textarea_pending)
        self._pending_textarea_key: str | None = None
        self._force_next_patch = False

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

        self._origin_picker = QFrame()
        self._origin_picker.setObjectName("GlobalFieldCard")
        origin_layout = QVBoxLayout(self._origin_picker)
        origin_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        origin_layout.setSpacing(SPACING.xs)
        origin_label = QLabel("BASE DA SEÇÃO")
        origin_label.setObjectName("GlobalFieldLabel")
        origin_label.setStyleSheet(form_label_style())
        self._origin_combo = ThemedComboBox()
        self._origin_combo.setMinimumHeight(38)
        self._origin_combo.currentIndexChanged.connect(self._on_origin_combo_changed)
        self._origin_hint = QLabel(
            "Comece do zero ou troque por uma seção do catálogo ainda não usada neste relatório."
        )
        self._origin_hint.setWordWrap(True)
        self._origin_hint.setObjectName("SidebarHint")
        self._origin_hint.setStyleSheet(caption_style())
        origin_layout.addWidget(origin_label)
        origin_layout.addWidget(self._origin_combo)
        origin_layout.addWidget(self._origin_hint)
        self._origin_picker.hide()

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
            on_field_restore=self._on_field_restore,
            on_manage_versions=self.manage_versions_requested.emit,
        )

        self._delete_btn = SecondaryButton("Excluir seção")
        self._delete_btn.clicked.connect(self._on_delete)
        self._restore_section_btn = SecondaryButton("Restaurar seção inteira")
        self._restore_section_btn.clicked.connect(self._on_restore_section)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        scroll_layout.setSpacing(SPACING.sm)
        scroll_layout.addWidget(self._origin_picker)
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

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._content_scroll)

    @property
    def scroll_area(self) -> QScrollArea:
        return self._content_scroll

    @property
    def field_widgets(self) -> dict[str, PlaceholderTextEdit | QLineEdit]:
        return self._field_widgets

    def set_loading(self, loading: bool) -> None:
        self._loading = loading

    def set_defaults_mode(self, enabled: bool) -> None:
        self._defaults_mode = enabled
        self._form_builder.set_defaults_mode(enabled)
        self._delete_btn.setVisible(not enabled)
        self._restore_section_btn.setVisible(not enabled)
        if enabled:
            self._origin_picker.hide()

    def set_catalog_origin_options(self, options: list[dict[str, str]]) -> None:
        self._catalog_origin_options = list(options or [])
        if self._section_id is not None:
            is_custom = is_custom_section_id(self._section_id) or self._section_id.startswith(
                "custom_"
            )
            self.sync_origin_picker(is_custom=is_custom)

    def set_section_overrides(self, overrides: dict) -> None:
        self._section_overrides = dict(overrides)

    def set_version_entries(self, entries: list[VersionEntry]) -> None:
        self._version_entries = list(entries)

    def sync_origin_picker(self, *, is_custom: bool) -> None:
        show = (
            is_custom
            and not self._defaults_mode
            and bool(self._catalog_origin_options)
        )
        self._origin_picker.setVisible(show)
        if not show:
            return
        self._origin_combo.blockSignals(True)
        self._origin_combo.clear()
        self._origin_combo.addItem("Personalizada — começar do zero", None)
        for option in self._catalog_origin_options:
            label = option.get("label") or option.get("id", "")
            if option.get("action") == "restore":
                label = f"{label} (reativar)"
            self._origin_combo.addItem(label, option.get("id"))
        self._origin_combo.setCurrentIndex(0)
        self._origin_combo.blockSignals(False)

    def open_content(
        self,
        section_id: str,
        overrides: dict,
        *,
        is_custom: bool,
    ) -> int:
        """Monta título/campos/origem. Retorna posição vertical do scroll anterior."""
        scroll_pos = self._content_scroll.verticalScrollBar().value()
        self._section_id = section_id
        self._section_overrides = dict(overrides)
        self._delete_btn.setVisible(is_custom and not self._defaults_mode)
        self._restore_section_btn.setVisible(not is_custom and not self._defaults_mode)
        self.sync_origin_picker(is_custom=is_custom)
        self.rebuild_section_title(section_id, overrides)
        self.rebuild_fields(section_id, overrides, is_custom)
        return scroll_pos

    def restore_scroll(self, scroll_pos: int) -> None:
        self._content_scroll.verticalScrollBar().setValue(scroll_pos)

    def scroll_position(self) -> int:
        return self._content_scroll.verticalScrollBar().value()

    def rebuild_section_title(self, section_id: str, overrides: dict) -> None:
        default = SECTION_HEADING_DEFAULTS.get(section_id, overrides.get("title", section_id))
        self._section_title_edit.set_text(overrides.get("section_title", default))

    def rebuild_fields(self, section_id: str, overrides: dict, is_custom: bool) -> None:
        self._field_widgets = self._form_builder.rebuild(
            section_id,
            overrides,
            is_custom,
            version_entries=self._version_entries,
        )

    def rebuild_version_history_fields(self) -> None:
        if self._section_id == "historico_versoes" and not self._defaults_mode:
            self._field_widgets = self._form_builder.rebuild(
                self._section_id,
                self._section_overrides,
                False,
                version_entries=self._version_entries,
            )

    def patch_fields(self, section_id: str, overrides: dict, *, force: bool = False) -> None:
        self._section_overrides = dict(overrides)
        force = force or self.consume_force_patch()
        default = SECTION_HEADING_DEFAULTS.get(section_id, overrides.get("title", section_id))
        self._section_title_edit.set_text(overrides.get("section_title", default), force=force)
        defaults = default_field_values(section_id)
        for key, widget in self._field_widgets.items():
            if key.startswith("title_"):
                value = overrides.get(key, INTRODUCAO_BLOCK_TITLES.get(key, ""))
            else:
                value = overrides.get(key, defaults.get(key, ""))
            if isinstance(widget, PlaceholderTextEdit):
                widget.set_text(value, force=force)
            elif isinstance(widget, QLineEdit):
                widget.setText(value)

    def prepare_restore(self) -> None:
        """Cancela debounce e autoriza patch mesmo com o editor focado."""
        self._cancel_pending_textarea()
        self._force_next_patch = True

    def should_force_patch(self) -> bool:
        return self._force_next_patch

    def consume_force_patch(self) -> bool:
        force = self._force_next_patch
        self._force_next_patch = False
        return force

    def has_focused_editor(self) -> bool:
        if self._section_title_edit.has_editor_focus():
            return True
        for widget in self._field_widgets.values():
            if isinstance(widget, PlaceholderTextEdit) and widget.has_editor_focus():
                return True
        return False

    def has_pending_textarea(self) -> bool:
        return self._pending_textarea_key is not None or self._debounce.isActive()

    def focus_section_title_editor(self) -> None:
        self._content_scroll.ensureWidgetVisible(self._section_title_host, 0, 40)
        self._section_title_edit.focus_editor(select_all=True)

    def refresh_action_buttons(self) -> None:
        self._delete_btn.refresh_appearance()

    def _on_origin_combo_changed(self, index: int) -> None:
        if self._loading or index < 0:
            return
        catalog_id = self._origin_combo.itemData(index)
        if not catalog_id:
            return
        self.catalog_section_chosen.emit(str(catalog_id))

    def _on_section_title_changed(self, text: str) -> None:
        if self._loading or self._section_id is None:
            return
        self.section_field_changed.emit(self._section_id, "section_title", text)

    def _on_field_changed(self, key: str, text: str) -> None:
        if self._loading or self._section_id is None or not key:
            return
        textarea_keys = {
            f.key for f in get_edit_fields(self._section_id) if f.field_type == "textarea"
        }
        if key in textarea_keys:
            self._pending_textarea_key = key
            self._debounce.start()
        else:
            self.section_field_changed.emit(self._section_id, key, text)

    def _on_line_finished(self, key: str, widget: QLineEdit) -> None:
        if self._loading or self._section_id is None:
            return
        self.section_field_changed.emit(self._section_id, key, widget.text())

    def _cancel_pending_textarea(self) -> None:
        self._debounce.stop()
        self._pending_textarea_key = None

    def _flush_textarea_pending(self) -> None:
        if self._section_id is None or self._pending_textarea_key is None:
            self._cancel_pending_textarea()
            return
        key = self._pending_textarea_key
        self._cancel_pending_textarea()
        widget = self._field_widgets.get(key)
        if isinstance(widget, PlaceholderTextEdit):
            self.section_field_changed.emit(self._section_id, key, widget.get_text())

    def _on_field_restore(self, section_id: str, key: str) -> None:
        self.prepare_restore()
        self.section_field_restore_requested.emit(section_id, key)

    def _on_restore_section(self) -> None:
        if self._section_id is not None:
            self.prepare_restore()
            self.section_restore_requested.emit(self._section_id)

    def _on_delete(self) -> None:
        if self._section_id is not None:
            self.delete_requested.emit(self._section_id)
