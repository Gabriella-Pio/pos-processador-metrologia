from reportlab.platypus import Paragraph, Spacer
from .base import BaseSection

class TomografiaSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        story.append(Paragraph("4. INSPEÇÃO TOMOGRÁFICA", styles['secao']))
        story.append(Paragraph("Avaliação qualitativa da integridade interna do componente realizada por ensaio tomográfico.", styles['texto']))
        story.append(Spacer(1, 10))