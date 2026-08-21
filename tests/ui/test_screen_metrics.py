"""Layout resiliente à escala de exibição do Windows (100%, 125%, 150%…)."""
from __future__ import annotations

import pytest

from src.ui.shared.report_editor.editor_shell import (
    EDITING_RATIOS,
    PREVIEW_ONLY_RATIOS,
    splitter_sizes,
)
from src.ui.shared.report_editor.preview_constants import PREVIEW_ZOOM


# Área lógica típica de um monitor 1920x1080 em cada escala do Windows.
LOGICAL_WIDTHS = [1920, 1536, 1280, 1097, 960]


@pytest.mark.parametrize("width", LOGICAL_WIDTHS)
@pytest.mark.parametrize("ratios", [EDITING_RATIOS, PREVIEW_ONLY_RATIOS])
def test_splitter_never_exceeds_available_width(width: int, ratios) -> None:
    sizes = splitter_sizes(width, ratios)
    assert sum(sizes) <= width


@pytest.mark.parametrize("width", LOGICAL_WIDTHS)
def test_splitter_keeps_preview_and_sidebar_usable(width: int) -> None:
    sidebar, _editor, preview = splitter_sizes(width, EDITING_RATIOS)
    assert sidebar >= 200
    assert preview >= 320


def test_splitter_falls_back_when_width_unknown() -> None:
    sizes = splitter_sizes(0, EDITING_RATIOS)
    assert all(size > 0 for size in sizes)


def test_fit_to_screen_clamps_to_available_area(monkeypatch) -> None:
    from src.ui.styles import screen_metrics

    monkeypatch.setattr(screen_metrics, "available_size", lambda reference=None: (1280, 720))
    assert screen_metrics.fit_to_screen(1060, 940, margin=48) == (1060, 672)
    assert screen_metrics.fit_to_screen(800, 400, margin=48) == (800, 400)


def test_preview_device_pixel_ratio_is_stepped(monkeypatch) -> None:
    from src.ui.styles import screen_metrics

    class _Screen:
        def __init__(self, ratio: float) -> None:
            self._ratio = ratio

        def devicePixelRatio(self) -> float:  # noqa: N802
            return self._ratio

    for raw, expected in ((1.0, 1.0), (1.26, 1.25), (1.5, 1.5), (4.0, 3.0), (0.5, 1.0)):
        monkeypatch.setattr(screen_metrics, "_screen_for", lambda _r=None, v=raw: _Screen(v))
        assert screen_metrics.preview_device_pixel_ratio() == expected


def test_raster_zoom_follows_screen_density(monkeypatch) -> None:
    from src.ui.shared.report_editor import preview_constants
    from src.ui.styles import screen_metrics

    monkeypatch.setattr(screen_metrics, "preview_device_pixel_ratio", lambda reference=None: 1.5)
    assert preview_constants.raster_zoom() == pytest.approx(PREVIEW_ZOOM * 1.5)


def test_preview_fits_page_width_without_horizontal_scroll() -> None:
    from PyQt6.QtCore import QBuffer, QByteArray, QIODevice
    from PyQt6.QtGui import QColor, QImage
    from PyQt6.QtWidgets import QApplication

    from src.ui.shared.report_editor.preview_panel import PreviewPanel

    app = QApplication.instance() or QApplication([])
    image = QImage(979, 1267, QImage.Format.Format_RGB32)
    image.fill(QColor("white"))
    payload = QByteArray()
    buffer = QBuffer(payload)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert image.save(buffer, "PNG")

    panel = PreviewPanel()
    panel.resize(650, 500)
    panel.show()
    panel.render_pages([bytes(payload)])
    for _ in range(3):
        app.processEvents()

    page = panel._page_items[0]
    page_width, _page_height = page["logical_size"]
    assert page_width <= panel.scroll_area().viewport().width()
    assert panel.scroll_area().horizontalScrollBar().maximum() == 0
    assert page["display_zoom"] <= PREVIEW_ZOOM
    panel.close()


def test_prompt_text_uses_themed_dialog() -> None:
    from PyQt6.QtCore import QTimer
    from PyQt6.QtWidgets import QApplication, QDialog, QLineEdit, QWidget

    from src.ui.components.app_dialog import present_app_dialog
    from src.ui.components.feedback import _TextPromptDialog

    app = QApplication.instance() or QApplication([])
    parent = QWidget()
    parent.show()
    dialog = _TextPromptDialog(parent, "Marcador numerado", "Descrição do marcador 1:")

    def fill_and_accept() -> None:
        line = dialog.findChild(QLineEdit)
        assert line is not None
        line.setText("fissura")
        dialog.accept()

    QTimer.singleShot(0, fill_and_accept)
    assert present_app_dialog(parent, dialog) == QDialog.DialogCode.Accepted
    assert dialog.value == "fissura"
    parent.close()
