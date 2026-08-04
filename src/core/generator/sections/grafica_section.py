from reportlab.platypus import Paragraph, Spacer
from .base import BaseSection, anchored_section_title
from ..components.image_handler import ReportImageHandler
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
        
        # Exemplo opcional: renderizando fotos dinâmicas caso o usuário tenha anexado fotos nesta seção
        fotos_secao = contexto_extra.get("fotos_secoes", {}).get("grafica", [])
        for caminho in fotos_secao:
            elem = ReportImageHandler.criar_elemento_foto(caminho, styles=styles)
            story.append(Spacer(1, 4))
            story.append(elem)

        story.append(Spacer(1, 10))