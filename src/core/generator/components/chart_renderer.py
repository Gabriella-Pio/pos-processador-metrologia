"""Renderização de gráficos do relatório estatístico (matplotlib ou fallback ReportLab)."""
from __future__ import annotations

import tempfile
from pathlib import Path

from src.core.application.cmm_chart_data import CmmDimensionalGroup, CmmGeometricPoint
from src.core.application.statistical_aggregator import (
    StatisticalCharacteristicSeries,
    parse_measure_number,
    short_characteristic_label,
)


def render_diameter_behavior_chart(
    series_list: list[StatisticalCharacteristicSeries],
    piece_labels: list[str],
    output_path: Path,
    *,
    title: str = "Diâmetros por peça",
    ylabel: str = "Valor medido",
) -> Path | None:
    """Figura: valores por peça para características lineares selecionadas."""
    if not series_list:
        return None
    return _render_line_chart(
        series_list[:4],
        piece_labels,
        output_path,
        title=title,
        ylabel=ylabel,
    )


def render_mean_deviation_chart(
    series_list: list[StatisticalCharacteristicSeries],
    output_path: Path,
) -> Path | None:
    """Figura: desvio médio em relação ao nominal."""
    labels: list[str] = []
    values: list[float] = []
    colors: list[str] = []
    for series in series_list:
        mean = series.mean
        nominal = parse_measure_number(series.nominal)
        if mean is None or nominal is None:
            continue
        labels.append(short_characteristic_label(series.display_name))
        values.append(mean - nominal)
        colors.append("#C0392B" if series.fora_count > 0 else "#1F4E79")
    if not labels:
        return None
    return _render_bar_chart(
        labels,
        values,
        output_path,
        title="Desvio médio dos diâmetros em relação ao nominal",
        ylabel="Desvio médio (mm)",
        colors=colors,
    )


def render_cylindricity_chart(
    series_list: list[StatisticalCharacteristicSeries],
    output_path: Path,
    *,
    title: str = "Cilindricidade: média e máximo",
    ylabel: str = "Valor",
) -> Path | None:
    labels: list[str] = []
    means: list[float] = []
    maxima: list[float] = []
    for series in series_list:
        if series.mean is None or series.maximum is None:
            continue
        labels.append(short_characteristic_label(series.display_name))
        means.append(series.mean)
        maxima.append(series.maximum)
    if not labels:
        return None
    return _render_grouped_bar_chart(
        labels,
        {"Média": means, "Máximo": maxima},
        output_path,
        title=title,
        ylabel=ylabel,
    )


def render_fora_count_chart(
    series_list: list[StatisticalCharacteristicSeries],
    output_path: Path,
) -> Path | None:
    labels = [short_characteristic_label(s.display_name) for s in series_list]
    values = [float(s.fora_count) for s in series_list]
    if not labels:
        return None
    colors = ["#C0392B" if v > 0 else "#1F4E79" for v in values]
    return _render_bar_chart(
        labels,
        values,
        output_path,
        title="Ocorrências fora dos limites",
        ylabel="Quantidade",
        colors=colors,
        value_digits=0,
    )


