from pathlib import Path

from src.core.application.cmm_chart_data import CmmDimensionalGroup, CmmDimensionalPoint, CmmGeometricPoint
from src.core.application.statistical_aggregator import short_characteristic_label
from src.core.generator.components.chart_renderer import (
    _bar_figsize,
    render_cmm_dimensional_chart,
    render_cmm_geometric_chart,
)


def test_short_characteristic_label_removes_measure_type_prefix():
    assert short_characteristic_label("Diâmetro area de trabalho") == "area de trabalho"
    assert short_characteristic_label("Cilindricidade encaixe superior") == "encaixe superior"


def test_bar_figsize_grows_with_label_count():
    small = _bar_figsize(3)
    large = _bar_figsize(10)
    assert large[0] > small[0]
    assert small[1] == large[1] == 3.4


def test_render_cmm_dimensional_chart_writes_file(tmp_path: Path) -> None:
    group = CmmDimensionalGroup(
        tipo="diametro",
        title="Resultado dimensional — diâmetros",
        points=(
            CmmDimensionalPoint(
                label="Cilindro1",
                measured=25.12,
                nominal=25.0,
                upper=25.1,
                lower=24.9,
                tipo="diametro",
            ),
        ),
    )
    out = tmp_path / "dim.png"
    path = render_cmm_dimensional_chart(group, out)
    assert path is not None
    assert path.is_file()
    assert path.stat().st_size > 0


def test_render_cmm_geometric_chart_writes_file(tmp_path: Path) -> None:
    points = [
        CmmGeometricPoint(label="Cilindricidade1", measured=0.1754, limit=0.15, tipo="cilindricidade"),
        CmmGeometricPoint(label="Perpendicularidade1", measured=0.4975, limit=0.05, tipo="perpendicularidade"),
    ]
    out = tmp_path / "geo.png"
    path = render_cmm_geometric_chart(points, out)
    assert path is not None
    assert path.is_file()
    assert path.stat().st_size > 0
