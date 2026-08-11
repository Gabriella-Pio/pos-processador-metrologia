"""Testes dos dados de gráficos CMM (seção gráfica)."""
from __future__ import annotations

from types import SimpleNamespace

from src.core.application.cmm_chart_data import build_cmm_chart_groups


def _item(
    caracteristica: str,
    *,
    valor_medido: str,
    nominal: str = "",
    tol_superior: str = "",
    tol_inferior: str = "",
    tipo: str = "",
) -> SimpleNamespace:
    return SimpleNamespace(
        caracteristica=caracteristica,
        valor_medido=valor_medido,
        nominal=nominal,
        tol_superior=tol_superior,
        tol_inferior=tol_inferior,
        tipo=tipo,
    )


def test_build_cmm_chart_groups_splits_dimensional_and_geometric() -> None:
    itens = [
        _item(
            "Diâmetro Cilindro1",
            valor_medido="25,12",
            nominal="25,00",
            tol_superior="0,10",
            tol_inferior="-0,10",
        ),
        _item(
            "Cilindricidade1",
            valor_medido="0,1754",
            tol_superior="0,1500",
        ),
        _item(
            "Perpendicularidade1",
            valor_medido="0,4975",
            tol_superior="0,0500",
        ),
    ]
    dim_groups, geometric = build_cmm_chart_groups(itens)
    assert len(dim_groups) == 1
    assert dim_groups[0].tipo == "diametro"
    assert len(dim_groups[0].points) == 1
    pt = dim_groups[0].points[0]
    assert pt.measured == 25.12
    assert pt.nominal == 25.0
    assert pt.upper == 25.1
    assert pt.lower == 24.9
    assert len(geometric) == 2
    assert geometric[0].limit == 0.15
    assert geometric[1].limit == 0.05


def test_build_cmm_chart_groups_skips_incomplete_linear_rows() -> None:
    itens = [
        _item("Altura A", valor_medido="10,0"),
    ]
    dim_groups, geometric = build_cmm_chart_groups(itens)
    assert dim_groups == []
    assert geometric == []