def render_cmm_dimensional_chart(
    group: CmmDimensionalGroup,
    output_path: Path,
) -> Path | None:
    """Valor medido x nominal com faixa de tolerância (relatório CMM individual)."""
    if not group.points:
        return None
    plt = _try_matplotlib()
    if plt is None:
        return _render_placeholder(output_path, group.title)
    fig, ax = plt.subplots(figsize=_bar_figsize(len(group.points)), dpi=120)
    labels = [pt.label for pt in group.points]
    x = list(range(len(group.points)))
    measured = [pt.measured for pt in group.points]
    ax.scatter(x, measured, color="#1F4E79", s=42, zorder=3, label="Valor medido")
    for idx, pt in enumerate(group.points):
        ax.hlines(pt.nominal, idx - 0.32, idx + 0.32, colors="#1F4E79", linewidth=2)
        ax.hlines(pt.upper, idx - 0.32, idx + 0.32, colors="#1F4E79", linewidth=1, linestyles="dashed")
        ax.hlines(pt.lower, idx - 0.32, idx + 0.32, colors="#1F4E79", linewidth=1, linestyles="dashed")
    ax.plot([], [], color="#1F4E79", linewidth=2, label="Nominal")
    ax.plot([], [], color="#1F4E79", linewidth=1, linestyle="dashed", label="Limite superior")
    ax.plot([], [], color="#1F4E79", linewidth=1, linestyle="dashed", label="Limite inferior")
    ax.set_title(group.title)
    ax.set_ylabel("Dimensão (mm)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=7)
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(fontsize=7, loc="best")
    fig.subplots_adjust(bottom=0.28)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path if output_path.is_file() else None


def render_cmm_geometric_chart(
    points: list[CmmGeometricPoint],
    output_path: Path,
) -> Path | None:
    """Valor medido x limite estabelecido para características geométricas."""
    if not points:
        return None
    labels = [pt.label for pt in points]
    measured = [pt.measured for pt in points]
    limits = [pt.limit for pt in points]
    return _render_grouped_bar_chart(
        labels,
        {"Valor medido": measured, "Limite estabelecido": limits},
        output_path,
        title="Características geométricas — valor medido x limite",
        ylabel="Valor (mm)",
        series_colors={"Valor medido": "#1F4E79", "Limite estabelecido": "#E67E22"},
    )


def _try_matplotlib():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        return plt
    except Exception:
        return None


def _format_chart_number(value: float, *, digits: int | None = 4) -> str:
    if digits is None:
        digits = 4
    if digits <= 0:
        return str(int(round(float(value))))
    return f"{float(value):.{digits}f}".replace(".", ",")


def _annotate_bar_values(
    ax,
    bars,
    values: list[float],
    *,
    digits: int | None = 4,
) -> None:
    """Coloca o valor exato acima (positivo) ou abaixo (negativo) de cada barra."""
    if not values:
        return
    y_min, y_max = ax.get_ylim()
    span = (y_max - y_min) or 1.0
    pad = span * 0.02
    for bar, value in zip(bars, values):
        if value is None:
            continue
        text = _format_chart_number(float(value), digits=digits)
        x = bar.get_x() + bar.get_width() / 2
        height = bar.get_height()
        if value >= 0:
            y = height + pad
            va = "bottom"
        else:
            y = height - pad
            va = "top"
        ax.text(
            x,
            y,
            text,
            ha="center",
            va=va,
            fontsize=7,
            fontweight="bold",
            color="#1F2937",
            clip_on=False,
        )


def _annotate_line_values(
    ax,
    xs: list[float | int],
    ys: list[float | None],
    *,
    digits: int = 4,
    max_labels: int = 24,
) -> None:
    points = [(x, y) for x, y in zip(xs, ys) if y is not None]
    if not points or len(points) > max_labels:
        return
    for x, y in points:
        value = float(y)
        ax.annotate(
            _format_chart_number(value, digits=digits),
            xy=(x, value),
            xytext=(0, 6 if value >= 0 else -6),
            textcoords="offset points",
            ha="center",
            va="bottom" if value >= 0 else "top",
            fontsize=6.5,
            fontweight="bold",
            color="#1F2937",
        )


def _pad_ylim_for_labels(ax, *, factor: float = 0.14) -> None:
    lo, hi = ax.get_ylim()
    span = (hi - lo) or 1.0
    margin = span * factor
    ax.set_ylim(lo - margin, hi + margin)


def _bar_figsize(n_labels: int) -> tuple[float, float]:
    width = min(9.5, max(7.2, 5.8 + n_labels * 0.35))
    return (width, 3.4)


def _render_line_chart(
    series_list: list[StatisticalCharacteristicSeries],
    piece_labels: list[str],
    output_path: Path,
    *,
    title: str,
    ylabel: str,
) -> Path | None:
    plt = _try_matplotlib()
    if plt is None:
        return _render_placeholder(output_path, title)
    fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=120)
    x = list(range(1, len(piece_labels) + 1))
    total_points = len(x) * max(1, len(series_list))
    label_each_series = total_points <= 24
    for series in series_list:
        ys = []
        value_map = {idx: value for idx, value, _ in series.values}
        for idx in x:
            ys.append(value_map.get(idx))
        ax.plot(
            x,
            ys,
            marker="o",
            linewidth=1.6,
            label=short_characteristic_label(series.display_name),
        )
        if label_each_series:
            _annotate_line_values(ax, x, ys, digits=4, max_labels=24)
    ax.set_title(title)
    ax.set_xlabel("Peça")
    ax.set_ylabel(ylabel)
    ax.set_xticks(x)
    ax.set_xticklabels([str(i) for i in x], fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7, loc="best")
    if label_each_series:
        _pad_ylim_for_labels(ax)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path if output_path.is_file() else None


def _render_bar_chart(
    labels: list[str],
    values: list[float],
    output_path: Path,
    *,
    title: str,
    ylabel: str,
    colors: list[str] | str | None = None,
    value_digits: int | None = 4,
) -> Path | None:
    plt = _try_matplotlib()
    if plt is None:
        return _render_placeholder(output_path, title)
    fig, ax = plt.subplots(figsize=_bar_figsize(len(labels)), dpi=120)
    bar_colors = colors or "#1F4E79"
    bars = ax.bar(range(len(labels)), values, color=bar_colors)
    ax.axhline(0, color="#94A3B8", linewidth=0.8)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=7)
    ax.grid(True, axis="y", alpha=0.3)
    _annotate_bar_values(ax, bars, values, digits=value_digits)
    _pad_ylim_for_labels(ax)
    fig.subplots_adjust(bottom=0.28)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path if output_path.is_file() else None


def _render_grouped_bar_chart(
    labels: list[str],
    series_map: dict[str, list[float]],
    output_path: Path,
    *,
    title: str,
    ylabel: str,
    series_colors: dict[str, str] | None = None,
) -> Path | None:
    plt = _try_matplotlib()
    if plt is None:
        return _render_placeholder(output_path, title)
    fig, ax = plt.subplots(figsize=_bar_figsize(len(labels)), dpi=120)
    x = list(range(len(labels)))
    width = 0.35
    keys = list(series_map.keys())
    for offset, key in enumerate(keys):
        xpos = [i + (offset - (len(keys) - 1) / 2) * width for i in x]
        values = series_map[key]
        color = (series_colors or {}).get(key)
        bars = ax.bar(xpos, values, width, label=key, color=color) if color else ax.bar(xpos, values, width, label=key)
        _annotate_bar_values(ax, bars, values, digits=4)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=7)
    ax.legend(fontsize=8)
    ax.grid(True, axis="y", alpha=0.3)
    _pad_ylim_for_labels(ax)
    fig.subplots_adjust(bottom=0.28)
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path if output_path.is_file() else None


def _render_placeholder(output_path: Path, title: str) -> Path | None:
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return None
    img = Image.new("RGB", (900, 360), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)
    draw.rectangle((8, 8, 892, 352), outline=(31, 78, 121), width=2)
    draw.text((24, 24), title, fill=(31, 78, 121))
    draw.text((24, 64), "Instale matplotlib para gráficos detalhados.", fill=(100, 116, 139))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return output_path if output_path.is_file() else None


def make_temp_chart_path(prefix: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(prefix=prefix, suffix=".png", delete=False)
    tmp.close()
    return Path(tmp.name)
