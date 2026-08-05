from reportlab.platypus import Paragraph, Spacer
from .base import BaseSection, anchored_section_title
from ..components.photo_grid import append_photo_grid
from ..prose_helpers import get_section_prose, get_section_heading
from src.core.domain.report_field_registry import PROSE_TEMPLATES
from src.core.domain.table_row_registry import SECTION_HEADING_DEFAULTS

class GraficaSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        heading = get_section_heading(
            contexto_extra, "grafica", SECTION_HEADING_DEFAULTS["grafica"],
        )
        story.append(anchored_section_title(heading, styles['secao'], "grafica", contexto_extra.get("section_anchor_map")))
        intro_default = PROSE_TEMPLATES.get("grafica", {}).get("intro", "")
        intro_text = get_section_prose(contexto_extra, "grafica", "intro", intro_default)
        story.append(Paragraph(intro_text, styles['texto']))
        
        fotos_secao = contexto_extra.get("fotos_secoes", {}).get("grafica", [])
        captions = contexto_extra.get("foto_captions") or {}
        if fotos_secao:
            story.append(Spacer(1, 4))
            append_photo_grid(story, list(fotos_secao), captions, styles)

        story.append(Spacer(1, 10))
