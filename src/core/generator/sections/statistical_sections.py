"""Seções do relatório estatístico multi-peça."""
from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Image, PageBreak, Paragraph, Spacer, Table, TableStyle

from src.core.application.statistical_aggregator import (
    display_characteristic_name,
    format_series_limits_range,
    format_stat_number,
    is_geometric_measure_tipo,
    is_linear_measure_tipo,
    measure_tipo_meta,
    parse_measure_number,
    present_measure_tipos,
    series_by_tipo,
    tipo_from_estat_section_id,
)
from src.core.generator.components.chart_renderer import (
    make_temp_chart_path,
    render_cylindricity_chart,
    render_diameter_behavior_chart,
    render_fora_count_chart,
    render_mean_deviation_chart,
)
from src.core.generator.constants import ReportTheme
from src.core.generator.prose_helpers import get_section_heading
from src.core.generator.sections.base import BaseSection, append_section_title
from src.core.domain.chart_figure_defs import section_has_graphics
from src.core.domain.table_row_registry import SECTION_HEADING_DEFAULTS


def _header_style(styles):
    return ParagraphStyle(
        "EstatHeader",
        parent=styles["celula_centro"],
        textColor=colors.white,
        fontName="Helvetica-Bold",
        fontSize=8,
    )


def _summary_table(styles, series_list, contexto_extra, *, section_id: str = ""):
    header = _header_style(styles)
    rows = [[
        Paragraph("Característica", header),
        Paragraph("Nominal", header),
        Paragraph("Limites", header),
        Paragraph("N", header),
        Paragraph("Média", header),
        Paragraph("DesvPad", header),
        Paragraph("Mín.", header),
        Paragraph("Máx.", header),
        Paragraph("Fora", header),
    ]]
    edited = list((contexto_extra.get("table_rows") or {}).get(section_id) or [])
    use_edited = bool(edited) and any(
        str(row.get("n") or row.get("mean") or row.get("maximum") or "").strip()
        for row in edited
    )
    if use_edited:
        for row in edited:
            rows.append([
                Paragraph(str(row.get("label") or "—"), styles["celula"]),
                Paragraph(str(row.get("nominal") or "—"), styles["celula_centro"]),
                Paragraph(str(row.get("limits") or "—"), styles["celula_centro"]),
                Paragraph(str(row.get("n") or "—"), styles["celula_centro"]),
                Paragraph(str(row.get("mean") or "—"), styles["celula_centro"]),
                Paragraph(str(row.get("stdev") or "—"), styles["celula_centro"]),
                Paragraph(str(row.get("minimum") or "—"), styles["celula_centro"]),
                Paragraph(str(row.get("maximum") or "—"), styles["celula_centro"]),
                Paragraph(str(row.get("fora") or "—"), styles["celula_centro"]),
            ])
    else:
        for series in series_list:
            unit = series.unit or ""
            nominal_value = parse_measure_number(series.nominal)
            nominal_text = (
                format_stat_number(nominal_value, unit=unit)
                if nominal_value is not None
                else (f"{series.nominal} {unit}".strip() if series.nominal else "—")
            )
            limits = format_series_limits_range(series)
            name = display_characteristic_name(series.display_name)
            rows.append([
                Paragraph(name, styles["celula"]),
                Paragraph(nominal_text, styles["celula_centro"]),
                Paragraph(limits, styles["celula_centro"]),
                Paragraph(str(series.n), styles["celula_centro"]),
                Paragraph(format_stat_number(series.mean, unit=unit), styles["celula_centro"]),
                Paragraph(format_stat_number(series.stdev, unit=unit), styles["celula_centro"]),
                Paragraph(format_stat_number(series.minimum, unit=unit), styles["celula_centro"]),
                Paragraph(format_stat_number(series.maximum, unit=unit), styles["celula_centro"]),
                Paragraph(str(series.fora_count), styles["celula_centro"]),
            ])
    table = Table(rows, colWidths=[140, 54, 90, 28, 50, 46, 50, 50, 30])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ReportTheme.COR_PRIMARIA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F4F7")]),
        ("GRID", (0, 0), (-1, -1), 0.5, ReportTheme.COR_LINHA),
        ("PADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def _detail_table(styles, series_list, piece_labels):
    header = _header_style(styles)
    header_row = [Paragraph("Peça", header)]
    for series in series_list:
        label = display_characteristic_name(series.display_name)
        if series.unit:
            label = f"{label} ({series.unit})"
        header_row.append(Paragraph(label, header))
    header_row.append(Paragraph("Fora", header))
    rows = [header_row]

    for piece_idx, label in enumerate(piece_labels, start=1):
        fora = 0
        row = [Paragraph(str(piece_idx), styles["celula_centro"])]
        for series in series_list:
            value_map = {idx: (value, status) for idx, value, status in series.values}
            value, status = value_map.get(piece_idx, (None, ""))
            if status and status.lower() == "fora":
                fora += 1
                text = f"{format_stat_number(value)}*"
                color = ReportTheme.COR_ALERTA
            else:
                text = format_stat_number(value)
                color = ReportTheme.COR_SECUNDARIA
            cell = ParagraphStyle(
                f"EstatCell{piece_idx}{series.key}",
                parent=styles["celula_centro"],
                textColor=color,
                fontSize=8,
            )
            row.append(Paragraph(text, cell))
        row.append(Paragraph(str(fora), styles["celula_centro"]))
        rows.append(row)

    n_cols = max(len(header_row), 2)
    first_w = 36
    last_w = 36
    mid = max(40, int((520 - first_w - last_w) / max(1, n_cols - 2)))
    col_widths = [first_w] + [mid] * (n_cols - 2) + [last_w]
    table = Table(rows, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ReportTheme.COR_PRIMARIA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F4F7")]),
        ("GRID", (0, 0), (-1, -1), 0.5, ReportTheme.COR_LINHA),
        ("PADDING", (0, 0), (-1, -1), 2),
    ]))
    return table


