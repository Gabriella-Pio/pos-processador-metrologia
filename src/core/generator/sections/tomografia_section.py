from reportlab.platypus import Spacer

from .base import BaseSection
from ..components.photo_grid import append_photo_grid
from ..prose_helpers import render_section_header
from src.core.domain.report_field_registry import PROSE_TEMPLATES


class TomografiaSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        render_section_header(
            story,
            styles,
            contexto_extra,
            "tomografia",
            prose_default=PROSE_TEMPLATES.get("tomografia", {}).get("intro", ""),
            spacer_after_intro=8,
        )
        fotos = contexto_extra.get("fotos_secoes", {}).get("tomografia", [])
        captions = contexto_extra.get("foto_captions") or {}
        if fotos:
            append_photo_grid(
                story,
                list(fotos),
                captions,
                styles,
                section_id="tomografia",
                foto_edits=contexto_extra.get("foto_edits"),
                photo_anchors=contexto_extra.get("photo_anchors"),
            )
        story.append(Spacer(1, 6))
