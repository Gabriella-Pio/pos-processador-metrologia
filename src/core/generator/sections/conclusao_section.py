from reportlab.platypus import Paragraph
from .base import BaseSection, anchored_section_title

class ConclusaoSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        story.append(anchored_section_title("6. CONCLUSÃO", styles['secao'], "conclusao", contexto_extra.get("section_anchor_map")))
        total_fora = sum(1 for i in dados_parseados.itens_medicao if i.status == "Fora")
        
        texto_customizado = self.config.get("texto_personalizado")
        if texto_customizado:
            conclusao_texto = texto_customizado
        else:
            conclusao_texto = (
                "O componente analisado encontra-se reprovado parcialmente devido às divergências dimensionais constatadas, "
                "cabendo avaliação do setor de engenharia e qualidade para liberação ou retrabalho." if total_fora > 0 else
                "O componente analisado atende plenamente aos requisitos dimensionais especificados no relatório de origem, estando aprovado."
            )
            
        story.append(Paragraph(conclusao_texto, styles['texto']))