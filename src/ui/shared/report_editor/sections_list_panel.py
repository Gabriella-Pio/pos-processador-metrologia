"""Lista reordenável de seções — compartilhada entre workspace e templates."""
from __future__ import annotations

from PyQt6.QtCore import QEvent, QPoint, Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)
from src.core.domain.ports import ReportImage
from src.ui.shared.report_editor.section_order_rules import (
    is_sidebar_section_draggable,
    validate_sidebar_order,
)
from src.ui.shared.report_editor.section_summary_rows import (
    AddSectionRow,
    SectionSummaryRow,
    TemplateSectionRow,
)
from src.ui.shared.report_editor.sidebar_chrome import sidebar_section_header
from src.ui.styles import SPACING, PALETTE, caption_style, sidebar_panel_style


def _notice_style(*, padding: str = "6px 8px") -> str:
    return (
        f"color: {PALETTE.senai_orange}; background: {PALETTE.senai_orange_glow}; "
        f"border: 1px solid {PALETTE.senai_orange}; border-radius: 8px; padding: {padding};"
    )


class _DropLineOverlay(QWidget):
    """Barra laranja persistente entre itens da lista (filho do viewport)."""

    _HEIGHT = 4
    _MARGIN = 8

    def __init__(self, viewport: QWidget) -> None:
        super().__init__(viewport)
        self._viewport = viewport
        self.setObjectName("SectionDropLine")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setFixedHeight(self._HEIGHT)
        self.hide()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(PALETTE.senai_orange))
        painter.drawRoundedRect(self.rect(), 2, 2)

    def place_at_viewport_y(self, viewport_y: int) -> None:
        width = max(48, self._viewport.width() - 2 * self._MARGIN)
        y = viewport_y - self._HEIGHT // 2
        self.setGeometry(self._MARGIN, y, width, self._HEIGHT)
        self.show()
        self.raise_()


