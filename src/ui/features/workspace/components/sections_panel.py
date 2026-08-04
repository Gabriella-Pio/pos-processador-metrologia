"""Sumário compacto — seções reordenáveis, ícones de mídia e subseções."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.core.domain.ports import ReportImage
from src.core.domain.section_schema import SECTION_DEFINITIONS
from src.core.domain.table_row_registry import NUMBERED_SECTION_IDS
from src.ui.components.buttons import SecondaryButton
from src.ui.components.icons import icon_chart, icon_chevron_down, icon_chevron_up, icon_edit, icon_image, icon_table
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, caption_style
from src.ui.features.workspace.components.section_field_schema import get_media_blocks

_PROTECTED_IDS = frozenset(s.id for s in SECTION_DEFINITIONS)

_MEDIA_ICONS = {
    "photos": icon_image,
    "graphics": icon_chart,
    "tables": icon_table,
}


class _MediaSubRow(QFrame):
    def __init__(self, label: str, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.lg, 2, SPACING.sm, 2)
        layout.setSpacing(SPACING.xs)
        icon = QLabel()
        icon.setPixmap(icon_image().pixmap(14, 14))
        text = QLabel(label)
        text.setStyleSheet(caption_style())
        layout.addWidget(icon)
        layout.addWidget(text, stretch=1)


class _SectionRow(QFrame):
    navigate_requested = pyqtSignal(str)
    edit_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)

    def __init__(self, section: dict, images: list[ReportImage], parent=None) -> None:
        super().__init__(parent)
        self.section_id = section["id"]
        self._expanded = False
        self._images = images

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        header_layout.setSpacing(SPACING.xs)

        self._drag_handle = QLabel("⠿")
        self._drag_handle.setToolTip("Arraste para reordenar")
        self._drag_handle.setFixedWidth(14)

        self._expand_btn = QToolButton()
        self._expand_btn.setAutoRaise(True)
        self._expand_btn.setFixedSize(22, 22)
        self._expand_btn.clicked.connect(self._toggle_expand)
        self._update_expand_icon()

        display_title = section.get("display_title") or section.get("title", section["id"])
        self._title_btn = QPushButton(display_title)
        self._title_btn.setFlat(True)
        self._title_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._title_btn.clicked.connect(
            lambda: self.navigate_requested.emit(self.section_id)
        )
        self._title_btn.setStyleSheet(
            f"QPushButton {{ text-align: left; color: {PALETTE.text_primary}; "
            f"font-size: {TYPOGRAPHY.size_body + 1}px; font-weight: {TYPOGRAPHY.weight_medium}; "
            f"background: transparent; border: none; padding: 2px 0; }}"
            f"QPushButton:hover {{ color: {PALETTE.senai_blue_light}; }}"
        )

        if section.get("has_overrides"):
            dot = QLabel("●")
            keys = section.get("override_keys") or []
            tooltip = "Campos alterados: " + ", ".join(keys) if keys else "Seção com alterações"
            dot.setToolTip(tooltip)
            dot.setStyleSheet(f"color: {PALETTE.senai_orange}; font-size: 10px;")
            header_layout.addWidget(dot)

        header_layout.addWidget(self._drag_handle)
        header_layout.addWidget(self._expand_btn)
        header_layout.addWidget(self._title_btn, stretch=1)

        self._media_badges: list[QToolButton] = []
        for media in get_media_blocks(self.section_id):
            badge = QToolButton()
            badge.setAutoRaise(True)
            badge.setIcon(_MEDIA_ICONS[media.kind]())
            badge.setToolTip(media.label)
            badge.setEnabled(self._media_count(media.kind) > 0)
            header_layout.addWidget(badge)
            self._media_badges.append(badge)

        self._edit_btn = QToolButton()
        self._edit_btn.setAutoRaise(True)
        self._edit_btn.setIcon(icon_edit())
        self._edit_btn.setToolTip("Editar seção")
        self._edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.section_id))
        header_layout.addWidget(self._edit_btn)

        is_custom = section.get("custom", False) or str(section["id"]).startswith("custom_")
        self._delete_btn = SecondaryButton("×")
        self._delete_btn.setFixedSize(28, 28)
        self._delete_btn.setVisible(is_custom and section["id"] not in _PROTECTED_IDS)
        self._delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.section_id))
        header_layout.addWidget(self._delete_btn)

        root.addWidget(header)

        self._subs_host = QWidget()
        self._subs_layout = QVBoxLayout(self._subs_host)
        self._subs_layout.setContentsMargins(0, 0, 0, 0)
        self._subs_host.setVisible(False)
        root.addWidget(self._subs_host)

        self._rebuild_subsections()
        self._expand_btn.setVisible(self._has_subsections())

    def _media_count(self, kind: str) -> int:
        return len(self._images) if kind == "photos" else 0

    def _has_subsections(self) -> bool:
        return len(self._images) > 0

    def _rebuild_subsections(self) -> None:
        while self._subs_layout.count():
            item = self._subs_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for image in self._images:
            self._subs_layout.addWidget(_MediaSubRow(image.image_path.name))

    def update_images(self, images: list[ReportImage]) -> None:
        self._images = images
        self._rebuild_subsections()
        self._expand_btn.setVisible(self._has_subsections())

    def set_active(self, active: bool) -> None:
        border = PALETTE.senai_blue_light if active else PALETTE.border_subtle
        self.setStyleSheet(
            f"QFrame {{ background: {PALETTE.bg_surface_alt}; border: 1px solid {border}; border-radius: 6px; }}"
        )

    def _toggle_expand(self) -> None:
        if not self._has_subsections():
            return
        self._expanded = not self._expanded
        self._subs_host.setVisible(self._expanded)
        self._update_expand_icon()

    def _update_expand_icon(self) -> None:
        icon = icon_chevron_down if not self._expanded else icon_chevron_up
        self._expand_btn.setIcon(icon())
        self._expand_btn.setEnabled(self._has_subsections())


    def sizeHint(self):
        from PyQt6.QtCore import QSize
        hint = super().sizeHint()
        return QSize(hint.width(), max(hint.height(), 48))


class _AddSectionRow(QFrame):
    clicked = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"QFrame {{ background: transparent; border: 1px dashed {PALETTE.border_subtle}; "
            f"border-radius: 6px; }}"
            f"QFrame:hover {{ border-color: {PALETTE.senai_blue_light}; background: {PALETTE.bg_surface_alt}; }}"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        label = QLabel("+ Nova seção")
        label.setStyleSheet(
            f"color: {PALETTE.text_secondary}; font-size: {TYPOGRAPHY.size_body}px; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(label)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def sizeHint(self):
        from PyQt6.QtCore import QSize
        return QSize(200, 44)


class SectionsPanel(QFrame):
    section_navigated = pyqtSignal(str)
    section_edit_requested = pyqtSignal(str)
    section_delete_requested = pyqtSignal(str)
    sections_reordered = pyqtSignal(list)
    add_custom_section_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("WorkspaceSidebarPanel")
        self._sections: list[dict] = []
        self._images_by_section: dict[str, list[ReportImage]] = {}
        self._active_section_id: str | None = None
        self._loading = False

        self._list = QListWidget()
        self._list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self._list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._list.setSpacing(8)
        self._list.model().rowsMoved.connect(self._emit_reorder)

        self._add_row = _AddSectionRow()
        self._add_row.clicked.connect(self.add_custom_section_requested.emit)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        outer.setSpacing(SPACING.sm)
        outer.addWidget(self._list, stretch=1)
        outer.addWidget(self._add_row)

    def refresh_appearance(self) -> None:
        pass

    def set_section_images(self, images: list[ReportImage]) -> None:
        self._images_by_section = {}
        for image in images:
            self._images_by_section.setdefault(image.section_id, []).append(image)
        for index in range(self._list.count()):
            item = self._list.item(index)
            widget = self._list.itemWidget(item)
            if isinstance(widget, _SectionRow):
                widget.update_images(self._images_by_section.get(widget.section_id, []))

    def render_sections(self, sections: list[dict]) -> None:
        self._sections = sections
        self._rebuild_rows()

    def set_active_section(self, section_id: str | None) -> None:
        self._active_section_id = section_id
        for index in range(self._list.count()):
            item = self._list.item(index)
            widget = self._list.itemWidget(item)
            if isinstance(widget, _SectionRow):
                widget.set_active(widget.section_id == section_id)

    def _rebuild_rows(self) -> None:
        self._loading = True
        self._list.clear()
        for section in self._sections:
            section_id = section["id"]
            images = self._images_by_section.get(section_id, [])
            row = _SectionRow(section, images)
            row.navigate_requested.connect(self.section_navigated.emit)
            row.edit_requested.connect(self.section_edit_requested.emit)
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

    def _emit_reorder(self, *_args) -> None:
        if self._loading:
            return
        ordered: list[str] = []
        for index in range(self._list.count()):
            item = self._list.item(index)
            widget = self._list.itemWidget(item)
            if isinstance(widget, _SectionRow):
                ordered.append(widget.section_id)
        if ordered:
            self.sections_reordered.emit(ordered)
