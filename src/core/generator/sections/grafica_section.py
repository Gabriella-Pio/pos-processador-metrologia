from reportlab.platypus import Spacer

from .base import BaseSection
from ..components.photo_grid import append_photo_grid
from ..prose_helpers import render_section_header
from src.core.domain.report_field_registry import PROSE_TEMPLATES


class GraficaSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        render_section_header(
            story,
            styles,
            contexto_extra,
            "grafica",
            prose_default=PROSE_TEMPLATES.get("grafica", {}).get("intro", ""),
            spacer_after_intro=0,
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