def _resolve_tipo(section_id: str, config: dict) -> str:
    configured = str(config.get("measure_tipo") or "").strip()
    if configured:
        return configured
    return tipo_from_estat_section_id(section_id) or "outro"


class EstatResumoTipoSection(BaseSection):
    """Resumo estatístico genérico (diâmetro, altura, cilindricidade, …)."""

    section_id = "estat_resumo_outros"
    measure_tipo = "outro"

    def render(self, story, styles, dados_parseados, contexto_extra):
        section_id = str(self.config.get("section_id") or self.section_id)
        tipo = _resolve_tipo(section_id, {**self.config, "measure_tipo": self.measure_tipo})
        _, heading_default, _, plural, _, _ = measure_tipo_meta(tipo)
        heading = get_section_heading(
            contexto_extra,
            section_id,
            SECTION_HEADING_DEFAULTS.get(section_id, heading_default),
        )
        append_section_title(
            story, heading, styles["secao"], section_id, contexto_extra.get("section_anchor_map"))
        series = series_by_tipo(getattr(dados_parseados, "series", []) or [], tipo)
        if not series:
            story.append(
                Paragraph(f"<i>Nenhuma série de {plural} agregada neste lote.</i>", styles["texto"])
            )
            story.append(Spacer(1, 8))
            return
        story.append(_summary_table(styles, series, contexto_extra, section_id=section_id))
        story.append(Spacer(1, 10))


