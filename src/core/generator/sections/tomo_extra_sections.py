"""Seções auxiliares do relatório tomográfico (método, registro, resultados, observações)."""
from reportlab.platypus import Spacer

from .base import BaseSection
from ..components.photo_grid import append_photo_grid
from ..prose_helpers import render_section_header
from src.core.domain.report_field_registry import PROSE_TEMPLATES


class MetodoEscopoSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        render_section_header(
            story,
            styles,
            contexto_extra,
            "metodo_escopo",
            prose_key="body",
            prose_default=PROSE_TEMPLATES.get("metodo_escopo", {}).get("body", ""),
            spacer_after_intro=10,
        )


class RegistroComponenteSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        render_section_header(
            story,
            styles,
            contexto_extra,
            "registro_componente",
            prose_default=PROSE_TEMPLATES.get("registro_componente", {}).get("intro", ""),
            spacer_after_intro=6,
        )
        fotos = contexto_extra.get("fotos_secoes", {}).get("registro_componente", [])
        captions = contexto_extra.get("foto_captions") or {}
        if fotos:
            append_photo_grid(story, list(fotos), captions, styles)
        story.append(Spacer(1, 6))


class ResultadosInspecaoSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        render_section_header(
            story,
            styles,
            contexto_extra,
            "resultados_inspecao",
            prose_key="body",
            prose_default=PROSE_TEMPLATES.get("resultados_inspecao", {}).get("body", ""),
            spacer_after_intro=10,
        )


class ObservacoesLimitacoesSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        render_section_header(
            story,
            styles,
            contexto_extra,
            "observacoes_limitacoes",
            prose_key="body",
            prose_default=PROSE_TEMPLATES.get("observacoes_limitacoes", {}).get("body", ""),
            spacer_after_intro=10,
        )
