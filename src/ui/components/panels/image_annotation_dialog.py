"""Modal para edição de crop, zoom e marcações em uma fotografia."""
from __future__ import annotations

from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
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

from src.core.domain.ports import ReportImage
from src.ui.components.app_dialog import AppDialog, present_app_dialog
from src.ui.components.buttons import PrimaryButton, SecondaryButton
from src.ui.components.panels.annotation_toolbar import AnnotationToolbar
from src.ui.components.panels.image_annotation_canvas import ImageAnnotationCanvas
from src.ui.components.panels.marker_legend_panel import MarkerLegendPanel
from src.ui.components.panels.photo_pdf_preview import PhotoPdfPreviewPanel
from src.ui.components.placeholder_field import PlaceholderTextEdit
from src.ui.styles import SPACING, available_size, caption_style, fit_dialog
from src.ui.styles.screen_metrics import SCREEN_MARGIN

#: Altura somada de cabeçalho, legenda, barra de ferramentas, rodapé e margens.
_DIALOG_CHROME_HEIGHT = 531


def _canvas_min_height(dialog: QWidget) -> int:
    """Sobra para a foto depois do chrome — evita diálogo maior que a tela."""
    _, screen_h = available_size(dialog)
    return max(160, min(360, screen_h - SCREEN_MARGIN - _DIALOG_CHROME_HEIGHT))


