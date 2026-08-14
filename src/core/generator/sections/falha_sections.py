"""Seções do template de análise de falha (óptica + discussão do mecanismo)."""
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from .base import BaseSection
from ..components.photo_grid import append_photo_grid
from ..constants import ReportTheme
from ..prose_helpers import (
    append_anchored_section_title,
    append_section_prose_paragraph,
    format_prose_paragraph,
    get_section_prose,
    render_section_header,
)
from src.core.domain.placeholder_utils import resolve_placeholders
from src.core.domain.report_field_registry import PROSE_TEMPLATES
from src.core.domain.table_row_registry import default_discussao_falha_rows


class InspecaoOpticaSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        render_section_header(
            story,
            styles,
            contexto_extra,
            "inspecao_optica",
            prose_key="body",
            prose_default=PROSE_TEMPLATES.get("inspecao_optica", {}).get("body", ""),
            spacer_after_intro=6,
        )
        fotos = contexto_extra.get("fotos_secoes", {}).get("inspecao_optica", [])
        captions = contexto_extra.get("foto_captions") or {}
        if fotos:
            append_photo_grid(
                story,
                list(fotos),
                captions,
                styles,
                section_id="inspecao_optica",
                foto_edits=contexto_extra.get("foto_edits"),
                photo_anchors=contexto_extra.get("photo_anchors"),
            )
        story.append(Spacer(1, 6))


class ResultadosSuperficiesSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        append_anchored_section_title(story, styles, contexto_extra, "resultados_superficies")
        intro_default = PROSE_TEMPLATES.get("resultados_superficies", {}).get("intro", "")
        append_section_prose_paragraph(
            story,
            styles,
            contexto_extra,
            "resultados_superficies",
            "intro",
            intro_default,
            spacer_after=4,
        )
        prose = contexto_extra.get("section_prose", {}).get("resultados_superficies", {})
        bullet_keys = sorted(
            (k for k in prose if k.startswith("bullet_") and str(prose.get(k) or "").strip()),
            key=lambda k: int(k.split("_", 1)[1]) if k.split("_", 1)[1].isdigit() else 999,
        )
        keys = bullet_keys or [f"bullet_{i}" for i in range(1, 5)]
        for key in keys:
            bullet = get_section_prose(contexto_extra, "resultados_superficies", key, "")
            if bullet:
                story.append(Paragraph(f"•  {format_prose_paragraph(bullet)}", styles["bullet"]))
        story.append(Spacer(1, 10))


class DiscussaoFalhaSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        render_section_header(
            story,
            styles,
            contexto_extra,
            "discussao_falha",
            prose_default=PROSE_TEMPLATES.get("discussao_falha", {}).get("intro", ""),
            spacer_after_intro=8,
        )
        ctx = contexto_extra.get("placeholder_context", {})
        table_rows = (contexto_extra.get("table_rows") or {}).get("discussao_falha", [])
        if not table_rows:
            table_rows = default_discussao_falha_rows()

        header = [
            Paragraph("<b>Etapa</b>", styles["texto"]),
            Paragraph("<b>Mecanismo</b>", styles["texto"]),
            Paragraph("<b>Descrição</b>", styles["texto"]),
        ]
        linhas = [header]
        for row in table_rows:
            etapa = resolve_placeholders(str(row.get("id", "")), ctx)
            mecanismo = resolve_placeholders(str(row.get("label", "")), ctx)
            descricao = resolve_placeholders(str(row.get("value", "")), ctx)
            linhas.append([
                Paragraph(etapa, styles["texto"]),
                Paragraph(mecanismo, styles["texto"]),
                Paragraph(descricao, styles["texto"]),
            ])

        tabela = Table(linhas, colWidths=[50, 170, 320])
        tabela.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF0FA")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F4F7")]),
                ("BOX", (0, 0), (-1, -1), 0.5, ReportTheme.COR_LINHA),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, ReportTheme.COR_LINHA),
                ("PADDING", (0, 0), (-1, -1), 5),
            ])
        )
        story.append(tabela)
        story.append(Spacer(1, 10))
