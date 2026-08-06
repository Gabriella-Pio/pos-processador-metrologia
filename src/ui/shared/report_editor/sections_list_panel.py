"""Lista reordenável de seções — compartilhada entre workspace e templates."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.domain.ports import ReportImage
from src.ui.shared.report_editor.section_summary_rows import (
    AddSectionRow,
    SectionSummaryRow,
    TemplateSectionRow,
)
from src.ui.shared.report_editor.sidebar_chrome import sidebar_section_header
from src.ui.styles import SPACING, caption_style, sidebar_panel_style


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
            else "Marque para incluir no relatório · clique no preview · duplo-clique para editar"
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

        self._add_row = AddSectionRow()
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
            enabled_count = sum(1 for s in sections if s.get("enabled", True))
            self._hint.setText(
                f"{enabled_count} de {count} seção{'ões' if count != 1 else ''} ativas · "
                "marque para incluir no PDF · clique para preview · duplo-clique para editar"
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
                row = SectionSummaryRow(section, photos, show_enable_toggle=True)
                row.click_requested.connect(self._on_row_clicked)
                row.edit_requested.connect(self._on_row_edit_requested)
                row.delete_requested.connect(self.section_delete_requested.emit)
                row.enabled_changed.connect(self.section_enabled_changed.emit)
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
