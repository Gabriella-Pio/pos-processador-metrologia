"""Overlay semitransparente dentro da janela — clique fora fecha o diálogo."""
from __future__ import annotations

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtWidgets import QDialog, QWidget


class ModalOverlay(QWidget):
    """Cobre a janela host; cliques no overlay rejeitam o diálogo associado."""

    OBJECT_NAME = "ModalOverlay"

    def __init__(self, host: QWidget, dialog: QDialog) -> None:
        super().__init__(host)
        self._host = host
        self._dialog = dialog
        self.setObjectName(self.OBJECT_NAME)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0.45);")
        self._sync_geometry()
        host.installEventFilter(self)

    def _sync_geometry(self) -> None:
        self.setGeometry(self._host.rect())

    def eventFilter(self, obj, event) -> bool:  # noqa: ANN001
        if obj is self._host and event.type() in (
            QEvent.Type.Resize,
            QEvent.Type.Move,
        ):
            self._sync_geometry()
        return False

    def mousePressEvent(self, event) -> None:  # noqa: ANN001, N802
        self._dialog.reject()
        event.accept()
