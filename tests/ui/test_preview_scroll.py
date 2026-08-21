"""O preview não deve pular para o topo ao regenerar páginas."""
from __future__ import annotations

from PyQt6.QtCore import QBuffer, QByteArray, QIODevice
from PyQt6.QtGui import QColor, QImage
from PyQt6.QtWidgets import QApplication

from src.ui.shared.report_editor.preview_panel import PreviewPanel


def _png_page(width: int = 400, height: int = 900) -> bytes:
    image = QImage(width, height, QImage.Format.Format_RGB32)
    image.fill(QColor("white"))
    payload = QByteArray()
    buffer = QBuffer(payload)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert image.save(buffer, "PNG")
    return bytes(payload)


def test_render_pages_keeps_vertical_scroll() -> None:
    app = QApplication.instance() or QApplication([])
    panel = PreviewPanel()
    panel.resize(480, 360)
    panel.show()
    page = _png_page()
    panel.render_pages([page, page, page])
    for _ in range(4):
        app.processEvents()

    bar = panel.scroll_area().verticalScrollBar()
    assert bar.maximum() > 40
    bar.setValue(min(180, bar.maximum()))
    before = bar.value()
    assert before > 0

    panel.render_pages([page, page, page])
    for _ in range(4):
        app.processEvents()

    after = panel.scroll_area().verticalScrollBar().value()
    assert after > 0
    assert abs(after - before) <= 30

    from PyQt6.QtTest import QTest

    QTest.qWait(60)
    delayed = panel.scroll_area().verticalScrollBar().value()
    assert delayed > 0
    assert abs(delayed - before) <= 30
    panel.close()


def test_preview_rebuild_keeps_page_widgets_parented() -> None:
    app = QApplication.instance() or QApplication([])
    panel = PreviewPanel()
    panel.resize(480, 360)
    panel.show()
    page = _png_page()
    panel.render_pages([page, page])
    for _ in range(4):
        app.processEvents()
    panel.render_pages([page, page])
    for _ in range(4):
        app.processEvents()

    assert panel._status_label.parent() is panel
    assert panel._pages_host.parent() is not None
    for item in panel._page_items:
        container = item["container"]
        assert container.parent() is panel._pages_host
        assert item["page_label"].parent() is container
        assert item["image_label"].parent() is container
    panel.close()


def test_update_anchor_map_records_sections_without_prior_seed() -> None:
    app = QApplication.instance() or QApplication([])
    panel = PreviewPanel()
    panel.update_anchor_map(
        {
            "introducao": {"page": 2, "x": 72, "y": 700, "width": 200, "height": 18},
        }
    )
    assert panel.section_id_for_page(2) == "introducao"
    panel.set_anchor_map({"introducao": {"id": "introducao", "title": "Introdução"}})
    assert panel._anchor_map["introducao"]["page_start"] == 2
    assert panel._anchor_map["introducao"]["anchor_rect"]["page"] == 2
    panel.close()
    _ = app


def test_focus_section_scrolls_to_target_after_fit() -> None:
    from PyQt6.QtTest import QTest

    app = QApplication.instance() or QApplication([])
    panel = PreviewPanel()
    panel.resize(480, 360)
    panel.show()
    page = _png_page()
    panel.render_pages([page, page, page])
    for _ in range(4):
        app.processEvents()

    bar = panel.scroll_area().verticalScrollBar()
    assert bar.maximum() > 40
    bar.setValue(bar.maximum())
    assert bar.value() > bar.maximum() // 2

    panel.set_anchor_map(
        {
            "interpretacao": {
                "id": "interpretacao",
                "page_start": 1,
                "anchor_rect": {"page": 1, "x": 72, "y": 700, "width": 200, "height": 18},
            }
        }
    )
    panel.focus_section("interpretacao")
    QTest.qWait(80)
    app.processEvents()

    assert panel.scroll_area().verticalScrollBar().value() < bar.maximum() // 2
    panel.close()


def test_focus_section_does_not_move_when_title_already_visible() -> None:
    from PyQt6.QtTest import QTest

    app = QApplication.instance() or QApplication([])
    panel = PreviewPanel()
    panel.resize(480, 360)
    panel.show()
    page = _png_page()
    panel.render_pages([page, page, page])
    for _ in range(4):
        app.processEvents()

    panel.set_anchor_map(
        {
            "interpretacao": {
                "id": "interpretacao",
                "page_start": 1,
                "anchor_rect": {"page": 1, "x": 72, "y": 700, "width": 200, "height": 18},
            }
        }
    )
    bar = panel.scroll_area().verticalScrollBar()
    before = bar.value()
    panel.focus_section("interpretacao")
    QTest.qWait(80)
    app.processEvents()
    assert bar.value() == before
    panel.close()


def test_pin_keeps_content_when_pages_shrink() -> None:
    from PyQt6.QtTest import QTest

    app = QApplication.instance() or QApplication([])
    panel = PreviewPanel()
    panel.resize(520, 360)
    panel.show()
    page = _png_page(width=480, height=900)
    panel.render_pages([page, page, page])
    for _ in range(4):
        app.processEvents()

    bar = panel.scroll_area().verticalScrollBar()
    assert bar.maximum() > 40
    bar.setValue(min(200, bar.maximum()))
    before = bar.value()
    old_h = sum(item["logical_size"][1] for item in panel._page_items)
    assert before > 0
    assert old_h > 0

    panel.pin_vertical_scroll()
    panel.resize(240, 360)
    QTest.qWait(120)
    app.processEvents()

    new_h = sum(item["logical_size"][1] for item in panel._page_items)
    expected = round(before * new_h / old_h)
    assert new_h < old_h
    assert abs(bar.value() - expected) <= 25
    panel.close()