class EstatDetalheTipoSection(BaseSection):
    """Tabela detalhada genérica por tipo de medida."""

    section_id = "estat_detalhe_outros"
    measure_tipo = "outro"
    page_break_before = True

    def render(self, story, styles, dados_parseados, contexto_extra):
        section_id = str(self.config.get("section_id") or self.section_id)
        tipo = _resolve_tipo(section_id, {**self.config, "measure_tipo": self.measure_tipo})
        _, _, heading_default, plural, _, _ = measure_tipo_meta(tipo)
        heading = get_section_heading(
            contexto_extra,
            section_id,
            SECTION_HEADING_DEFAULTS.get(section_id, heading_default),
        )
        if self.page_break_before:
            story.append(PageBreak())
        append_section_title(
            story, heading, styles["secao"], section_id, contexto_extra.get("section_anchor_map"))
        story.append(
            Paragraph(
                "Valores assinalados com * indicam medição fora dos limites informados "
                "no relatório de origem.",
                styles["texto"],
            )
        )
        story.append(Spacer(1, 6))
        series = series_by_tipo(getattr(dados_parseados, "series", []) or [], tipo)
        labels = list(getattr(dados_parseados, "piece_labels", []) or [])
        if not series:
            story.append(Paragraph(f"<i>Sem {plural} para detalhar.</i>", styles["texto"]))
            return
        story.append(_detail_table(styles, series, labels))
        story.append(Spacer(1, 10))


def _make_resumo(tipo: str, section_id: str):
    class _Section(EstatResumoTipoSection):
        pass

    _Section.section_id = section_id
    _Section.measure_tipo = tipo
    _Section.__name__ = f"EstatResumo_{tipo}"
    return _Section


def _make_detalhe(tipo: str, section_id: str):
    class _Section(EstatDetalheTipoSection):
        pass

    _Section.section_id = section_id
    _Section.measure_tipo = tipo
    _Section.__name__ = f"EstatDetalhe_{tipo}"
    return _Section


EstatResumoDiametrosSection = _make_resumo("diametro", "estat_resumo_diametros")
EstatResumoAlturasSection = _make_resumo("altura", "estat_resumo_alturas")
EstatResumoDimensoesSection = _make_resumo("comprimento", "estat_resumo_dimensoes")
EstatResumoCilindricidadesSection = _make_resumo("cilindricidade", "estat_resumo_cilindricidades")
EstatResumoParalelismosSection = _make_resumo("paralelismo", "estat_resumo_paralelismos")
EstatResumoPerpendicularidadesSection = _make_resumo(
    "perpendicularidade", "estat_resumo_perpendicularidades"
)
EstatResumoCoaxialidadesSection = _make_resumo("coaxialidade", "estat_resumo_coaxialidades")
EstatResumoAngulosSection = _make_resumo("angulo", "estat_resumo_angulos")
EstatResumoOutrosSection = _make_resumo("outro", "estat_resumo_outros")

EstatDetalheDiametrosSection = _make_detalhe("diametro", "estat_detalhe_diametros")
EstatDetalheAlturasSection = _make_detalhe("altura", "estat_detalhe_alturas")
EstatDetalheDimensoesSection = _make_detalhe("comprimento", "estat_detalhe_dimensoes")
EstatDetalheCilindricidadesSection = _make_detalhe("cilindricidade", "estat_detalhe_cilindricidades")
EstatDetalheParalelismosSection = _make_detalhe("paralelismo", "estat_detalhe_paralelismos")
EstatDetalhePerpendicularidadesSection = _make_detalhe(
    "perpendicularidade", "estat_detalhe_perpendicularidades"
)
EstatDetalheCoaxialidadesSection = _make_detalhe("coaxialidade", "estat_detalhe_coaxialidades")
EstatDetalheAngulosSection = _make_detalhe("angulo", "estat_detalhe_angulos")
EstatDetalheOutrosSection = _make_detalhe("outro", "estat_detalhe_outros")


class EstatGraficosSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        heading = get_section_heading(
            contexto_extra,
            "estat_graficos",
            SECTION_HEADING_DEFAULTS.get("estat_graficos", "COMPORTAMENTO E ANÁLISE GRÁFICA"),
        )
        append_section_title(
            story, heading, styles["secao"], "estat_graficos", contexto_extra.get("section_anchor_map"))
        piece_labels = list(getattr(dados_parseados, "piece_labels", []) or [])
        all_series = list(getattr(dados_parseados, "series", []) or [])
        tipos = present_measure_tipos(all_series)
        linear_tipos = [t for t in tipos if is_linear_measure_tipo(t)]
        chart_series = []
        for tipo in linear_tipos or tipos[:1]:
            chart_series.extend(series_by_tipo(all_series, tipo))
        if not chart_series:
            chart_series = all_series

        label_plural = measure_tipo_meta(linear_tipos[0] if linear_tipos else (tipos[0] if tipos else "outro"))[3]
        chart_specs = [
            (
                "behavior_by_piece",
                f"Figura 1 — {label_plural.capitalize()} por peça.",
                render_diameter_behavior_chart(
                    chart_series,
                    piece_labels,
                    make_temp_chart_path("estat_d1_"),
                    title=f"{label_plural.capitalize()} por peça",
                ),
            ),
            (
                "mean_deviation",
                f"Figura 2 — Desvio médio das {label_plural} em relação ao nominal.",
                render_mean_deviation_chart(
                    chart_series,
                    make_temp_chart_path("estat_d2_"),
                ),
            ),
        ]
        _append_chart_figures(story, styles, chart_specs, "estat_graficos", contexto_extra)


class EstatGraficosComplementarSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        heading = get_section_heading(
            contexto_extra,
            "estat_graficos_comp",
            SECTION_HEADING_DEFAULTS.get(
                "estat_graficos_comp", "ANÁLISE GRÁFICA COMPLEMENTAR"
            ),
        )
        story.append(PageBreak())
        append_section_title(
            story, heading,
                styles["secao"],
                "estat_graficos_comp",
                contexto_extra.get("section_anchor_map"),
        )
        all_series = list(getattr(dados_parseados, "series", []) or [])
        geometric = [
            s for s in all_series if is_geometric_measure_tipo(s.tipo)
        ]
        chart_specs = []
        if geometric:
            geo_label = measure_tipo_meta(geometric[0].tipo)[3]
            chart_specs.append(
                (
                    "geo_mean_max",
                    f"Figura 3 — {geo_label.capitalize()}: média e maior valor medido.",
                    render_cylindricity_chart(
                        geometric,
                        make_temp_chart_path("estat_c1_"),
                        title=f"{geo_label.capitalize()}: média e máximo",
                    ),
                )
            )
        chart_specs.append(
            (
                "fora_count",
                "Figura 4 — Quantidade de ocorrências fora dos limites."
                if geometric
                else "Figura 3 — Quantidade de ocorrências fora dos limites.",
                render_fora_count_chart(all_series, make_temp_chart_path("estat_f1_")),
            )
        )
        _append_chart_figures(story, styles, chart_specs, "estat_graficos_comp", contexto_extra)


def _section_media_overrides(section_id: str, contexto_extra: dict) -> dict:
    settings = (contexto_extra.get("section_media_settings") or {}).get(section_id, {})
    media_kinds = settings.get("media_kinds")
    if media_kinds is None:
        prose = (contexto_extra.get("section_prose") or {}).get(section_id, {})
        # Fallback legado via section_overrides embutido na prosa não existe — usa default.
        return {"media_kinds": ["graphics"], "disabled_chart_ids": []}
    return {
        "media_kinds": list(media_kinds),
        "disabled_chart_ids": list(settings.get("disabled_chart_ids") or []),
    }


def _append_chart_figures(story, styles, chart_specs, section_id: str, contexto_extra) -> None:
    overrides = _section_media_overrides(section_id, contexto_extra)
    if not section_has_graphics(section_id, overrides):
        return
    disabled = set(overrides.get("disabled_chart_ids") or [])
    for figure_id, caption, path in chart_specs:
        if figure_id in disabled:
            continue
        if path is None:
            continue
        try:
            story.append(Image(str(path), width=480, height=220, kind="proportional"))
        except Exception:
            continue
        story.append(Paragraph(f"<i>{caption}</i>", styles["texto"]))
        story.append(Spacer(1, 10))
