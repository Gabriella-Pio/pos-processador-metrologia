from src.core.domain.chart_figure_defs import (
    chart_figure_defs,
    disabled_chart_ids,
    enabled_chart_count,
    is_chart_figure_enabled,
    section_has_graphics,
)


def test_section_has_graphics_respects_media_kinds():
    assert section_has_graphics("estat_graficos", {"media_kinds": ["graphics"]})
    assert not section_has_graphics("estat_graficos", {"media_kinds": []})


def test_disabled_chart_ids_filter_figures():
    overrides = {"media_kinds": ["graphics"], "disabled_chart_ids": ["fora_count"]}
    assert is_chart_figure_enabled("estat_graficos_comp", "fora_count", overrides) is False
    assert is_chart_figure_enabled("estat_graficos_comp", "geo_mean_max", overrides) is True
    assert enabled_chart_count("estat_graficos_comp", overrides) == 1


def test_chart_figure_defs_for_statistical_sections():
    assert len(chart_figure_defs("estat_graficos")) == 2
    assert len(chart_figure_defs("estat_graficos_comp")) == 2
    assert len(chart_figure_defs("grafica")) == 2
    assert disabled_chart_ids({"disabled_chart_ids": ["a", "b"]}) == {"a", "b"}
