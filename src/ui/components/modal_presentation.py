"""Apresentação de diálogos com overlay — clique fora e Esc fecham."""
from __future__ import annotations

from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtWidgets import QApplication, QDialog, QMainWindow, QWidget

from src.ui.components.modal_overlay import ModalOverlay


def modal_host(parent: QWidget) -> QWidget:
    """Widget que o overlay deve cobrir (área central da janela principal)."""
    window = parent.window()
    if isinstance(window, QMainWindow):
        return window.centralWidget() or window
    return window


def _center_dialog_on_window(parent: QWidget, dialog: QDialog) -> None:
    window = parent.window()
    dialog.adjustSize()
    host_geo = window.frameGeometry()
    dialog_geo = dialog.frameGeometry()
    dialog_geo.moveCenter(host_geo.center())
    dialog.move(dialog_geo.topLeft())


class _DialogEscapeFilter(QObject):
    """Garante Esc no modal mesmo com atalhos globais da janela principal."""

    def __init__(self, dialog: QDialog) -> None:
        super().__init__(dialog)
        self._dialog = dialog

    def eventFilter(self, obj, event) -> bool:  # noqa: ANN001
        if (
            event.type() == QEvent.Type.KeyPress
            and event.key() == Qt.Key.Key_Escape
            and self._dialog.isVisible()
        ):
            self._dialog.reject()
            return True
        return False


def present_modal_dialog(parent: QWidget, dialog: QDialog) -> int:
    """Exibe diálogo com overlay; retorna ``QDialog.DialogCode``."""
    host = modal_host(parent)
    overlay = ModalOverlay(host, dialog)
    if hasattr(dialog, "set_overlay"):
        dialog.set_overlay(overlay)

    app = QApplication.instance()
    escape_filter: _DialogEscapeFilter | None = None
    if app is not None:
        escape_filter = _DialogEscapeFilter(dialog)
        app.installEventFilter(escape_filter)

    overlay.show()
    overlay.raise_()
    dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
    if hasattr(dialog, "prepare_for_show"):
        dialog.prepare_for_show()
    _center_dialog_on_window(parent, dialog)
    dialog.raise_()
    result = int(dialog.exec())

    if app is not None and escape_filter is not None:
        app.removeEventFilter(escape_filter)

    overlay.hide()
    host.removeEventFilter(overlay)
    overlay.deleteLater()
    if hasattr(dialog, "set_overlay"):
        dialog.set_overlay(None)
    return result
