"""O sumário não deve voltar ao topo ao re-renderizar as seções."""
from __future__ import annotations

from PyQt6.QtWidgets import QApplication

from src.ui.shared.report_editor.sections_list_panel import SectionsListPanel


def _sections(*, enabled_at: int | None = None) -> list[dict]:
    rows: list[dict] = []
    for index in range(18):
        rows.append(
            {
                "id": f"secao_{index}",
                "title": f"Seção {index:02d} com título longo",
                "display_title": f"Seção {index:02d} com título longo",
                "enabled": index != enabled_at,
            }
        )
    return rows


def _shown_panel(mode: str) -> tuple[QApplication, SectionsListPanel]:
    app = QApplication.instance() or QApplication([])
    panel = SectionsListPanel(mode=mode)
    panel.resize(320, 360)
    panel.show()
    panel.render_sections(_sections())
    panel._list.setFixedHeight(160)
    for _ in range(6):
        app.processEvents()
    return app, panel


def _assert_rebuild_keeps_scroll(panel: SectionsListPanel, app: QApplication, enabled_at: int) -> None:
    bar = panel._list.verticalScrollBar()
    target = bar.maximum()
    assert target > 0
    bar.setValue(target)
    before = bar.value()
    assert before > 0

    panel.render_sections(_sections(enabled_at=enabled_at))
    for _ in range(6):
        app.processEvents()

    after = panel._list.verticalScrollBar().value()
    assert after == before
    panel.close()


def test_template_render_sections_keeps_vertical_scroll() -> None:
    app, panel = _shown_panel("template")
    _assert_rebuild_keeps_scroll(panel, app, enabled_at=10)


def test_workspace_render_sections_keeps_vertical_scroll() -> None:
    app, panel = _shown_panel("workspace")
    _assert_rebuild_keeps_scroll(panel, app, enabled_at=8)


def test_double_click_requests_edit_instead_of_navigate() -> None:
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest

    app, panel = _shown_panel("workspace")
    navigated: list[str] = []
    edited: list[str] = []
    panel.section_navigated.connect(navigated.append)
    panel.section_edit_requested.connect(edited.append)

    row = panel._list.itemWidget(panel._list.item(2))
    assert row is not None
    QTest.mouseDClick(row, Qt.MouseButton.LeftButton)
    QTest.qWait(350)
    app.processEvents()

    assert "secao_2" in edited
    assert navigated == []
    panel.close()

