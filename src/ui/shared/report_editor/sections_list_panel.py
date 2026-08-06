"""Lista reordenável de seções — compartilhada entre workspace e templates."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.core.domain.ports import ReportImage
from src.core.domain.section_schema import FIXED_SECTION_IDS, SECTION_DEFINITIONS
from src.ui.components.icons import icon_edit, icon_plus, icon_trash
from src.ui.shared.report_editor.sidebar_chrome import sidebar_section_header
from src.ui.styles import SPACING, caption_style, sidebar_panel_style

_PROTECTED_IDS = frozenset(s.id for s in SECTION_DEFINITIONS)
_ROW_HEIGHT = 52
_ACCENT_WIDTH = 3
_ACTIONS_WIDTH = 76


class TemplateSectionRow(QFrame):
    """Linha do sumário no modo template — toggle enabled + seleção para editar."""

    click_requested = pyqtSignal(str)
    enabled_changed = pyqtSignal(str, bool)
    delete_requested = pyqtSignal(str)

    def __init__(self, section: dict, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("SectionSummaryRow")
        self.setMinimumWidth(0)
        self.section_id = section["id"]
        self._full_title = section.get("display_title") or section.get("title", section["id"])
        self._protected = bool(section.get("protected")) or self.section_id in FIXED_SECTION_IDS
        self._is_custom = bool(section.get("custom")) or (
            self.section_id.startswith("custom_") and self.section_id not in FIXED_SECTION_IDS
        )
        enabled = section.get("enabled", True)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, SPACING.sm, 0)
        root.setSpacing(0)

        self._accent = QFrame()
        self._accent.setObjectName("SectionSummaryAccent")
        self._accent.setFixedWidth(_ACCENT_WIDTH)

        body = QWidget()
        body.setMinimumWidth(0)
        body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(SPACING.sm, SPACING.xs, SPACING.xs, SPACING.xs)
        body_layout.setSpacing(SPACING.sm)

        self._enabled_cb = QCheckBox()
        self._enabled_cb.setObjectName("SectionSummaryEnabled")
        self._enabled_cb.setChecked(enabled)
        self._enabled_cb.setEnabled(not self._protected)
        self._enabled_cb.setToolTip(
            "Seção fixa do relatório" if self._protected else "Incluir seção no template"
        )
        self._enabled_cb.stateChanged.connect(self._on_enabled_changed)

        self._title_label = QLabel(self._full_title)
        self._title_label.setToolTip(self._full_title)
        self._title_label.setObjectName("SectionSummaryTitle")
        self._title_label.setWordWrap(False)
        self._title_label.setMinimumWidth(0)
        self._title_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

        text_col = QWidget()
        text_col.setMinimumWidth(0)
        text_col.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        text_layout = QVBoxLayout(text_col)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(SPACING.xs)
        title_row.addWidget(self._title_label, stretch=1)
        text_layout.addLayout(title_row)
        if not enabled and not self._protected:
            meta = QLabel("Desativada")
            meta.setObjectName("SectionSummaryMeta")
            text_layout.addWidget(meta)

        body_layout.addWidget(self._enabled_cb)
        body_layout.addWidget(text_col, stretch=1)

        if self._is_custom:
            self._delete_btn = QToolButton()
            self._delete_btn.setObjectName("SectionSummaryActionDanger")
            self._delete_btn.setAutoRaise(True)
            self._delete_btn.setFixedSize(28, 28)
            self._delete_btn.setIcon(icon_trash())
            self._delete_btn.setToolTip("Excluir seção personalizada")
            self._delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.section_id))
            body_layout.addWidget(self._delete_btn)

        root.addWidget(self._accent)
        root.addWidget(body, stretch=1)

        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_active(False)
        self._elide_title()

    def _on_enabled_changed(self, _state: int) -> None:
        self.enabled_changed.emit(self.section_id, self._enabled_cb.isChecked())

    def set_enabled(self, enabled: bool) -> None:
        self._enabled_cb.blockSignals(True)
        self._enabled_cb.setChecked(enabled)
        self._enabled_cb.blockSignals(False)

    def _elide_title(self) -> None:
        checkbox_w = 28
        margins = SPACING.sm * 3 + _ACCENT_WIDTH + checkbox_w
        available = max(48, self.width() - margins)
        metrics = QFontMetrics(self._title_label.font())
        self._title_label.setText(
            metrics.elidedText(self._full_title, Qt.TextElideMode.ElideRight, available)
        )

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._elide_title()

    def set_active(self, active: bool) -> None:
        self._apply_active(active)

    def _apply_active(self, active: bool) -> None:
        state = "true" if active else "false"
        self.setProperty("active", state)
        self._accent.setProperty("active", state)
        self.style().unpolish(self)
        self.style().polish(self)
        self._accent.style().unpolish(self._accent)
        self._accent.style().polish(self._accent)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(event.position().toPoint())
            widget = child
            while widget is not None and widget is not self:
                if isinstance(widget, QCheckBox):
                    super().mousePressEvent(event)
                    return
                if isinstance(widget, QToolButton):
                    super().mousePressEvent(event)
                    return
                widget = widget.parentWidget()
            self.click_requested.emit(self.section_id)
        super().mousePressEvent(event)

    def sizeHint(self) -> QSize:
        return QSize(super().sizeHint().width(), _ROW_HEIGHT)


class SectionSummaryRow(QFrame):
    """Linha do sumário — clique navega; duplo-clique ou lápis edita."""

    click_requested = pyqtSignal(str)
    edit_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)

    def __init__(self, section: dict, photo_count: int, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("SectionSummaryRow")
        self.setMinimumWidth(0)
        self.section_id = section["id"]
        self._photo_count = photo_count
        self._full_title = section.get("display_title") or section.get("title", section["id"])
        self._has_modified_dot = bool(section.get("has_overrides"))

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, SPACING.sm, 0)
        root.setSpacing(0)

        self._accent = QFrame()
        self._accent.setObjectName("SectionSummaryAccent")
        self._accent.setFixedWidth(_ACCENT_WIDTH)

        body = QWidget()
        body.setMinimumWidth(0)
        body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(SPACING.sm, SPACING.xs, SPACING.xs, SPACING.xs)
        body_layout.setSpacing(SPACING.sm)

        text_col = QWidget()
        text_col.setMinimumWidth(0)
        text_col.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        text_layout = QVBoxLayout(text_col)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(SPACING.xs)

        if self._has_modified_dot:
            dot = QLabel("●")
            dot.setObjectName("SectionSummaryModified")
            keys = section.get("override_keys") or []
            dot.setToolTip(
                "Campos alterados: " + ", ".join(keys) if keys else "Seção com alterações"
            )
            title_row.addWidget(dot)

        self._title_label = QLabel(self._full_title)
        self._title_label.setToolTip(self._full_title)
        self._title_label.setObjectName("SectionSummaryTitle")
        self._title_label.setWordWrap(False)
        self._title_label.setMinimumWidth(0)
        self._title_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        title_row.addWidget(self._title_label, stretch=1)
        text_layout.addLayout(title_row)

        meta_parts: list[str] = []
        if photo_count > 0:
            meta_parts.append(f"{photo_count} foto{'s' if photo_count != 1 else ''}")
        if section.get("custom") or str(section["id"]).startswith("custom_"):
            meta_parts.append("Personalizada")
        self._meta_label = QLabel(" · ".join(meta_parts))
        self._meta_label.setObjectName("SectionSummaryMeta")
        self._meta_label.setVisible(bool(meta_parts))
        text_layout.addWidget(self._meta_label)

        body_layout.addWidget(text_col, stretch=1)

        self._photo_badge = QLabel()
        self._photo_badge.setObjectName("SectionSummaryBadge")
        self._photo_badge.setVisible(photo_count > 0)
        if photo_count > 0:
            self._photo_badge.setText(str(photo_count))

        self._edit_btn = QToolButton()
        self._edit_btn.setObjectName("SectionSummaryAction")
        self._edit_btn.setAutoRaise(True)
        self._edit_btn.setFixedSize(28, 28)
        self._edit_btn.setIcon(icon_edit())
        self._edit_btn.setToolTip("Editar seção")
        self._edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.section_id))

        is_custom = (
            (section.get("custom") or str(section["id"]).startswith("custom_"))
            and section["id"] not in _PROTECTED_IDS
        )
        self._delete_btn = QToolButton()
        self._delete_btn.setObjectName("SectionSummaryActionDanger")
        self._delete_btn.setAutoRaise(True)
        self._delete_btn.setFixedSize(28, 28)
        self._delete_btn.setIcon(icon_trash())
        self._delete_btn.setToolTip("Excluir seção")
        self._delete_btn.setVisible(is_custom)
        self._delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.section_id))

        self._actions_host = QWidget()
        self._actions_host.setObjectName("SectionSummaryActions")
        self._actions_host.setFixedWidth(_ACTIONS_WIDTH)
        self._actions_host.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        actions_layout = QHBoxLayout(self._actions_host)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(2)
        actions_layout.addStretch(1)
        actions_layout.addWidget(self._photo_badge)
        actions_layout.addWidget(self._edit_btn)
        actions_layout.addWidget(self._delete_btn)
        body_layout.addWidget(self._actions_host, stretch=0)

        root.addWidget(self._accent)
        root.addWidget(body, stretch=1)

        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_active(False)
        self._elide_title()

    def _elide_title(self) -> None:
        dot_w = 12 if self._has_modified_dot else 0
        margins = SPACING.sm * 3 + _ACCENT_WIDTH
        available = max(48, self.width() - margins - _ACTIONS_WIDTH - dot_w)
        metrics = QFontMetrics(self._title_label.font())
        self._title_label.setText(
            metrics.elidedText(self._full_title, Qt.TextElideMode.ElideRight, available)
        )

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._elide_title()

    def set_photo_count(self, count: int) -> None:
        self._photo_count = count
        self._photo_badge.setVisible(count > 0)
        if count > 0:
            self._photo_badge.setText(str(count))

    def set_active(self, active: bool) -> None:
        self._apply_active(active)

    def _apply_active(self, active: bool) -> None:
        state = "true" if active else "false"
        self.setProperty("active", state)
        self._accent.setProperty("active", state)
        self.style().unpolish(self)
        self.style().polish(self)
        self._accent.style().unpolish(self._accent)
        self._accent.style().polish(self._accent)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(event.position().toPoint())
            widget = child
            while widget is not None and widget is not self:
                if isinstance(widget, QToolButton):
                    super().mousePressEvent(event)
                    return
                widget = widget.parentWidget()
            self.click_requested.emit(self.section_id)
        super().mousePressEvent(event)

    def sizeHint(self) -> QSize:
        return QSize(super().sizeHint().width(), _ROW_HEIGHT)


class _AddSectionRow(QFrame):
    clicked = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("SectionSummaryAddRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        layout.setSpacing(SPACING.sm)
        icon = QLabel()
        icon.setPixmap(icon_plus().pixmap(16, 16))
        label = QLabel("Nova seção")
        label.setObjectName("SectionSummaryAddLabel")
        layout.addWidget(icon)
        layout.addWidget(label)
        layout.addStretch(1)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def sizeHint(self) -> QSize:
        return QSize(200, 44)


class SectionsListPanel(QFrame):
    """Painel de sumário — emitir sinais; quem consome decide navegação vs. edição."""

    section_navigated = pyqtSignal(str)
    section_edit_requested = pyqtSignal(str)
    section_delete_requested = pyqtSignal(str)
    section_enabled_changed = pyqtSignal(str, bool)
    sections_reordered = pyqtSignal(list)
    add_custom_section_requested = pyqtSignal()

    def __init__(self, mode: str = "workspace", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("SectionSummaryPanel")
        self.setMinimumWidth(0)
        self._mode = mode
        self._sections: list[dict] = []
        self._images_by_section: dict[str, list[ReportImage]] = {}
        self._active_section_id: str | None = None
        self._loading = False
        self._pending_section_id: str | None = None

        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.setInterval(280)
        self._click_timer.timeout.connect(self._emit_single_click)

        self._hint = QLabel(
            "Marque as seções e clique para editar defaults"
            if self._mode == "template"
            else "Clique para ir ao preview · duplo-clique para editar"
        )
        self._hint.setObjectName("SidebarHint")
        self._hint.setWordWrap(True)

        self._list = QListWidget()
        self._list.setObjectName("SectionSummaryList")
        self._list.setMinimumWidth(0)
        self._list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self._list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._list.setSpacing(2)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.model().rowsMoved.connect(self._emit_reorder)

        self._add_row = _AddSectionRow()
        self._add_row.clicked.connect(self.add_custom_section_requested.emit)
        if self._mode == "template":
            self._add_row.setToolTip("Adicionar seção personalizada ao template")

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(SPACING.md, SPACING.xs, SPACING.md, SPACING.md)
        inner_layout.setSpacing(SPACING.sm)
        inner_layout.addWidget(self._hint)
        inner_layout.addWidget(self._list, stretch=1)
        inner_layout.addWidget(self._add_row)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(sidebar_section_header("Sumário"))
        outer.addWidget(inner, stretch=1)

    def refresh_appearance(self) -> None:
        self.setStyleSheet(sidebar_panel_style())
        self._hint.setStyleSheet(caption_style())

    def set_section_images(self, images: list[ReportImage]) -> None:
        self._images_by_section = {}
        for image in images:
            self._images_by_section.setdefault(image.section_id, []).append(image)
        for index in range(self._list.count()):
            item = self._list.item(index)
            widget = self._list.itemWidget(item)
            if isinstance(widget, SectionSummaryRow):
                widget.set_photo_count(len(self._images_by_section.get(widget.section_id, [])))

    def render_sections(self, sections: list[dict]) -> None:
        self._sections = sections
        count = len(sections)
        if self._mode == "template":
            enabled_count = sum(1 for s in sections if s.get("enabled", True))
            self._hint.setText(
                f"{enabled_count} de {count} seção{'ões' if count != 1 else ''} ativas · "
                "marque e clique para editar defaults"
            )
        else:
            self._hint.setText(
                f"{count} seção{'ões' if count != 1 else ''} · "
                "clique para ir ao preview · duplo-clique para editar"
            )
        self._rebuild_rows()

    def set_active_section(self, section_id: str | None) -> None:
        self._active_section_id = section_id
        row_types = (SectionSummaryRow, TemplateSectionRow)
        for index in range(self._list.count()):
            item = self._list.item(index)
            widget = self._list.itemWidget(item)
            if isinstance(widget, row_types):
                widget.set_active(widget.section_id == section_id)

    def _rebuild_rows(self) -> None:
        self._loading = True
        self._list.clear()
        for section in self._sections:
            section_id = section["id"]
            if self._mode == "template":
                row = TemplateSectionRow(section)
                row.click_requested.connect(self.section_edit_requested.emit)
                row.enabled_changed.connect(self.section_enabled_changed.emit)
                row.delete_requested.connect(self.section_delete_requested.emit)
            else:
                photos = len(self._images_by_section.get(section_id, []))
                row = SectionSummaryRow(section, photos)
                row.click_requested.connect(self._on_row_clicked)
                row.edit_requested.connect(self._on_row_edit_requested)
                row.delete_requested.connect(self.section_delete_requested.emit)
            row.set_active(section_id == self._active_section_id)
            item = QListWidgetItem()
            item.setFlags(
                item.flags()
                | Qt.ItemFlag.ItemIsDragEnabled
                | Qt.ItemFlag.ItemIsDropEnabled
                | Qt.ItemFlag.ItemIsEnabled
            )
            item.setSizeHint(row.sizeHint())
            self._list.addItem(item)
            self._list.setItemWidget(item, row)
        self._loading = False

    def _on_row_clicked(self, section_id: str) -> None:
        if self._click_timer.isActive() and self._pending_section_id == section_id:
            self._click_timer.stop()
            self._pending_section_id = None
            self.section_edit_requested.emit(section_id)
            return
        self._pending_section_id = section_id
        self._click_timer.start()

    def _on_row_edit_requested(self, section_id: str) -> None:
        self._click_timer.stop()
        self._pending_section_id = None
        self.section_edit_requested.emit(section_id)

    def _emit_single_click(self) -> None:
        if self._pending_section_id is not None:
            self.section_navigated.emit(self._pending_section_id)
            self._pending_section_id = None

    def _emit_reorder(self, *_args) -> None:
        if self._loading:
            return
        row_type = TemplateSectionRow if self._mode == "template" else SectionSummaryRow
        ordered = [
            self._list.itemWidget(self._list.item(i)).section_id  # type: ignore[union-attr]
            for i in range(self._list.count())
            if isinstance(self._list.itemWidget(self._list.item(i)), row_type)
        ]
        if ordered:
            self.sections_reordered.emit(ordered)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        row_type = TemplateSectionRow if self._mode == "template" else SectionSummaryRow
        for index in range(self._list.count()):
            widget = self._list.itemWidget(self._list.item(index))
            if isinstance(widget, row_type):
                widget.resize(self._list.viewport().width() - 4, widget.height())
