from reportlab.platypus import Paragraph, Spacer
from .base import BaseSection, anchored_section_title
from ..components.image_handler import ReportImageHandler

class GraficaSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        story.append(anchored_section_title("3. ANÁLISE GRÁFICA DOS RESULTADOS", styles['secao'], "grafica", contexto_extra.get("section_anchor_map")))
        story.append(Paragraph("Espaço reservado para inserção de fotografias, diagramas ou gráficos analíticos do componente.", styles['texto']))
        
        # Exemplo opcional: renderizando fotos dinâmicas caso o usuário tenha anexado fotos nesta seção
        fotos_secao = contexto_extra.get("fotos_secoes", {}).get("grafica", [])
        for caminho in fotos_secao:
            elem = ReportImageHandler.criar_elemento_foto(caminho, styles=styles)
            story.append(Spacer(1, 4))
            story.append(elem)

        story.append(Spacer(1, 10))