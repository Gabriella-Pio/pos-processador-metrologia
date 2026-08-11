"""Definições dos gráficos automáticos das seções estatísticas."""
from __future__ import annotations

from dataclasses import dataclass

from src.core.domain.field_definitions import CHART_SECTION_IDS, effective_media_kinds


@dataclass(frozen=True)
class ChartFigureDef:
    id: str
    label: str


CHART_FIGURES_BY_SECTION: dict[str, tuple[ChartFigureDef, ...]] = {
    "grafica": (
        ChartFigureDef("dimensional", "Resultados dimensionais (medido x nominal)"),
        ChartFigureDef("geometric", "Características geométricas (medido x limite)"),
    ),
    "estat_graficos": (
        ChartFigureDef("behavior_by_piece", "Figura 1 — Valores por peça"),
        ChartFigureDef("mean_deviation", "Figura 2 — Desvio médio vs nominal"),
    ),
    "estat_graficos_comp": (
        ChartFigureDef("geo_mean_max", "Figura 3 — Média e máximo"),
        ChartFigureDef("fora_count", "Figura 4 — Ocorrências fora dos limites"),
    ),
}


def chart_figure_defs(section_id: str) -> tuple[ChartFigureDef, ...]:
    return CHART_FIGURES_BY_SECTION.get(section_id, ())


def section_has_graphics(section_id: str, overrides: dict | None = None) -> bool:
    if section_id not in CHART_SECTION_IDS:
        return False
    return "graphics" in effective_media_kinds(section_id, overrides)


def disabled_chart_ids(overrides: dict | None = None) -> set[str]:
    raw = (overrides or {}).get("disabled_chart_ids")
    if not isinstance(raw, list):
        return set()
    return {str(item) for item in raw if item}


def is_chart_figure_enabled(section_id: str, figure_id: str, overrides: dict | None = None) -> bool:
    if not section_has_graphics(section_id, overrides):
        return False
    return figure_id not in disabled_chart_ids(overrides)


def enabled_chart_count(section_id: str, overrides: dict | None = None) -> int:
    defs = chart_figure_defs(section_id)
    if not defs:
        return 0
    disabled = disabled_chart_ids(overrides)
    return sum(1 for item in defs if item.id not in disabled)
