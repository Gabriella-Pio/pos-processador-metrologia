"""Seletor de imagens capturadas do PDF Bosello."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.ui.components.app_dialog import AppDialog
from src.ui.components.buttons import PrimaryButton, SecondaryButton
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, caption_style, heading_style


class _CaptureTile(QFrame):
    toggled = pyqtSignal(Path, bool)

    def __init__(self, path: Path, *, in_section: bool, parent=None) -> None:
        super().__init__(parent)
        self.path = path
        self._in_section = in_section
        self._selected = False
        self.setObjectName("BoselloCaptureTile")
        self.setCursor(Qt.CursorShape.PointingHandCursor if not in_section else Qt.CursorShape.ArrowCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        thumb = QLabel()
        thumb.setFixedSize(120, 80)
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumb.setStyleSheet(
            f"background: {PALETTE.bg_surface_alt}; border-radius: 4px; "
            f"border: 1px solid {PALETTE.border_subtle};"
        )
        pixmap = QPixmap(str(path))
        if not pixmap.isNull():
            thumb.setPixmap(
                pixmap.scaled(
                    120,
                    80,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        layout.addWidget(thumb, alignment=Qt.AlignmentFlag.AlignHCenter)

        name = QLabel(path.name)
        name.setWordWrap(True)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet(
            f"color: {PALETTE.text_secondary}; font-size: {TYPOGRAPHY.size_caption}px;"
        )
        layout.addWidget(name)

        self._status = QLabel()
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status)
        self._apply_style()

    def mousePressEvent(self, event) -> None:
        if self._in_section:
            super().mousePressEvent(event)
            return
        self._selected = not self._selected
        self._apply_style()
        self.toggled.emit(self.path, self._selected)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool) -> None:
        if self._in_section:
            return
        self._selected = selected
        self._apply_style()

    def is_selected(self) -> bool:
        return self._selected and not self._in_section

    def _apply_style(self) -> None:
        if self._in_section:
            self._status.setText("Já nesta seção")
            self._status.setStyleSheet(
                f"color: {PALETTE.text_muted}; font-size: {TYPOGRAPHY.size_micro}px;"
            )
            border = PALETTE.border_subtle
            bg = PALETTE.bg_surface
        elif self._selected:
            self._status.setText("Selecionada")
            self._status.setStyleSheet(
                f"color: {PALETTE.senai_blue_light}; font-size: {TYPOGRAPHY.size_micro}px;"
            )
            border = PALETTE.senai_blue_light
            bg = "rgba(74, 111, 212, 0.14)"
        else:
            self._status.setText("Clique para selecionar")
            self._status.setStyleSheet(caption_style())
            border = PALETTE.border_subtle
            bg = PALETTE.bg_surface
        self.setStyleSheet(
            f"QFrame#BoselloCaptureTile {{ background: {bg}; border: 1px solid {border}; border-radius: 8px; }}"
        )


class BoselloCapturePickerDialog(AppDialog):
    """Escolhe capturas Bosello para adicionar à seção em edição."""

    def __init__(
        self,
        captures: list[Path],
        *,
        section_id: str,
        paths_in_section: set[str],
        parent=None,
    ) -> None:
        super().__init__(
            parent,
            window_title="Capturas do relatório Bosello",
            minimum_width=520,
        )
        self.setMinimumHeight(420)

        self._tiles: list[_CaptureTile] = []
        self._selected: set[str] = set()

        layout = self.create_root_layout()
        self.add_dialog_header(
            layout,
            "Adicionar capturas à seção",
            "Estas imagens foram extraídas do PDF da máquina. "
            "Remover uma foto da seção não apaga a captura — você pode adicioná-la de novo aqui.",
        )

        grid_host = QWidget()
        self._grid = QGridLayout(grid_host)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(SPACING.sm)
        self._grid.setVerticalSpacing(SPACING.sm)

        for index, path in enumerate(captures):
            tile = _CaptureTile(
                path,
                in_section=str(path) in paths_in_section,
            )
            tile.toggled.connect(self._on_tile_toggled)
            self._tiles.append(tile)
            row, col = divmod(index, 3)
            self._grid.addWidget(tile, row, col)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(grid_host)

        self._summary = QLabel()
        self._summary.setStyleSheet(caption_style())
        self._update_summary()

        cancel = SecondaryButton("Cancelar")
        cancel.clicked.connect(self.reject)
        confirm = PrimaryButton("Adicionar selecionadas")
        confirm.clicked.connect(self.accept)
        footer = QHBoxLayout()
        footer.addStretch(1)
        footer.addWidget(cancel)
        footer.addWidget(confirm)

        layout.addWidget(scroll, stretch=1)
        layout.addWidget(self._summary)
        self.add_dialog_divider(layout)
        layout.addLayout(footer)

        _ = section_id

    def _on_tile_toggled(self, path: Path, selected: bool) -> None:
        key = str(path)
        if selected:
            self._selected.add(key)
        else:
            self._selected.discard(key)
        self._update_summary()

    def _update_summary(self) -> None:
        count = len(self._selected)
        self._summary.setText(
            f"{count} captura(s) selecionada(s) para adicionar."
            if count
            else "Selecione uma ou mais capturas acima."
        )

    def selected_paths(self) -> list[Path]:
        return [Path(key) for key in sorted(self._selected)]
