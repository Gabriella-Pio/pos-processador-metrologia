from reportlab.platypus import Paragraph, Spacer
from .base import BaseSection, anchored_section_title

class TomografiaSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        story.append(anchored_section_title("4. INSPEÇÃO TOMOGRÁFICA", styles['secao'], "tomografia", contexto_extra.get("section_anchor_map")))
        story.append(Paragraph("Avaliação qualitativa da integridade interna do componente realizada por ensaio tomográfico.", styles['texto']))
        story.append(Spacer(1, 10))