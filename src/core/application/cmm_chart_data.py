"""Dados para gráficos da seção gráfica em relatórios CMM (peça única)."""
from __future__ import annotations

from dataclasses import dataclass

from src.core.application.statistical_aggregator import (
    classify_characteristic_tipo,
    is_geometric_measure_tipo,
    is_linear_measure_tipo,
    measure_tipo_meta,
    parse_measure_number,
    short_characteristic_label,
)


@dataclass(frozen=True)
class CmmDimensionalPoint:
    label: str
    measured: float
    nominal: float
    upper: float
    lower: float
    tipo: str


@dataclass(frozen=True)
class CmmGeometricPoint:
    label: str
    measured: float
    limit: float
    tipo: str


@dataclass(frozen=True)
class CmmDimensionalGroup:
    tipo: str
    title: str
    points: tuple[CmmDimensionalPoint, ...]


def _absolute_limits(
    nominal: float | None,
    tol_sup: float | None,
    tol_inf: float | None,
    *,
    geometric: bool,
) -> tuple[float | None, float | None]:
    if geometric:
        limit = tol_sup if tol_sup is not None else tol_inf
        if limit is None:
            return None, None
        return 0.0, limit

    if nominal is None:
        return None, None
    upper = nominal + tol_sup if tol_sup is not None else None
    lower = nominal + tol_inf if tol_inf is not None else None
    return upper, lower


def build_cmm_chart_groups(itens: list) -> tuple[list[CmmDimensionalGroup], list[CmmGeometricPoint]]:
    """Agrupa medições de uma peça para os gráficos da seção ``grafica``."""
    dimensional_by_tipo: dict[str, list[CmmDimensionalPoint]] = {}
    geometric: list[CmmGeometricPoint] = []

    for item in itens or []:
        name = str(getattr(item, "caracteristica", "") or "").strip()
        if not name:
            continue
        measured = parse_measure_number(getattr(item, "valor_medido", ""))
        if measured is None:
            continue
        nominal = parse_measure_number(getattr(item, "nominal", ""))
        tol_sup = parse_measure_number(getattr(item, "tol_superior", ""))
        tol_inf = parse_measure_number(getattr(item, "tol_inferior", ""))
        tipo_hint = str(getattr(item, "tipo", "") or "")
        tipo = classify_characteristic_tipo(name, tipo_hint)
        label = short_characteristic_label(name)

        if is_geometric_measure_tipo(tipo):
            _upper, limit = _absolute_limits(nominal, tol_sup, tol_inf, geometric=True)
            if limit is None:
                continue
            geometric.append(
                CmmGeometricPoint(
                    label=label,
                    measured=measured,
                    limit=limit,
                    tipo=tipo,
                )
            )
            continue

        if not is_linear_measure_tipo(tipo):
            continue

        upper, lower = _absolute_limits(nominal, tol_sup, tol_inf, geometric=False)
        if nominal is None or upper is None or lower is None:
            continue
        dimensional_by_tipo.setdefault(tipo, []).append(
            CmmDimensionalPoint(
                label=label,
                measured=measured,
                nominal=nominal,
                upper=upper,
                lower=lower,
                tipo=tipo,
            )
        )

    dim_groups: list[CmmDimensionalGroup] = []
    for tipo, points in dimensional_by_tipo.items():
        if not points:
            continue
        _, _, heading, plural, _, _ = measure_tipo_meta(tipo)
        dim_groups.append(
            CmmDimensionalGroup(
                tipo=tipo,
                title=f"Resultado dimensional — {plural}",
                points=tuple(points[:10]),
            )
        )

    dim_groups.sort(key=lambda g: g.tipo)
    return dim_groups, geometric[:12]
