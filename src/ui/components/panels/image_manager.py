"""Gerenciador de imagens por drag-and-drop (sidebar / aba Fotografias)."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QFontMetrics, QPixmap, QResizeEvent
from PyQt6.QtWidgets import (
    QAbstractScrollArea,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.core.domain.ports import ReportImage
from src.ui.components.buttons import IconButton, SecondaryButton
from src.ui.components.icons import icon_close
from src.ui.components.panels._chrome import section_header
from src.ui.components.placeholder_field import PlaceholderTextEdit
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, caption_style, sidebar_panel_style
from src.ui.styles.helpers import workspace_drop_hint_style, workspace_image_list_style


class _ImageListRow(QFrame):
    remove_requested = pyqtSignal(object)
    _ROW_HEIGHT = 56
    _ROW_HEIGHT_COMPACT = 44
    _THUMB = 40
    _THUMB_COMPACT = 32

    def __init__(
        self,
        image: ReportImage,
        parent=None,
        *,
        compact: bool = False,
        show_status_line: bool = True,
    ) -> None:
        super().__init__(parent)
        self.image = image
        self._selected = False
        self._compact = compact
        self._show_status_line = show_status_line and not compact
        row_h = self._ROW_HEIGHT_COMPACT if compact else self._ROW_HEIGHT
        thumb = self._THUMB_COMPACT if compact else self._THUMB
        self.setMinimumHeight(row_h)
        self.setObjectName("ImageListRow")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 6, 6)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._thumb = QLabel()
        self._thumb.setFixedSize(thumb, thumb)
        self._thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumb.setStyleSheet(
            f"background: {PALETTE.bg_surface_alt}; border-radius: 4px; border: 1px solid {PALETTE.border_subtle};"
        )
        pixmap = QPixmap(str(image.image_path))
        if not pixmap.isNull():
            self._thumb.setPixmap(
                pixmap.scaled(
                    thumb,
                    thumb,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        meta = QVBoxLayout()
        meta.setContentsMargins(0, 0, 0, 0)
        meta.setSpacing(2)
        self._full_name = image.image_path.name
        self._name = QLabel(self._full_name)
        self._name.setToolTip(str(image.image_path))
        self._name.setWordWrap(False)
        self._name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._name.setStyleSheet(f"color: {PALETTE.text_primary}; background: transparent;")
        self._status = QLabel("")
        self._status.setStyleSheet(
            f"color: {PALETTE.text_muted}; font-size: {TYPOGRAPHY.size_caption}px; background: transparent;"
        )
        meta.addWidget(self._name)
        if self._show_status_line:
            meta.addWidget(self._status)

        self._remove_btn = IconButton(icon_close(), "Remover foto")
        self._remove_btn.setFixedSize(28, 28)
        self._remove_btn.setMinimumSize(28, 28)
        self._remove_btn.setIconSize(QSize(14, 14))
        self._remove_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.image))
        layout.addWidget(self._thumb)
        layout.addLayout(meta, stretch=1)
        layout.addWidget(self._remove_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        self.set_selected(False)

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        border = PALETTE.senai_blue_light if selected else PALETTE.border_subtle
        bg = "rgba(74, 111, 212, 0.16)" if selected else PALETTE.bg_surface
        self.setStyleSheet(
            f"QFrame#ImageListRow {{"
            f" background: {bg};"
            f" border: 1px solid {border};"
            f" border-radius: 8px;"
            f"}}"
        )
        self._status.setText(
            "Selecionada — duplo clique ou botão abaixo para editar"
            if selected
            else "Clique para selecionar"
        )
        if self._show_status_line:
            self._status.setStyleSheet(
                f"color: {PALETTE.senai_blue_light if selected else PALETTE.text_muted}; "
                f"font-size: {TYPOGRAPHY.size_caption}px; background: transparent;"
            )

    def _update_name_elide(self) -> None:
        available = self._name.width()
        if available <= 0:
            return
        metrics = QFontMetrics(self._name.font())
        self._name.setText(metrics.elidedText(self._full_name, Qt.TextElideMode.ElideRight, available))

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._update_name_elide()

    def sizeHint(self) -> QSize:  # noqa: N802
        height = self._ROW_HEIGHT_COMPACT if self._compact else self._ROW_HEIGHT
        return QSize(super().sizeHint().width(), height)


class ImageManagerPanel(QFrame):
    """Gerenciador de imagens por drag-and-drop (sidebar / aba Fotografias)."""

    image_dropped = pyqtSignal(Path)
    image_selected = pyqtSignal(object)
    image_edit_requested = pyqtSignal(object)
    image_remove_requested = pyqtSignal(object)
    image_caption_changed = pyqtSignal(object, str)
    choose_file_requested = pyqtSignal()
    bosello_picker_requested = pyqtSignal()

    def __init__(self, parent=None, *, show_header: bool = True, compact: bool = False, show_caption: bool = True, expand_list: bool = False) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._compact = compact
        self._expand_list = expand_list
        self._show_caption = show_caption
        self._drop_active = False
        self._selected_image: ReportImage | None = None
        self._loading_caption = False
        self._row_widgets: list[_ImageListRow] = []
        self._caption_debounce = QTimer(self)
        self._caption_debounce.setSingleShot(True)
        self._caption_debounce.setInterval(450)
        self._caption_debounce.timeout.connect(self._flush_caption)
        self._layout_sync_timer = QTimer(self)
        self._layout_sync_timer.setSingleShot(True)
        self._layout_sync_timer.timeout.connect(self._sync_list_item_widths)

        self._list = QListWidget()
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._list.setSpacing(6)
        self._list.setFrameShape(QFrame.Shape.NoFrame)
        self._list.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self._list.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding if (compact or expand_list) else QSizePolicy.Policy.Fixed,
        )
        self._list.itemClicked.connect(self._on_item_clicked)
        self._list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._list.currentItemChanged.connect(self._on_current_changed)

        self._drop_hint = QLabel("Solte imagens PNG ou JPG aqui")
        self._drop_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._drop_hint.setWordWrap(True)
        self._drop_hint.setMinimumHeight(48)

        self._choose_btn = SecondaryButton("+ Arquivo" if compact else "+ Escolher arquivo…")
        self._choose_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._choose_btn.clicked.connect(self.choose_file_requested.emit)

        self._bosello_btn = SecondaryButton("Bosello…" if compact else "Capturas Bosello…")
        self._bosello_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._bosello_btn.setVisible(False)
        self._bosello_btn.clicked.connect(self.bosello_picker_requested.emit)

        self._hint = QLabel("Fotos" if compact else "Fotos desta seção")
        self._hint.setObjectName("GlobalFieldLabel")
        self._hint.setWordWrap(True)

        self._empty_list_hint = QLabel("Nenhuma foto ainda — adicione pela área acima.")
        self._empty_list_hint.setObjectName("SidebarHint")
        self._empty_list_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_list_hint.setWordWrap(True)

        self._selection_block = QFrame()
        self._selection_block.setObjectName("GlobalFieldCard")
        selection_layout = QVBoxLayout(self._selection_block)
        selection_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        selection_layout.setSpacing(SPACING.xs)
        selection_layout.addWidget(self._hint)
        selection_layout.addWidget(self._empty_list_hint)
        selection_layout.addWidget(self._list, stretch=1 if (compact or expand_list) else 0)
        self._caption_label = QLabel("Legenda")
        self._caption_label.setObjectName("GlobalFieldLabel")
        self._caption_edit = PlaceholderTextEdit(multiline=False)
        self._caption_edit.set_text("")
        self._caption_edit.setEnabled(False)
        self._caption_edit.text_changed.connect(self._on_caption_changed)
        if show_caption:
            selection_layout.addWidget(self._caption_label)
            selection_layout.addWidget(self._caption_edit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._header = section_header("Fotografias")
        self._header.setVisible(show_header)
        layout.addWidget(self._header)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        pad = SPACING.sm if show_header else 0
        inner_layout.setContentsMargins(pad, SPACING.xs if show_header else 0, pad, pad)
        inner_layout.setSpacing(SPACING.sm)
        if show_header:
            hint_legacy = QLabel("Arraste imagens aqui ou clique na lista para selecionar.")
            hint_legacy.setObjectName("SidebarHint")
            hint_legacy.setWordWrap(True)
            hint_legacy.setStyleSheet(caption_style())
            inner_layout.addWidget(hint_legacy)
        self._toggle_add_btn = QPushButton("+ Adicionar fotos")
        self._toggle_add_btn.setVisible(compact)
        self._toggle_add_btn.clicked.connect(self._toggle_add_section)

        self._add_block = QWidget()
        add_block_layout = QVBoxLayout(self._add_block)
        add_block_layout.setContentsMargins(0, 0, 0, 0)
        add_block_layout.setSpacing(SPACING.xs)
        if compact:
            btn_row = QHBoxLayout()
            btn_row.setSpacing(SPACING.xs)
            btn_row.addWidget(self._choose_btn)
            btn_row.addWidget(self._bosello_btn)
            add_block_layout.addWidget(self._drop_hint)
            add_block_layout.addLayout(btn_row)
        else:
            add_block_layout.addWidget(self._drop_hint)
            add_block_layout.addWidget(self._choose_btn)
            add_block_layout.addWidget(self._bosello_btn)

        inner_layout.addWidget(self._toggle_add_btn)
        inner_layout.addWidget(self._add_block)
        inner_layout.addWidget(self._selection_block, stretch=1 if (compact or expand_list) else 0)
        if not compact and not expand_list:
            inner_layout.addStretch(1)
        layout.addWidget(inner, stretch=1)

        self.refresh_appearance()

    def _toggle_add_section(self) -> None:
        self._add_block.setVisible(not self._add_block.isVisible())

    def _row_height(self) -> int:
        return _ImageListRow._ROW_HEIGHT_COMPACT if self._compact else _ImageListRow._ROW_HEIGHT

    def selected_image(self) -> ReportImage | None:
        return self._selected_image

    def refresh_appearance(self) -> None:
        self.setStyleSheet(sidebar_panel_style())
        self._list.setStyleSheet(
            workspace_image_list_style()
            + "QListWidget::item { padding: 0px; margin: 0px; border: none; background: transparent; }"
        )
        self._empty_list_hint.setStyleSheet(caption_style())
        self._choose_btn.refresh_appearance()
        self._bosello_btn.refresh_appearance()
        self._apply_drop_hint_style()

    def set_bosello_captures_available(self, available: bool) -> None:
        self._bosello_btn.setVisible(available)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            self._drop_active = True
            self._apply_drop_hint_style()
            event.acceptProposedAction()

    def dragLeaveEvent(self, event) -> None:
        self._drop_active = False
        self._apply_drop_hint_style()

    def dropEvent(self, event: QDropEvent) -> None:
        self._drop_active = False
        self._apply_drop_hint_style()
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() in (".png", ".jpg", ".jpeg"):
                self.image_dropped.emit(path)
        event.acceptProposedAction()

    def _apply_drop_hint_style(self) -> None:
        self._drop_hint.setStyleSheet(workspace_drop_hint_style(active=self._drop_active))

    def is_caption_editing(self) -> bool:
        return self._show_caption and self._caption_edit.has_editor_focus()

    def render_images(self, images: list[ReportImage]) -> None:
        selected_path = (
            str(self._selected_image.image_path) if self._selected_image is not None else None
        )
        editing_caption = self.is_caption_editing()
        live_caption = self._caption_edit.get_text() if editing_caption else None

        self._list.clear()
        self._row_widgets.clear()
        has_images = len(images) > 0
        if self._compact:
            self._add_block.setVisible(not has_images)
            self._toggle_add_btn.setVisible(has_images)
            self._drop_hint.setMinimumHeight(36)
        else:
            self._drop_hint.setVisible(True)
        self._list.setVisible(has_images)
        self._empty_list_hint.setVisible(not has_images)
        self._hint.setVisible(True)
        self._caption_label.setVisible(has_images and self._show_caption)
        self._caption_edit.setVisible(has_images and self._show_caption)
        restore_row = 0
        for index, image in enumerate(images):
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, image)
            row = _ImageListRow(
                image,
                compact=self._compact,
                show_status_line=self._show_caption,
            )
            row.remove_requested.connect(self.image_remove_requested.emit)
            self._row_widgets.append(row)
            self._list.addItem(item)
            self._list.setItemWidget(item, row)
            if selected_path and str(image.image_path) == selected_path:
                restore_row = index
        self._sync_list_item_widths()
        if images:
            self._list.setCurrentRow(restore_row)
            self._select_image(
                images[restore_row],
                emit=True,
                preserve_caption=editing_caption,
                caption_override=live_caption,
            )
            if editing_caption:
                self._caption_edit.focus_editor()
        else:
            self._select_image(None, emit=True)
        self._sync_list_height()
        self.schedule_list_layout_sync()

    def schedule_list_layout_sync(self) -> None:
        """Recalcula largura das linhas após o layout da aba estar pronto."""
        self._layout_sync_timer.start(0)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._sync_list_item_widths()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.schedule_list_layout_sync()

    def _list_viewport_width(self) -> int:
        return max(1, self._list.viewport().width())

    def _sync_list_item_widths(self) -> None:
        width = self._list_viewport_width()
        row_h = self._row_height()
        for index in range(self._list.count()):
            item = self._list.item(index)
            if item is not None:
                item.setSizeHint(QSize(width, row_h))
            row = self._row_widgets[index] if index < len(self._row_widgets) else None
            if row is not None:
                row.setFixedWidth(width)
                row._update_name_elide()

    def _sync_list_height(self) -> None:
        count = self._list.count()
        if count == 0:
            self._list.setFixedHeight(0)
            return
        if self._compact or self._expand_list:
            self._list.setMinimumHeight(120)
            self._list.setMaximumHeight(16777215)
            return
        spacing = self._list.spacing()
        row_h = self._row_height()
        content_h = count * row_h + max(0, count - 1) * spacing + 4
        max_h = 180
        self._list.setFixedHeight(min(content_h, max_h))
        if content_h > max_h:
            self._list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            self._list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        image = item.data(Qt.ItemDataRole.UserRole)
        self._select_image(image, emit=True)

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        image = item.data(Qt.ItemDataRole.UserRole)
        if image is not None:
            self._select_image(image, emit=True)
            self.image_edit_requested.emit(image)

    def _on_current_changed(self, current: QListWidgetItem | None, _previous) -> None:
        if current is None:
            return
        image = current.data(Qt.ItemDataRole.UserRole)
        self._select_image(image, emit=True)

    def select_image_by_path(self, image_path: str, *, image_id: str = "") -> bool:
        from src.core.domain.image_workspace import image_matches_reference

        for index in range(self._list.count()):
            item = self._list.item(index)
            if item is None:
                continue
            image = item.data(Qt.ItemDataRole.UserRole)
            if image is not None and image_matches_reference(
                image,
                path=image_path,
                image_id=image_id,
            ):
                self._list.setCurrentRow(index)
                self._select_image(image, emit=True)
                return True
        return False

    def _select_image(
        self,
        image: ReportImage | None,
        *,
        emit: bool = False,
        preserve_caption: bool = False,
        caption_override: str | None = None,
    ) -> None:
        prev_path = (
            str(self._selected_image.image_path) if self._selected_image is not None else None
        )
        selected_path = str(image.image_path) if image is not None else None
        changed = prev_path != selected_path
        self._selected_image = image
        for row in self._row_widgets:
            row.set_selected(selected_path is not None and str(row.image.image_path) == selected_path)
        self._caption_edit.setEnabled(image is not None and self._show_caption)
        if not self._show_caption:
            if emit and changed:
                self.image_selected.emit(image)
            return
        if preserve_caption and not changed:
            if caption_override is not None and image is not None:
                image.caption = caption_override
        else:
            self._loading_caption = True
            self._caption_edit.set_text(
                image.caption if image is not None else "",
                force=True,
            )
            self._loading_caption = False
        if emit and changed:
            self.image_selected.emit(image)

    def _on_caption_changed(self, _text: str) -> None:
        if self._loading_caption or self._selected_image is None:
            return
        self._caption_debounce.start()

    def _flush_caption(self) -> None:
        if self._selected_image is None:
            return
        self.image_caption_changed.emit(self._selected_image, self._caption_edit.get_text().strip())
