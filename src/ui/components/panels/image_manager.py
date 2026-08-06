"""Gerenciador de imagens por drag-and-drop (sidebar / aba Fotografias)."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from PyQt6.QtWidgets import (
    QAbstractScrollArea,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
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
    _THUMB = 40

    def __init__(self, image: ReportImage, parent=None) -> None:
        super().__init__(parent)
        self.image = image
        self._selected = False
        self.setMinimumHeight(self._ROW_HEIGHT)
        self.setObjectName("ImageListRow")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 6, 6)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._thumb = QLabel()
        self._thumb.setFixedSize(self._THUMB, self._THUMB)
        self._thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumb.setStyleSheet(
            f"background: {PALETTE.bg_surface_alt}; border-radius: 4px; border: 1px solid {PALETTE.border_subtle};"
        )
        pixmap = QPixmap(str(image.image_path))
        if not pixmap.isNull():
            self._thumb.setPixmap(
                pixmap.scaled(
                    self._THUMB,
                    self._THUMB,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        meta = QVBoxLayout()
        meta.setContentsMargins(0, 0, 0, 0)
        meta.setSpacing(2)
        name = QLabel(image.image_path.name)
        name.setToolTip(str(image.image_path))
        name.setWordWrap(False)
        name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        name.setStyleSheet(f"color: {PALETTE.text_primary}; background: transparent;")
        self._status = QLabel("")
        self._status.setStyleSheet(
            f"color: {PALETTE.text_muted}; font-size: {TYPOGRAPHY.size_caption}px; background: transparent;"
        )
        meta.addWidget(name)
        meta.addWidget(self._status)

        remove_btn = IconButton(icon_close(), "Remover foto")
        remove_btn.setFixedSize(22, 22)
        remove_btn.setIconSize(QSize(12, 12))
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.image))
        layout.addWidget(self._thumb)
        layout.addLayout(meta, stretch=1)
        layout.addWidget(remove_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
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
        self._status.setText("Selecionada — editar legenda abaixo" if selected else "Clique para selecionar")
        self._status.setStyleSheet(
            f"color: {PALETTE.senai_blue_light if selected else PALETTE.text_muted}; "
            f"font-size: {TYPOGRAPHY.size_caption}px; background: transparent;"
        )

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(super().sizeHint().width(), self._ROW_HEIGHT)


class ImageManagerPanel(QFrame):
    """Gerenciador de imagens por drag-and-drop (sidebar / aba Fotografias)."""

    image_dropped = pyqtSignal(Path)
    image_selected = pyqtSignal(object)
    image_remove_requested = pyqtSignal(object)
    image_caption_changed = pyqtSignal(object, str)
    choose_file_requested = pyqtSignal()

    def __init__(self, parent=None, *, show_header: bool = True) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._drop_active = False
        self._selected_image: ReportImage | None = None
        self._loading_caption = False
        self._row_widgets: list[_ImageListRow] = []
        self._caption_debounce = QTimer(self)
        self._caption_debounce.setSingleShot(True)
        self._caption_debounce.setInterval(450)
        self._caption_debounce.timeout.connect(self._flush_caption)

        self._list = QListWidget()
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._list.setSpacing(6)
        self._list.setFrameShape(QFrame.Shape.NoFrame)
        self._list.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self._list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._list.itemClicked.connect(self._on_item_clicked)
        self._list.currentItemChanged.connect(self._on_current_changed)

        self._drop_hint = QLabel("Solte imagens PNG ou JPG aqui")
        self._drop_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._drop_hint.setWordWrap(True)
        self._drop_hint.setMinimumHeight(48)

        self._choose_btn = SecondaryButton("+ Escolher arquivo…")
        self._choose_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._choose_btn.clicked.connect(self.choose_file_requested.emit)

        self._hint = QLabel("Fotos desta seção")
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
        selection_layout.addWidget(self._list)
        self._caption_label = QLabel("Legenda")
        self._caption_label.setObjectName("GlobalFieldLabel")
        self._caption_edit = PlaceholderTextEdit(multiline=False)
        self._caption_edit.set_text("")
        self._caption_edit.setEnabled(False)
        self._caption_edit.text_changed.connect(self._on_caption_changed)
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
        inner_layout.addWidget(self._drop_hint)
        inner_layout.addWidget(self._choose_btn)
        inner_layout.addWidget(self._selection_block)
        inner_layout.addStretch(1)
        layout.addWidget(inner, stretch=1)

        self.refresh_appearance()

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
        self._apply_drop_hint_style()

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
        return self._caption_edit.has_editor_focus()

    def render_images(self, images: list[ReportImage]) -> None:
        selected_path = (
            str(self._selected_image.image_path) if self._selected_image is not None else None
        )
        editing_caption = self.is_caption_editing()
        live_caption = self._caption_edit.get_text() if editing_caption else None

        self._list.clear()
        self._row_widgets.clear()
        has_images = len(images) > 0
        self._drop_hint.setVisible(True)
        self._list.setVisible(has_images)
        self._empty_list_hint.setVisible(not has_images)
        self._hint.setVisible(True)
        self._caption_label.setVisible(has_images)
        self._caption_edit.setVisible(has_images)
        restore_row = 0
        for index, image in enumerate(images):
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, image)
            row = _ImageListRow(image)
            row.remove_requested.connect(self.image_remove_requested.emit)
            self._row_widgets.append(row)
            self._list.addItem(item)
            self._list.setItemWidget(item, row)
            item.setSizeHint(QSize(max(80, self._list.viewport().width()), _ImageListRow._ROW_HEIGHT))
            if selected_path and str(image.image_path) == selected_path:
                restore_row = index
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

    def _sync_list_height(self) -> None:
        count = self._list.count()
        if count == 0:
            self._list.setFixedHeight(0)
            return
        spacing = self._list.spacing()
        content_h = count * _ImageListRow._ROW_HEIGHT + max(0, count - 1) * spacing + 4
        max_h = 180
        self._list.setFixedHeight(min(content_h, max_h))
        if content_h > max_h:
            self._list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            self._list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        image = item.data(Qt.ItemDataRole.UserRole)
        self._select_image(image, emit=True)

    def _on_current_changed(self, current: QListWidgetItem | None, _previous) -> None:
        if current is None:
            return
        image = current.data(Qt.ItemDataRole.UserRole)
        self._select_image(image, emit=True)

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
        self._caption_edit.setEnabled(image is not None)
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
