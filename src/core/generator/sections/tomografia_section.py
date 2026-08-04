from reportlab.platypus import Paragraph, Spacer
from .base import BaseSection, anchored_section_title
from ..prose_helpers import get_section_prose, get_section_heading
from src.core.domain.report_field_registry import PROSE_TEMPLATES
from src.core.domain.table_row_registry import SECTION_HEADING_DEFAULTS

class TomografiaSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        heading = get_section_heading(
            contexto_extra, "tomografia", SECTION_HEADING_DEFAULTS["tomografia"],
        )
        story.append(anchored_section_title(heading, styles['secao'], "tomografia", contexto_extra.get("section_anchor_map")))
        intro_default = PROSE_TEMPLATES.get("tomografia", {}).get("intro", "")
        intro_text = get_section_prose(contexto_extra, "tomografia", "intro", intro_default)
        story.append(Paragraph(intro_text, styles['texto']))
        story.append(Spacer(1, 10))