"""Restaurar atualiza a aba de edição mesmo com o campo focado."""
from __future__ import annotations

from dataclasses import fields

from PyQt6.QtWidgets import QApplication, QLabel

from src.ui.accessibility.themes import copy_palette_into_global, light_palette
from src.ui.shared.report_editor.section_content_tab import SectionContentTab
from src.ui.styles.helpers import configure_restore_link, restore_link_color
from src.ui.styles.tokens import PALETTE

_EDITED = "Nas reconstruções e vistas seccionais analisadas."
_RESTORED = (
    "Nas reconstruções e vistas seccionais analisadas, não foram identificadas indicações "
    "detectáveis compatíveis com trincas internas, inclusões ou impurezas significativas, "
    "corpos estranhos ou obstruções."
)


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _open_resultados_tab(body: str) -> SectionContentTab:
    tab = SectionContentTab()
    tab.open_content("resultados_inspecao", {"body": body}, is_custom=False)
    return tab


def test_flush_clears_pending_textarea() -> None:
    app = _app()
    tab = _open_resultados_tab(_EDITED)
    tab.show()
    app.processEvents()
    tab._on_field_changed("body", _EDITED)
    assert tab.has_pending_textarea()
    tab._flush_textarea_pending()
    assert not tab.has_pending_textarea()
    tab.close()


def test_patch_skips_focused_textarea_unless_forced() -> None:
    app = _app()
    tab = _open_resultados_tab(_EDITED)
    tab.show()
    widget = tab.field_widgets["body"]
    widget.focus_editor()
    app.processEvents()
    assert widget.has_editor_focus()

    tab.patch_fields("resultados_inspecao", {"body": _RESTORED})
    assert widget.get_text() == _EDITED

    tab.patch_fields("resultados_inspecao", {"body": _RESTORED}, force=True)
    assert widget.get_text() == _RESTORED
    tab.close()


def test_restore_force_patches_focused_editor() -> None:
    app = _app()
    tab = _open_resultados_tab(_EDITED)
    tab.show()
    widget = tab.field_widgets["body"]
    widget.focus_editor()
    app.processEvents()
    tab._on_field_changed("body", _EDITED)
    assert tab.has_pending_textarea()

    emitted: list[tuple[str, str]] = []
    tab.section_field_restore_requested.connect(lambda sid, key: emitted.append((sid, key)))
    tab._on_field_restore("resultados_inspecao", "body")

    assert emitted == [("resultados_inspecao", "body")]
    assert not tab.has_pending_textarea()
    assert tab.should_force_patch()

    tab.patch_fields("resultados_inspecao", {"body": _RESTORED})
    assert widget.get_text() == _RESTORED
    assert not tab.should_force_patch()
    tab.close()


def test_restore_link_uses_dark_blue_on_light_theme() -> None:
    snapshot = {field.name: getattr(PALETTE, field.name) for field in fields(PALETTE)}
    app = _app()
    try:
        copy_palette_into_global(light_palette())
        assert restore_link_color() == PALETTE.senai_blue
        label = QLabel()
        configure_restore_link(label)
        assert PALETTE.senai_blue in label.text()
        assert "Restaurar" in label.text()
    finally:
        for name, value in snapshot.items():
            setattr(PALETTE, name, value)
        app.processEvents()
