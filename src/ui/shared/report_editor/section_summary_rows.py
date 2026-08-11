"""Widgets de linha do sumário de seções (workspace e template)."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.core.domain.section_schema import PROTECTED_SECTION_IDS, SECTION_DEFINITIONS
from src.ui.components.icons import icon_edit, icon_grip, icon_lock, icon_plus, icon_trash
from src.ui.shared.report_editor.section_order_rules import is_sidebar_section_draggable
from src.ui.styles import SPACING

_PROTECTED_IDS = frozenset(s.id for s in SECTION_DEFINITIONS)
_ROW_HEIGHT = 52
_ACCENT_WIDTH = 3
_ACTIONS_WIDTH = 76
_GRIP_WIDTH = 16


def _repolish(widget: QWidget) -> None:
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)


def _summary_list_parent(widget: QWidget):
    parent = widget.parentWidget()
    while parent is not None:
        if parent.objectName() == "SectionSummaryList":
            return parent
        parent = parent.parentWidget()
    return None


def _transparent_panel(widget: QWidget) -> None:
    widget.setAutoFillBackground(False)
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)


class _SummaryRowChromeMixin:
    """Hover/ativo via propriedades — :hover em QSS falha em itemWidget de QListWidget."""

    def _init_summary_row_chrome(self) -> None:
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setProperty("hovered", "false")

    def enterEvent(self, event) -> None:  # noqa: N802
        parent_list = _summary_list_parent(self)
        if parent_list is None or not parent_list.property("dragging"):
            self.setProperty("hovered", "true")
            _repolish(self)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.setProperty("hovered", "false")
        _repolish(self)
        super().leaveEvent(event)


def _drag_handle(section_id: str) -> QWidget:
    if is_sidebar_section_draggable(section_id):
        grip = QLabel()
        grip.setPixmap(icon_grip().pixmap(14, 14))
        grip.setObjectName("SectionSummaryGrip")
        grip.setToolTip("Arraste para reordenar")
        grip.setFixedSize(_GRIP_WIDTH, 24)
        grip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return grip
    spacer = QWidget()
    spacer.setFixedSize(_GRIP_WIDTH, 24)
    return spacer


class TemplateSectionRow(_SummaryRowChromeMixin, QFrame):
    """Linha do sumário no modo template — toggle enabled + seleção para editar."""

    click_requested = pyqtSignal(str)
    enabled_changed = pyqtSignal(str, bool)
    delete_requested = pyqtSignal(str)
    protected_toggle_blocked = pyqtSignal()

    def __init__(self, section: dict, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("SectionSummaryRow")
        self.setMinimumWidth(0)
        self.section_id = section["id"]
        self._full_title = section.get("display_title") or section.get("title", section["id"])
        self._protected = bool(section.get("protected")) or self.section_id in PROTECTED_SECTION_IDS
        self._is_custom = bool(section.get("custom")) or (
            self.section_id.startswith("custom_") and self.section_id not in PROTECTED_SECTION_IDS
        )
        enabled = section.get("enabled", True)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, SPACING.sm, 0)
        root.setSpacing(0)

        self._accent = QFrame()
        self._accent.setObjectName("SectionSummaryAccent")
        self._accent.setFixedWidth(_ACCENT_WIDTH)
        self._accent.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        body = QWidget()
        body.setMinimumWidth(0)
        body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        _transparent_panel(body)
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(SPACING.sm, SPACING.xs, SPACING.xs, SPACING.xs)
        body_layout.setSpacing(SPACING.sm)

        body_layout.addWidget(_drag_handle(self.section_id))

        if self._protected:
            self._enabled_cb = None
            lock_btn = QToolButton()
            lock_btn.setObjectName("SectionSummaryLock")
            lock_btn.setAutoRaise(True)
            lock_btn.setFixedSize(24, 24)
            lock_btn.setIcon(icon_lock())
            lock_btn.setToolTip("Sempre incluída no relatório — clique para saber mais")
            lock_btn.clicked.connect(self.protected_toggle_blocked.emit)
            body_layout.addWidget(lock_btn)
            self.setProperty("fixed", "true")
        else:
            self._enabled_cb = QCheckBox()
            self._enabled_cb.setObjectName("SectionSummaryEnabled")
            self._enabled_cb.setChecked(enabled)
            self._enabled_cb.setToolTip("Incluir seção no template")
            self._enabled_cb.stateChanged.connect(self._on_enabled_changed)
            body_layout.addWidget(self._enabled_cb)

        self._title_label = QLabel(self._full_title)
        self._title_label.setToolTip(self._full_title)
        self._title_label.setObjectName("SectionSummaryTitle")
        self._title_label.setWordWrap(False)
        self._title_label.setMinimumWidth(0)
        self._title_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

        text_col = QWidget()
        text_col.setMinimumWidth(0)
        text_col.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        _transparent_panel(text_col)
        text_layout = QVBoxLayout(text_col)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(SPACING.xs)
        title_row.addWidget(self._title_label, stretch=1)
        text_layout.addLayout(title_row)
        if self._protected:
            meta = QLabel("Obrigatória")
            meta.setObjectName("SectionSummaryMeta")
            text_layout.addWidget(meta)
        elif not enabled:
            meta = QLabel("Desativada")
            meta.setObjectName("SectionSummaryMeta")
            text_layout.addWidget(meta)

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

        self._init_summary_row_chrome()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_active(False)
        if self._protected:
            self.style().unpolish(self)
            self.style().polish(self)
        self._elide_title()

    def _on_enabled_changed(self, _state: int) -> None:
        if self._enabled_cb is None:
            return
        self.enabled_changed.emit(self.section_id, self._enabled_cb.isChecked())

    def set_enabled(self, enabled: bool) -> None:
        if self._enabled_cb is None:
            return
        self._enabled_cb.blockSignals(True)
        self._enabled_cb.setChecked(enabled)
        self._enabled_cb.blockSignals(False)

    def _elide_title(self) -> None:
        control_w = 24 if self._protected else 28
        margins = SPACING.sm * 3 + _ACCENT_WIDTH + control_w + _GRIP_WIDTH
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


class SectionSummaryRow(_SummaryRowChromeMixin, QFrame):
    """Linha do sumário — clique navega; duplo-clique ou lápis edita."""

    click_requested = pyqtSignal(str)
    edit_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    enabled_changed = pyqtSignal(str, bool)
    protected_toggle_blocked = pyqtSignal()

    def __init__(
        self,
        section: dict,
        photo_count: int,
        *,
        show_enable_toggle: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("SectionSummaryRow")
        self.setMinimumWidth(0)
        self.section_id = section["id"]
        self._photo_count = photo_count
        self._full_title = section.get("display_title") or section.get("title", section["id"])
        self._has_modified_dot = bool(section.get("has_overrides"))
        self._show_enable_toggle = show_enable_toggle
        self._protected = bool(section.get("protected")) or self.section_id in PROTECTED_SECTION_IDS
        enabled = section.get("enabled", True)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, SPACING.sm, 0)
        root.setSpacing(0)

        self._accent = QFrame()
        self._accent.setObjectName("SectionSummaryAccent")
        self._accent.setFixedWidth(_ACCENT_WIDTH)
        self._accent.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        body = QWidget()
        body.setMinimumWidth(0)
        body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        _transparent_panel(body)
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(SPACING.sm, SPACING.xs, SPACING.xs, SPACING.xs)
        body_layout.setSpacing(SPACING.sm)

        body_layout.addWidget(_drag_handle(self.section_id))

        self._enabled_cb = None
        if show_enable_toggle:
            if self._protected:
                lock_btn = QToolButton()
                lock_btn.setObjectName("SectionSummaryLock")
                lock_btn.setAutoRaise(True)
                lock_btn.setFixedSize(24, 24)
                lock_btn.setIcon(icon_lock())
                lock_btn.setToolTip("Sempre incluída no relatório — clique para saber mais")
                lock_btn.clicked.connect(self.protected_toggle_blocked.emit)
                body_layout.addWidget(lock_btn)
                self.setProperty("fixed", "true")
            else:
                self._enabled_cb = QCheckBox()
                self._enabled_cb.setObjectName("SectionSummaryEnabled")
                self._enabled_cb.setChecked(enabled)
                self._enabled_cb.setToolTip("Incluir seção no relatório")
                self._enabled_cb.stateChanged.connect(self._on_enabled_changed)
                body_layout.addWidget(self._enabled_cb)

        self._title_label = QLabel(self._full_title)
        text_col = QWidget()
        text_col.setMinimumWidth(0)
        text_col.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        _transparent_panel(text_col)
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

        self._title_label.setToolTip(self._full_title)
        self._title_label.setObjectName("SectionSummaryTitle")
        self._title_label.setWordWrap(False)
        self._title_label.setMinimumWidth(0)
        self._title_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        title_row.addWidget(self._title_label, stretch=1)
        text_layout.addLayout(title_row)

        meta_parts: list[str] = []
        if self._protected:
            meta_parts.append("Obrigatória")
        if photo_count > 0:
            meta_parts.append(f"{photo_count} foto{'s' if photo_count != 1 else ''}")
        if section.get("has_graphics") or "graphics" in (section.get("media_kinds") or []):
            meta_parts.append("Gráficos")
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
        _transparent_panel(self._actions_host)
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

        self._init_summary_row_chrome()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_active(False)
        if self._protected:
            self.style().unpolish(self)
            self.style().polish(self)
        self._elide_title()

    def _on_enabled_changed(self, _state: int) -> None:
        if self._enabled_cb is None:
            return
        self.enabled_changed.emit(self.section_id, self._enabled_cb.isChecked())

    def _elide_title(self) -> None:
        dot_w = 12 if self._has_modified_dot else 0
        control_w = 24 if self._protected and self._show_enable_toggle else (28 if self._enabled_cb is not None else 0)
        margins = SPACING.sm * 3 + _ACCENT_WIDTH + control_w + _GRIP_WIDTH
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


class AddSectionRow(QFrame):
    clicked = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("SectionSummaryAddRow")
        self.setMinimumHeight(_ROW_HEIGHT)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.xs, SPACING.sm, SPACING.xs)
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
        return QSize(200, _ROW_HEIGHT)
