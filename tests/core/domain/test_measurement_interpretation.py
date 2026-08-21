"""Testes dos textos de interpretação por medição."""
from types import SimpleNamespace

from src.core.domain.measurement_interpretation import (
    build_dimensional_summary,
    format_item_bullet_html,
    format_item_bullet_plain,
    item_has_tolerance,
)


def _item(**kwargs) -> SimpleNamespace:
    defaults = {
        "caracteristica": "DIM A",
        "tipo": "length",
        "valor_medido": "1.0",
        "nominal": "1.0",
        "tol_superior": "0.1",
        "tol_inferior": "0.1",
        "status": "Dentro",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_item_has_tolerance() -> None:
    assert item_has_tolerance(_item())
    assert not item_has_tolerance(_item(tol_superior="N/A"))


def test_plain_bullet_dentro() -> None:
    text = format_item_bullet_plain(_item())
    assert "**DIM A**" in text
    assert "**dentro**" in text
    assert "dentro dos limites" in text.replace("**", "")


def test_plain_bullet_fora_acima() -> None:
    text = format_item_bullet_plain(
        _item(valor_medido="1.5", status="Fora"),
    )
    assert "**acima**" in text
    assert "**+0.4000**" in text


def test_html_bullet_matches_editor_markdown() -> None:
    item = _item()
    html = format_item_bullet_html(item, alert_color="#ff0000")
    assert "<b>DIM A</b>" in html
    assert "<b>dentro</b>" in html
    assert "<b>1.0</b>" in html


def test_html_bullet_includes_alert_markup() -> None:
    html = format_item_bullet_html(
        _item(valor_medido="0.5", status="Fora"),
        alert_color="#ff0000",
    )
    assert "<b>" in html
    assert "font color='#ff0000'" in html
