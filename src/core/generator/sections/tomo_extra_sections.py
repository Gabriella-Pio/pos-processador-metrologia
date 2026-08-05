"""Seções auxiliares do relatório tomográfico (método, registro, resultados, observações)."""
from reportlab.platypus import Paragraph, Spacer

from .base import BaseSection, anchored_section_title
from ..components.photo_grid import append_photo_grid
from ..prose_helpers import get_section_prose, get_section_heading
from src.core.domain.report_field_registry import PROSE_TEMPLATES
from src.core.domain.table_row_registry import SECTION_HEADING_DEFAULTS


class MetodoEscopoSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        heading = get_section_heading(
            contexto_extra, "metodo_escopo", SECTION_HEADING_DEFAULTS["metodo_escopo"],
        )
        story.append(
            anchored_section_title(
                heading, styles["secao"], "metodo_escopo", contexto_extra.get("section_anchor_map")
            )
        )
        body = get_section_prose(
            contexto_extra,
            "metodo_escopo",
            "body",
            PROSE_TEMPLATES.get("metodo_escopo", {}).get("body", ""),
        )
        story.append(Paragraph(body, styles["texto"]))
        story.append(Spacer(1, 10))


class RegistroComponenteSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        heading = get_section_heading(
            contexto_extra, "registro_componente", SECTION_HEADING_DEFAULTS["registro_componente"],
        )
        story.append(
            anchored_section_title(
                heading, styles["secao"], "registro_componente", contexto_extra.get("section_anchor_map")
            )
        )
        intro = get_section_prose(
            contexto_extra,
            "registro_componente",
            "intro",
            PROSE_TEMPLATES.get("registro_componente", {}).get("intro", ""),
        )
        if intro:
            story.append(Paragraph(intro, styles["texto"]))
            story.append(Spacer(1, 6))
        fotos = contexto_extra.get("fotos_secoes", {}).get("registro_componente", [])
        captions = contexto_extra.get("foto_captions") or {}
        if fotos:
            append_photo_grid(story, list(fotos), captions, styles)
        story.append(Spacer(1, 6))


class ResultadosInspecaoSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        heading = get_section_heading(
            contexto_extra, "resultados_inspecao", SECTION_HEADING_DEFAULTS["resultados_inspecao"],
        )
        story.append(
            anchored_section_title(
                heading, styles["secao"], "resultados_inspecao", contexto_extra.get("section_anchor_map")
            )
        )
        body = get_section_prose(
            contexto_extra,
            "resultados_inspecao",
            "body",
            PROSE_TEMPLATES.get("resultados_inspecao", {}).get("body", ""),
        )
        story.append(Paragraph(body, styles["texto"]))
        story.append(Spacer(1, 10))


class ObservacoesLimitacoesSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        heading = get_section_heading(
            contexto_extra,
            "observacoes_limitacoes",
            SECTION_HEADING_DEFAULTS["observacoes_limitacoes"],
        )
        story.append(
            anchored_section_title(
                heading,
                styles["secao"],
                "observacoes_limitacoes",
                contexto_extra.get("section_anchor_map"),
            )
        )
        body = get_section_prose(
            contexto_extra,
            "observacoes_limitacoes",
            "body",
            PROSE_TEMPLATES.get("observacoes_limitacoes", {}).get("body", ""),
        )
        story.append(Paragraph(body, styles["texto"]))
        story.append(Spacer(1, 10))
