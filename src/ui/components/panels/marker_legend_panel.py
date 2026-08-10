"""Painel editável de legendas dos marcadores numerados."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QSizePolicy, QVBoxLayout, QWidget

from src.core.domain.ports import Annotation, ReportImage
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, caption_style


class MarkerLegendPanel(QFrame):
    legend_changed = pyqtSignal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("MarkerLegendPanel")
        self.setAutoFillBackground(True)
        self._image: ReportImage | None = None
        self._rows: list[tuple[Annotation, QLineEdit]] = []

        self._title = QLabel("Legenda dos marcadores")
        self._title.setObjectName("GlobalFieldLabel")
        self._hint = QLabel("Aparece abaixo da foto no PDF.")
        self._hint.setObjectName("SidebarHint")
        self._empty = QLabel("Nenhum marcador numerado nesta foto.")
        self._empty.setObjectName("SidebarHint")

        self._rows_host = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_host)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(SPACING.xs)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.xs, SPACING.sm, SPACING.xs)
        layout.setSpacing(SPACING.xs)
        layout.addWidget(self._title)
        layout.addWidget(self._hint)
        layout.addWidget(self._empty)
        layout.addWidget(self._rows_host)
        self.refresh_appearance()

    def set_image(self, image: ReportImage | None) -> None:
        self._image = image
        self._rebuild_rows()

    def refresh_appearance(self) -> None:
        self.setStyleSheet(
            f"QFrame#MarkerLegendPanel {{ background-color: {PALETTE.bg_surface}; border: none; }}"
        )
        self._hint.setStyleSheet(caption_style())
        self._empty.setStyleSheet(caption_style())
        self._title.setStyleSheet(
            f"color: {PALETTE.text_primary}; font-size: {TYPOGRAPHY.size_body}px; "
            f"font-weight: {TYPOGRAPHY.weight_semibold}; background: transparent;"
        )

    def _clear_rows(self) -> None:
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._rows = []

    def _rebuild_rows(self) -> None:
        self._clear_rows()
        numbers = [
            ann for ann in (self._image.annotations if self._image else []) if ann.kind == "number"
        ]
        numbers.sort(key=lambda ann: int(ann.text) if str(ann.text).isdigit() else ann.text)
        has_numbers = len(numbers) > 0
        self._empty.setVisible(not has_numbers)
        self._rows_host.setVisible(has_numbers)
        if not has_numbers:
            return
        for annotation in numbers:
            row = QHBoxLayout()
            row.setSpacing(SPACING.sm)
            badge = QLabel(str(annotation.text))
            badge.setFixedWidth(24)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(
                f"background: {PALETTE.senai_orange}; color: white; border-radius: 12px; "
                f"font-weight: {TYPOGRAPHY.weight_semibold};"
            )
            field = QLineEdit(annotation.legend)
            field.setPlaceholderText("Descrição do defeito / ponto de interesse")
            field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            field.textChanged.connect(
                lambda text, ann=annotation: self._on_legend_edited(ann, text)
            )
            row_widget = QFrame()
            row_widget.setLayout(row)
            row.addWidget(badge)
            row.addWidget(field, stretch=1)
            self._rows_layout.addWidget(row_widget)
            self._rows.append((annotation, field))

    def _on_legend_edited(self, annotation: Annotation, text: str) -> None:
        annotation.legend = text.strip()
        if self._image is not None:
            self.legend_changed.emit(self._image)
