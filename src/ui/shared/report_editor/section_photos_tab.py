"""Aba Fotografias do editor de seção."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.core.domain.ports import ReportImage
from src.ui.components.buttons import SecondaryButton
from src.ui.components.panels import ImageManagerPanel
from src.ui.components.panels.image_annotation_dialog import ImageAnnotationDialog
from src.ui.styles import SPACING, caption_style


class SectionPhotosTab(QWidget):
    image_dropped = pyqtSignal(Path)
    image_remove_requested = pyqtSignal(object)
    image_caption_changed = pyqtSignal(object, str)
    image_selected = pyqtSignal(object)
    image_edits_changed = pyqtSignal(object)
    bosello_picker_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._active_image: ReportImage | None = None
        self._section_images: list[ReportImage] = []
        self._section_id: str | None = None

        self._image_panel = ImageManagerPanel(
            show_header=False, show_caption=False, expand_list=True
        )
        self._image_panel.image_dropped.connect(self.image_dropped.emit)
        self._image_panel.image_remove_requested.connect(self.image_remove_requested.emit)
        self._image_panel.image_caption_changed.connect(self.image_caption_changed.emit)
        self._image_panel.image_selected.connect(self._on_image_selected)
        self._image_panel.image_edit_requested.connect(self._open_annotation_editor)
        self._image_panel.choose_file_requested.connect(self._on_insert_photo)
        self._image_panel.bosello_picker_requested.connect(self.bosello_picker_requested.emit)

        self._annotation_dialog = ImageAnnotationDialog(self)
        self._annotation_dialog.edits_changed.connect(self.image_edits_changed.emit)
        self._annotation_dialog.caption_changed.connect(self.image_caption_changed.emit)
        self._annotation_dialog.photo_navigated.connect(self._on_dialog_photo_navigated)

        self._edit_photo_btn = SecondaryButton("Editar legenda, marcações e crop…")
        self._edit_photo_btn.setEnabled(False)
        self._edit_photo_btn.clicked.connect(lambda: self._open_annotation_editor())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        layout.setSpacing(SPACING.sm)
        self._photos_hint = QLabel(
            "Fotos desta seção. Duplo clique na lista ou use o botão abaixo para editar. "
            "No editor: ← → troca de foto."
        )
        self._photos_hint.setWordWrap(True)
        self._photos_hint.setObjectName("SidebarHint")
        self._photos_hint.setStyleSheet(caption_style())
        layout.addWidget(self._photos_hint)
        layout.addWidget(self._image_panel, stretch=1)
        layout.addWidget(self._edit_photo_btn, stretch=0)

    def set_section_id(self, section_id: str | None) -> None:
        self._section_id = section_id

    def update_hint(self, section: dict | None = None) -> None:
        title = ""
        if section:
            title = section.get("display_title") or section.get("title") or ""
        if title:
            self._photos_hint.setText(
                f"Fotos desta seção ({title}). Duplo clique na lista ou use o botão abaixo. "
                "No editor: ← → troca de foto."
            )
        else:
            self._photos_hint.setText(
                "Fotos desta seção. Duplo clique na lista ou use o botão abaixo para editar. "
                "No editor: ← → troca de foto."
            )

    def render_images(self, images: list[ReportImage]) -> None:
        section_id = self._section_id
        if section_id is None:
            self._image_panel.render_images([])
            self._image_panel.set_bosello_captures_available(False)
            self._section_images = []
            return
        filtered = [img for img in images if img.section_id == section_id]
        self._section_images = filtered
        self._image_panel.render_images(filtered)

    def clear_images(self) -> None:
        self._image_panel.render_images([])

    def set_bosello_captures_available(self, available: bool) -> None:
        self._image_panel.set_bosello_captures_available(available)

    def is_caption_editing(self) -> bool:
        return (
            self._image_panel.is_caption_editing()
            or self._annotation_dialog.is_caption_editing()
        )

    def schedule_list_layout_sync(self) -> None:
        self._image_panel.schedule_list_layout_sync()

    def refresh_appearance(self) -> None:
        self._image_panel.refresh_appearance()
        self._edit_photo_btn.refresh_appearance()
        self._annotation_dialog.refresh_appearance()

    def _on_insert_photo(self) -> None:
        from PyQt6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Inserir fotografia",
            "",
            "Imagens (*.png *.jpg *.jpeg)",
        )
        if path:
            self.image_dropped.emit(Path(path))

    def _on_image_selected(self, image: ReportImage | None) -> None:
        self._active_image = image
        self._edit_photo_btn.setEnabled(image is not None)
        self.image_selected.emit(image)

    def _open_annotation_editor(self, image: ReportImage | None = None) -> None:
        target = image if image is not None else self._image_panel.selected_image()
        if target is None:
            return
        self._annotation_dialog.open_for(target, gallery=self._section_images)

    def _on_dialog_photo_navigated(self, image: ReportImage) -> None:
        self._image_panel.select_image_by_path(str(image.image_path))
