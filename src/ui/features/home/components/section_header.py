"""Cabeçalho de seção dos painéis da Home."""
from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.ui.styles import SPACING


class TabSectionHeader(QWidget):
    def __init__(
        self,
        title: str,
        subtitle: str = "",
        right: QWidget | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, SPACING.xl, 0, 0)
        column = QVBoxLayout()
        column.setSpacing(3)

        title_label = QLabel(title)
        title_label.setObjectName("SectionHeaderTitle")
        self._title_label = title_label
        column.addWidget(title_label)

        self._subtitle_label = QLabel(subtitle)
        self._subtitle_label.setObjectName("SectionHeaderSubtitle")
        column.addWidget(self._subtitle_label)

        row.addLayout(column)
        row.addStretch(1)
        if right is not None:
            row.addWidget(right)

    def set_title(self, text: str) -> None:
        if self._title_label is not None:
            self._title_label.setText(text)

    def set_subtitle(self, text: str) -> None:
        if self._subtitle_label is not None:
            self._subtitle_label.setText(text)

    def refresh_appearance(self) -> None:
        style = self.style()
        for label in (self._title_label, self._subtitle_label):
            style.unpolish(label)
            style.polish(label)
            label.update()
