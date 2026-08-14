"""Testes de formatação de unidades e resumo dimensional."""
from types import SimpleNamespace

from src.core.domain.measure_display import (
    ensure_measure_unit,
    format_item_measure_cells,
    infer_measure_unit,
)
from src.core.domain.measurement_interpretation import (
    build_dimensional_summary,
    format_dimensional_summary_sentence,
)


def _item(**kwargs) -> SimpleNamespace:
    defaults = {
        "caracteristica": "DIM A",
        "tipo": "length",
        "valor_medido": "1,0000 mm",
        "nominal": "1,0000",
        "tol_superior": "0,1000",
        "tol_inferior": "0,1000",
        "desvio": "0,0000",
        "status": "Dentro",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_infer_measure_unit_mm_and_inch() -> None:
    assert infer_measure_unit("81,9972 mm") == "mm"
    assert infer_measure_unit("3.2150 inch") == "inch"
    assert infer_measure_unit("90 °") == "°"
    assert infer_measure_unit("1,0") == ""


def test_ensure_measure_unit_appends_once() -> None:
    assert ensure_measure_unit("1,0000", "mm") == "1,0000 mm"
    assert ensure_measure_unit("1,0000 mm", "mm") == "1,0000 mm"
    assert ensure_measure_unit("N/A", "mm") == "N/A"


def test_format_item_measure_cells_propagates_medido_unit() -> None:
    cells = format_item_measure_cells(_item())
    assert cells["valor_medido"] == "1,0000 mm"
    assert cells["nominal"] == "1,0000 mm"
    assert cells["tol_superior"] == "0,1000 mm"
    assert cells["tol_inferior"] == "0,1000 mm"
    assert cells["desvio"] == "0,0000 mm"


def test_format_item_measure_cells_inch() -> None:
    cells = format_item_measure_cells(
        _item(valor_medido="2,0000 inch", nominal="2,0000", desvio="0,0010")
    )
    assert cells["nominal"].endswith("inch")
    assert cells["desvio"].endswith("inch")


def test_summary_dentro() -> None:
    text = format_dimensional_summary_sentence(_item())
    assert "DIM A" in text
    assert "dentro dos limites informados" in text


def test_summary_acima_e_abaixo() -> None:
    acima = format_dimensional_summary_sentence(
        _item(valor_medido="1,5000 mm", status="Fora"),
    )
    abaixo = format_dimensional_summary_sentence(
        _item(valor_medido="0,5000 mm", status="Fora"),
    )
    assert "acima do limite superior" in acima
    assert "abaixo do limite inferior" in abaixo


def test_build_dimensional_summary_joins_items() -> None:
    text = build_dimensional_summary(
        [
            _item(caracteristica="diâmetro interno"),
            _item(
                caracteristica="perpendicularidade",
                valor_medido="1,5000 mm",
                status="Fora",
            ),
        ]
    )
    assert text.startswith("Resumo dimensional:")
    assert "diâmetro interno" in text
    assert "perpendicularidade" in text
    assert "acima do limite superior" in text
    lines = text.split("\n")
    assert len(lines) == 3
    assert lines[0] == "Resumo dimensional:"
    assert lines[1].startswith("O diâmetro interno")
    assert lines[2].startswith("O perpendicularidade") or "perpendicularidade" in lines[2]
