"""Modais não devem recriar HWND nativo (janela fantasma no Windows)."""
from __future__ import annotations

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QApplication, QWidget

from src.ui.components.app_dialog import AppDialog
from src.ui.components.modal_presentation import present_modal_dialog


class _GuardedDialog(AppDialog):
    def __init__(self, parent=None) -> None:
        self.window_type_changes: list[tuple[object, bool]] = []
        super().__init__(parent, window_title="Teste")

    def setWindowFlag(self, flag, on: bool = True) -> None:  # noqa: N802
        self.window_type_changes.append((flag, on))
        super().setWindowFlag(flag, on)


def test_modal_presentation_does_not_recreate_native_window() -> None:
    app = QApplication.instance() or QApplication([])
    host = QWidget()
    host.resize(640, 480)
    host.show()
    dialog = _GuardedDialog(host)
    QTimer.singleShot(0, dialog.reject)
    present_modal_dialog(host, dialog)
    toggles = [flag for flag, _on in dialog.window_type_changes if flag == Qt.WindowType.Window]
    assert toggles == []
    host.close()
    app.processEvents()