class ImageAnnotationDialog(AppDialog):
    edits_changed = pyqtSignal(object)
    caption_changed = pyqtSignal(object, str)
    photo_navigated = pyqtSignal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent, window_title="Editar fotografia", minimum_width=960)
        fit_dialog(self, 1060, 940)
        self.setModal(True)
        self._image: ReportImage | None = None
        self._gallery: list[ReportImage] = []
        self._gallery_index = 0
        self._loading_caption = False
        self._caption_debounce = QTimer(self)
        self._caption_debounce.setSingleShot(True)
        self._caption_debounce.setInterval(450)
        self._caption_debounce.timeout.connect(self._flush_caption)

        self._photo_label = QLabel()
        self._photo_label.setObjectName("SidebarHint")
        self._photo_label.setStyleSheet(caption_style())

        self._caption_label = QLabel("Legenda da foto (no PDF)")
        self._caption_label.setObjectName("GlobalFieldLabel")
        self._caption_edit = PlaceholderTextEdit(multiline=False)
        self._caption_edit.text_changed.connect(self._on_caption_changed)

        self._canvas = ImageAnnotationCanvas()
        self._canvas.setMinimumHeight(_canvas_min_height(self))
        self._canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._canvas.edits_changed.connect(self._on_canvas_edits_changed)

        self._toolbar = AnnotationToolbar()
        self._toolbar.tool_selected.connect(self._on_tool_selected)
        self._toolbar.zoom_in_requested.connect(self._canvas.zoom_in)
        self._toolbar.zoom_out_requested.connect(self._canvas.zoom_out)
        self._toolbar.zoom_reset_requested.connect(self._canvas.reset_zoom)
        self._toolbar.undo_requested.connect(self._canvas.undo_last)
        self._toolbar.clear_crop_requested.connect(self._canvas.clear_crop)
        self._toolbar.copy_requested.connect(self._on_copy_annotations)
        self._toolbar.paste_requested.connect(self._canvas.paste_annotations)
        self._toolbar.delete_selected_requested.connect(self._canvas.delete_selected)
        self._toolbar.select_mode_requested.connect(lambda: self._canvas.set_tool(None))
        self._canvas.zoom_changed.connect(self._toolbar.set_zoom_percent)

        self._legend_panel = MarkerLegendPanel()
        self._legend_panel.legend_changed.connect(self._on_legend_changed)
        self._pdf_preview = PhotoPdfPreviewPanel()

        legend_scroll = QScrollArea()
        legend_scroll.setObjectName("MarkerLegendScroll")
        legend_scroll.setWidgetResizable(True)
        legend_scroll.setFrameShape(QFrame.Shape.NoFrame)
        legend_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        legend_scroll.setMaximumHeight(112 if available_size(self)[1] >= 900 else 88)
        legend_scroll.setWidget(self._legend_panel)

        bottom_row = QFrame()
        bottom_row.setObjectName("ImageAnnotationBottomRow")
        bottom_row.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        bottom_layout = QHBoxLayout(bottom_row)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(SPACING.sm)
        bottom_layout.addWidget(legend_scroll, stretch=1)
        bottom_layout.addWidget(self._pdf_preview, stretch=0)

        editor_host = QWidget()
        editor_host.setObjectName("ImageAnnotationEditorHost")
        editor_host.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        editor_layout = QVBoxLayout(editor_host)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(SPACING.sm)
        editor_layout.addWidget(self._toolbar)
        editor_layout.addWidget(self._canvas, stretch=1)
        editor_layout.addWidget(bottom_row)

        self._prev_btn = SecondaryButton("← Anterior")
        self._prev_btn.clicked.connect(self._show_previous)
        self._next_btn = SecondaryButton("Próxima →")
        self._next_btn.clicked.connect(self._show_next)
        self._position_label = QLabel()
        self._position_label.setObjectName("SidebarHint")

        layout = self.create_root_layout()
        self.add_dialog_header(
            layout,
            "Editar fotografia",
            "Atalhos: Selecionar · S/C/T/N ferramentas · ← → trocar foto · Del apagar · "
            "Ctrl+C/V copiar/colar · Ctrl+Z desfazer",
        )
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(SPACING.md)
        body_layout.addWidget(self._photo_label)
        body_layout.addWidget(self._caption_label)
        body_layout.addWidget(self._caption_edit)
        body_layout.addWidget(editor_host, stretch=1)

        # Em telas curtas (escala alta do Windows) o corpo rola; cabeçalho e
        # botões continuam visíveis em vez de sair para fora da tela.
        body_scroll = QScrollArea()
        body_scroll.setObjectName("ImageAnnotationBodyScroll")
        body_scroll.setWidgetResizable(True)
        body_scroll.setFrameShape(QFrame.Shape.NoFrame)
        body_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body_scroll.setWidget(body)
        layout.addWidget(body_scroll, stretch=1)

        self.add_dialog_divider(layout)
        footer = QHBoxLayout()
        footer.addWidget(self._prev_btn)
        footer.addWidget(self._next_btn)
        footer.addWidget(self._position_label)
        footer.addStretch(1)
        done_btn = PrimaryButton("Concluído")
        done_btn.clicked.connect(self.accept)
        footer.addWidget(done_btn)
        layout.addLayout(footer)

        self.refresh_appearance()

    def refresh_appearance(self) -> None:
        self._photo_label.setStyleSheet(caption_style())
        self._position_label.setStyleSheet(caption_style())
        self._prev_btn.refresh_appearance()
        self._next_btn.refresh_appearance()
        self._toolbar.refresh_appearance()
        self._legend_panel.refresh_appearance()
        self._canvas.update()

    def is_caption_editing(self) -> bool:
        return self._caption_edit.has_editor_focus()

    def open_for(self, image: ReportImage | None, *, gallery: list[ReportImage] | None = None) -> None:
        if image is None and not gallery:
            return
        self._gallery = list(gallery or ([image] if image is not None else []))
        if not self._gallery:
            return
        start = image if image is not None else self._gallery[0]
        self._gallery_index = self._index_of(start)
        self._show_current()
        present_app_dialog(self.parentWidget(), self)

    def _index_of(self, image: ReportImage) -> int:
        target = str(image.image_path)
        for index, item in enumerate(self._gallery):
            if str(item.image_path) == target:
                return index
        return 0

    def _show_current(self) -> None:
        if not self._gallery:
            return
        self._flush_caption()
        self._image = self._gallery[self._gallery_index]
        self._photo_label.setText(self._image.image_path.name)
        self._loading_caption = True
        self._caption_edit.set_text(self._image.caption or "", force=True)
        self._loading_caption = False
        self._canvas.set_image(self._image)
        self._legend_panel.set_image(self._image)
        self._pdf_preview.set_image(self._image)
        self._toolbar.set_tools_enabled(True)
        self._toolbar.set_zoom_percent(self._canvas.current_zoom())
        self._update_nav_controls()
        self.photo_navigated.emit(self._image)
        self._canvas.setFocus()

    def _update_nav_controls(self) -> None:
        total = len(self._gallery)
        has_many = total > 1
        self._prev_btn.setVisible(has_many)
        self._next_btn.setVisible(has_many)
        self._position_label.setVisible(has_many)
        if has_many:
            self._position_label.setText(f"Foto {self._gallery_index + 1} de {total}")
            self._prev_btn.setEnabled(self._gallery_index > 0)
            self._next_btn.setEnabled(self._gallery_index < total - 1)

    def _show_previous(self) -> None:
        if self._gallery_index > 0:
            self._gallery_index -= 1
            self._show_current()

    def _show_next(self) -> None:
        if self._gallery_index < len(self._gallery) - 1:
            self._gallery_index += 1
            self._show_current()

    def _can_navigate_gallery(self) -> bool:
        if self.is_caption_editing():
            return False
        focus = self.focusWidget()
        if isinstance(focus, QLineEdit):
            return False
        return len(self._gallery) > 1

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        if self._can_navigate_gallery() and not event.modifiers():
            if event.key() == Qt.Key.Key_Left:
                self._show_previous()
                event.accept()
                return
            if event.key() == Qt.Key.Key_Right:
                self._show_next()
                event.accept()
                return
        super().keyPressEvent(event)

    def _on_caption_changed(self, _text: str) -> None:
        if self._loading_caption or self._image is None:
            return
        self._caption_debounce.start()

    def _flush_caption(self) -> None:
        if self._image is None:
            return
        if self._caption_debounce.isActive():
            self._caption_debounce.stop()
        caption = self._caption_edit.get_text().strip()
        if caption != (self._image.caption or ""):
            self._image.caption = caption
            self.caption_changed.emit(self._image, caption)
            self._pdf_preview.schedule_refresh()

    def _on_tool_selected(self, tool_id: str) -> None:
        self._canvas.set_tool(tool_id)

    def _on_copy_annotations(self) -> None:
        self._canvas.copy_annotations()
        self._toolbar.refresh_appearance()

    def _on_canvas_edits_changed(self, image: ReportImage) -> None:
        self._legend_panel.set_image(image)
        self._pdf_preview.schedule_refresh()
        self._toolbar.refresh_appearance()
        self.edits_changed.emit(image)

    def _on_legend_changed(self, image: ReportImage) -> None:
        self._pdf_preview.schedule_refresh()
        self.edits_changed.emit(image)
