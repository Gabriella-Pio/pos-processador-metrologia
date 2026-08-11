"""Seção de análise gráfica — gráficos automáticos CMM e fotografias."""
from __future__ import annotations

from reportlab.platypus import Image, Paragraph, Spacer

from src.core.application.cmm_chart_data import build_cmm_chart_groups
from src.core.domain.chart_figure_defs import is_chart_figure_enabled, section_has_graphics
from .base import BaseSection
from ..components.chart_renderer import (
    make_temp_chart_path,
    render_cmm_dimensional_chart,
    render_cmm_geometric_chart,
)
from ..components.photo_grid import append_photo_grid
from ..prose_helpers import render_section_header
from src.core.domain.report_field_registry import PROSE_TEMPLATES


def _section_media_overrides(section_id: str, contexto_extra: dict) -> dict:
    settings = (contexto_extra.get("section_media_settings") or {}).get(section_id, {})
    media_kinds = settings.get("media_kinds")
    if media_kinds is None:
        return {"media_kinds": ["graphics"], "disabled_chart_ids": []}
    return {
        "media_kinds": list(media_kinds),
        "disabled_chart_ids": list(settings.get("disabled_chart_ids") or []),
    }


def _append_chart_image(story, styles, path, caption: str) -> None:
    if path is None:
        return
    try:
        story.append(Image(str(path), width=480, height=220, kind="proportional"))
    except Exception:
        return
    story.append(Paragraph(f"<i>{caption}</i>", styles["texto"]))
    story.append(Spacer(1, 10))


class GraficaSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        render_section_header(
            story,
            styles,
            contexto_extra,
            "grafica",
            prose_default=PROSE_TEMPLATES.get("grafica", {}).get("intro", ""),
            spacer_after_intro=6,
        )

        overrides = _section_media_overrides("grafica", contexto_extra)
        if section_has_graphics("grafica", overrides):
            itens = list(getattr(dados_parseados, "itens_medicao", []) or [])
            dim_groups, geometric = build_cmm_chart_groups(itens)
            fig_no = 1
            show_dimensional = is_chart_figure_enabled("grafica", "dimensional", overrides)
            for group in dim_groups:
                if not show_dimensional:
                    break
                path = render_cmm_dimensional_chart(
                    group,
                    make_temp_chart_path(f"cmm_dim_{group.tipo}_"),
                )
                _append_chart_image(
                    story,
                    styles,
                    path,
                    f"Figura {fig_no} — {group.title}.",
                )
                fig_no += 1
            if geometric and is_chart_figure_enabled("grafica", "geometric", overrides):
                path = render_cmm_geometric_chart(
                    geometric,
                    make_temp_chart_path("cmm_geo_"),
                )
                _append_chart_image(
                    story,
                    styles,
                    path,
                    f"Figura {fig_no} — Características geométricas: valor medido x limite.",
                )

        fotos_secao = contexto_extra.get("fotos_secoes", {}).get("grafica", [])
        captions = contexto_extra.get("foto_captions") or {}
        if fotos_secao:
            story.append(Spacer(1, 4))
            append_photo_grid(
                story,
                list(fotos_secao),
                captions,
                styles,
                section_id="grafica",
                foto_edits=contexto_extra.get("foto_edits"),
                photo_anchors=contexto_extra.get("photo_anchors"),
            )

        story.append(Spacer(1, 10))
