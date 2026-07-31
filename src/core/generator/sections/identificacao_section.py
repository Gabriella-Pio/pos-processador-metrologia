from reportlab.lib import colors
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from .base import BaseSection
from ..constants import ReportTheme

class IdentificacaoSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        cliente_projeto = contexto_extra.get("cliente_projeto", "Não informado")
        componente_avaliado = contexto_extra.get("componente_avaliado", "Não informado")

        story.append(Paragraph("1. IDENTIFICAÇÃO E CONDIÇÕES DE MEDIÇÃO", styles['secao']))
        
        dados_cab = [
            [Paragraph("<b>Cliente / Projeto</b>", styles['texto']), Paragraph(cliente_projeto, styles['texto'])],
            [Paragraph("<b>Componente Avaliado</b>", styles['texto']), Paragraph(componente_avaliado, styles['texto'])],
            [Paragraph("<b>Identificação no Relatório CALYPSO</b>", styles['texto']), Paragraph(dados_parseados.componente, styles['texto'])],
            [Paragraph("<b>Máquina de Medição</b>", styles['texto']), Paragraph(dados_parseados.maquina_mmc, styles['texto'])],
            [Paragraph("<b>Número da MMC</b>", styles['texto']), Paragraph(f"<b>{dados_parseados.numero_mmc}</b>", styles['texto'])],
            [Paragraph("<b>Software</b>", styles['texto']), Paragraph(f"{dados_parseados.software} {dados_parseados.versao_software}", styles['texto'])],
            [Paragraph("<b>Operador</b>", styles['texto']), Paragraph(f"{dados_parseados.operador}", styles['texto'])],
            [Paragraph("<b>Data/Hora da Medição</b>", styles['texto']), Paragraph(f"{dados_parseados.data_hora}", styles['texto'])],
            [Paragraph("<b>Quantidade de características</b>", styles['texto']), Paragraph(f"{dados_parseados.numero_medicoes_cabecalho} valore(s) medido(s)", styles['texto'])]
        ]

        tabela_cab = Table(dados_cab, colWidths=[200, 340])
        tabela_cab.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, colors.HexColor("#F2F4F7")]),
            ('BOX', (0,0), (-1,-1), 0.5, ReportTheme.COR_LINHA),
            ('INNERGRID', (0,0), (-1,-1), 0.5, ReportTheme.COR_LINHA),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        
        story.append(tabela_cab)
        story.append(Spacer(1, 10))