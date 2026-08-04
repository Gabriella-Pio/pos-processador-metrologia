from reportlab.platypus import Paragraph
from .base import BaseSection, anchored_section_title
from ..prose_helpers import get_section_prose, get_section_heading
from src.core.domain.report_field_registry import PROSE_TEMPLATES
from src.core.domain.table_row_registry import SECTION_HEADING_DEFAULTS

class ConclusaoSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        heading = get_section_heading(
            contexto_extra, "conclusao", SECTION_HEADING_DEFAULTS["conclusao"],
        )
        story.append(anchored_section_title(heading, styles['secao'], "conclusao", contexto_extra.get("section_anchor_map")))
        total_fora = sum(1 for i in dados_parseados.itens_medicao if i.status == "Fora")
        
        texto_customizado = get_section_prose(contexto_extra, "conclusao", "texto", "")
        if not texto_customizado:
            texto_customizado = self.config.get("texto_personalizado")
        if texto_customizado:
            conclusao_texto = texto_customizado
        else:
            tmpl = PROSE_TEMPLATES.get("conclusao", {})
            conclusao_texto = (
                tmpl.get("texto_reprovado", "") if total_fora > 0 else tmpl.get("texto_aprovado", "")
            )
            
        story.append(Paragraph(conclusao_texto, styles['texto']))