class SectionSummaryList(QListWidget):
    """Lista com reordenação linear — indicador de linha, sem highlight de 'caixa'."""

    _ROW_TYPES = (SectionSummaryRow, TemplateSectionRow)

    def __init__(self, panel: "SectionsListPanel", parent=None) -> None:
        super().__init__(parent)
        self._panel = panel
        self._drag_source_row = -1
        self._hovered_row: SectionSummaryRow | TemplateSectionRow | None = None
        self._last_drop_viewport_y: int | None = None
        self._drop_line = _DropLineOverlay(self.viewport())
        self.setDropIndicatorShown(False)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.viewport().setAutoFillBackground(False)
        self.viewport().installEventFilter(self)
        self.setProperty("dragging", False)

    def _set_dragging(self, dragging: bool) -> None:
        self.setProperty("dragging", dragging)
        self.style().unpolish(self)
        self.style().polish(self)
        if dragging:
            self._clear_row_hovers()

    def _set_row_hovered(self, row: SectionSummaryRow | TemplateSectionRow | None, hovered: bool) -> None:
        state = "true" if hovered else "false"
        if str(row.property("hovered")) == state:
            return
        row.setProperty("hovered", state)
        row.style().unpolish(row)
        row.style().polish(row)

    def _clear_row_hovers(self) -> None:
        self._hovered_row = None
        for index in range(self.count()):
            item = self.item(index)
            if item is None:
                continue
            widget = self.itemWidget(item)
            if isinstance(widget, self._ROW_TYPES):
                self._set_row_hovered(widget, False)

    def _row_at_viewport_pos(self, viewport_pos: QPoint) -> SectionSummaryRow | TemplateSectionRow | None:
        item = self.itemAt(self.viewport().mapTo(self, viewport_pos))
        if item is None:
            return None
        widget = self.itemWidget(item)
        if isinstance(widget, self._ROW_TYPES):
            return widget
        return None

    def _update_hover_at(self, viewport_pos: QPoint) -> None:
        if bool(self.property("dragging")):
            return
        row = self._row_at_viewport_pos(viewport_pos)
        if row is self._hovered_row:
            return
        if self._hovered_row is not None:
            self._set_row_hovered(self._hovered_row, False)
        self._hovered_row = row
        if row is not None:
            self._set_row_hovered(row, True)

    def clear(self) -> None:
        self._hovered_row = None
        super().clear()

    def _end_drag_visuals(self) -> None:
        self._set_dragging(False)
        self._clear_drop_line()

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if obj is self.viewport():
            event_type = event.type()
            if event_type == QEvent.Type.MouseMove:
                self._update_hover_at(event.position().toPoint())
            elif event_type == QEvent.Type.Leave:
                self._clear_row_hovers()
            elif event_type == QEvent.Type.DragMove:
                self._update_drop_line(int(event.position().y()))
            elif event_type in (QEvent.Type.DragLeave, QEvent.Type.Drop):
                self._clear_drop_line()
        return super().eventFilter(obj, event)

    def _viewport_pos(self, event) -> QPoint:
        """Converte posição do drag para coordenadas do viewport."""
        return self.viewport().mapFrom(self, event.position().toPoint())

    def _is_add_row_index(self, row: int) -> bool:
        item = self.item(row)
        if item is None:
            return False
        return isinstance(self.itemWidget(item), AddSectionRow)

    def _update_drop_line(self, pos_y: int) -> None:
        best_row: int | None = None
        best_dist = float("inf")
        insert_above = True
        for row in range(self.count()):
            if self._is_add_row_index(row):
                continue
            item = self.item(row)
            if item is None:
                continue
            rect = self.visualItemRect(item)
            dist = abs(pos_y - rect.center().y())
            if dist < best_dist:
                best_dist = dist
                best_row = row
                insert_above = pos_y < rect.center().y()
        if best_row is None:
            self._clear_drop_line()
        else:
            rect = self.visualItemRect(self.item(best_row))
            y = rect.top() if insert_above else rect.bottom()
            self._last_drop_viewport_y = y
            self._drop_line.place_at_viewport_y(y)

    def _clear_drop_line(self) -> None:
        self._last_drop_viewport_y = None
        self._drop_line.hide()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self._last_drop_viewport_y is not None:
            self._drop_line.place_at_viewport_y(self._last_drop_viewport_y)

    def startDrag(self, supportedActions) -> None:  # noqa: N802
        self._drag_source_row = self.currentRow()
        self._set_dragging(True)
        try:
            super().startDrag(supportedActions)
        finally:
            self._end_drag_visuals()

    def dragMoveEvent(self, event) -> None:  # noqa: N802
        vp = self._viewport_pos(event)
        target = self.indexAt(vp)
        if target.isValid() and self._is_add_row_index(target.row()):
            self._clear_drop_line()
            event.ignore()
            return
        super().dragMoveEvent(event)
        if 0 <= self._drag_source_row < self.count():
            self.setCurrentRow(self._drag_source_row)
        self._update_drop_line(vp.y())

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.source() is self:
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self._end_drag_visuals()
        super().dragLeaveEvent(event)

    def dropEvent(self, event) -> None:  # noqa: N802
        vp = self._viewport_pos(event)
        target = self.indexAt(vp)
        if target.isValid() and self._is_add_row_index(target.row()):
            event.ignore()
            return
        super().dropEvent(event)
        self._end_drag_visuals()
        self._panel._pin_add_row_last()
        if not self._panel._loading:
            self._panel._emit_reorder()


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
        self._pending_list_scroll: int | None = None

        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.setInterval(280)
        self._click_timer.timeout.connect(self._emit_single_click)

        self._hint = QLabel(
            "Marque para incluir no template · clique para o preview · lápis ou duplo-clique para editar"
            if self._mode == "template"
            else "Marque para incluir no relatório · clique no preview · duplo-clique para editar"
        )
        self._hint.setObjectName("SidebarHint")
        self._hint.setWordWrap(True)

        self._hint_default = self._hint.text()
        self._hint_timer = QTimer(self)
        self._hint_timer.setSingleShot(True)
        self._hint_timer.timeout.connect(self._restore_hint_text)

        self._list = SectionSummaryList(self)
        self._list.setObjectName("SectionSummaryList")
        self._list.setMinimumWidth(0)
        self._list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._list.setUniformItemSizes(True)
        self._list.setSpacing(SPACING.sm)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(SPACING.md, SPACING.xs, SPACING.md, SPACING.md)
        inner_layout.setSpacing(SPACING.sm)
        inner_layout.addWidget(self._hint)
        inner_layout.addWidget(self._list, stretch=1)

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

    def _show_notice(self, message: str, duration_ms: int = 4500) -> None:
        if not self._hint_timer.isActive():
            self._hint_default = self._hint.text()
        self._hint.setText(f"⚠ {message}")
        self._hint.setStyleSheet(caption_style() + " " + _notice_style())
        self._hint_timer.start(duration_ms)

    def _restore_hint_text(self) -> None:
        self._hint.setText(self._hint_default)
        self._hint.setStyleSheet(caption_style())

    def render_sections(self, sections: list[dict]) -> None:
        self._sections = sections
        count = len(sections)
        if self._mode == "template":
            enabled_count = sum(1 for s in sections if s.get("enabled", True))
            self._hint.setText(
                f"{enabled_count} de {count} seç{'ões' if count != 1 else 'ão'} ativas · "
                "≡ arraste para reordenar · clique para o preview · lápis ou duplo-clique para editar"
            )
        else:
            enabled_count = sum(1 for s in sections if s.get("enabled", True))
            self._hint.setText(
                f"{enabled_count} de {count} seç{'ões' if count != 1 else 'ão'} ativas · "
                "≡ arraste para reordenar · marque para incluir no PDF · "
                "clique para preview · duplo-clique para editar"
            )
        self._hint_default = self._hint.text()
        self._hint.setStyleSheet(caption_style())
        self._rebuild_rows()

    def set_active_section(self, section_id: str | None) -> None:
        self._active_section_id = section_id
        row_types = (SectionSummaryRow, TemplateSectionRow)
        for index in range(self._list.count()):
            item = self._list.item(index)
            widget = self._list.itemWidget(item)
            if isinstance(widget, row_types):
                widget.set_active(widget.section_id == section_id)

    def _append_add_row(self) -> None:
        row = AddSectionRow(self._list)
        row.clicked.connect(self.add_custom_section_requested.emit)
        if self._mode == "template":
            row.setToolTip("Adicionar seção personalizada ao template")
        else:
            row.setToolTip("Nova seção — editar e escolher do catálogo ou começar do zero")
        add_item = QListWidgetItem()
        add_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        add_item.setSizeHint(row.sizeHint())
        self._list.addItem(add_item)
        self._list.setItemWidget(add_item, row)

    def _pin_add_row_last(self) -> None:
        for index in range(self._list.count()):
            item = self._list.item(index)
            widget = self._list.itemWidget(item) if item is not None else None
            if isinstance(widget, AddSectionRow):
                if index == self._list.count() - 1:
                    return
                taken = self._list.takeItem(index)
                self._list.addItem(taken)
                return

    def _rebuild_rows(self) -> None:
        current_scroll = self._list.verticalScrollBar().value()
        if self._pending_list_scroll is None:
            self._pending_list_scroll = current_scroll
        self._loading = True
        self._list.blockSignals(True)
        self._list.clear()
        for section in self._sections:
            section_id = section["id"]
            if self._mode == "template":
                row = TemplateSectionRow(section)
                row.click_requested.connect(self._on_row_clicked)
                row.edit_requested.connect(self._on_row_edit_requested)
                row.enabled_changed.connect(self.section_enabled_changed.emit)
                row.delete_requested.connect(self.section_delete_requested.emit)
                row.protected_toggle_blocked.connect(self._on_protected_toggle_blocked)
            else:
                photos = len(self._images_by_section.get(section_id, []))
                row = SectionSummaryRow(section, photos, show_enable_toggle=True)
                row.click_requested.connect(self._on_row_clicked)
                row.edit_requested.connect(self._on_row_edit_requested)
                row.delete_requested.connect(self.section_delete_requested.emit)
                row.enabled_changed.connect(self.section_enabled_changed.emit)
                row.protected_toggle_blocked.connect(self._on_protected_toggle_blocked)
            row.set_active(section_id == self._active_section_id)
            item = QListWidgetItem()
            flags = (
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsDropEnabled
            )
            if is_sidebar_section_draggable(section_id):
                flags |= Qt.ItemFlag.ItemIsDragEnabled
            item.setFlags(flags)
            item.setSizeHint(row.sizeHint())
            self._list.addItem(item)
            self._list.setItemWidget(item, row)
        self._append_add_row()
        self._list.setCurrentItem(None)
        self._list.blockSignals(False)
        self._loading = False
        self._restore_list_scroll()

    def _restore_list_scroll(self) -> None:
        pos = self._pending_list_scroll
        if pos is None:
            return
        self._list.verticalScrollBar().setValue(pos)
        QTimer.singleShot(0, self._apply_pending_list_scroll)

    def _apply_pending_list_scroll(self) -> None:
        pos = self._pending_list_scroll
        self._pending_list_scroll = None
        if pos is None:
            return
        self._list.verticalScrollBar().setValue(pos)

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

    def _on_protected_toggle_blocked(self) -> None:
        self._show_notice(
            "Esta seção é obrigatória no relatório e não pode ser desativada."
        )

    def _emit_reorder(self, *_args) -> None:
        if self._loading:
            return
        self._pin_add_row_last()
        row_type = TemplateSectionRow if self._mode == "template" else SectionSummaryRow
        ordered: list[str] = []
        for i in range(self._list.count()):
            widget = self._list.itemWidget(self._list.item(i))
            if isinstance(widget, row_type):
                ordered.append(widget.section_id)
        if len(ordered) != len(self._sections):
            QTimer.singleShot(0, self._restore_section_order)
            return
        valid, message = validate_sidebar_order(ordered)
        if not valid:
            self._show_notice(message)
            QTimer.singleShot(0, self._restore_section_order)
            return
        self.sections_reordered.emit(ordered)

    def _restore_section_order(self) -> None:
        self.render_sections(self._sections)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        row_type = TemplateSectionRow if self._mode == "template" else SectionSummaryRow
        for index in range(self._list.count()):
            widget = self._list.itemWidget(self._list.item(index))
            if isinstance(widget, (row_type, AddSectionRow)):
                widget.resize(self._list.viewport().width() - 4, widget.height())
