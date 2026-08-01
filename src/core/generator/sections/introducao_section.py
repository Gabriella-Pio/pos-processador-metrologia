from reportlab.lib import colors
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from .base import BaseSection, anchored_section_title
from ..constants import ReportTheme
from ..components.image_handler import ReportImageHandler

class IntroducaoSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        # 1. Títulos Superiores da Peça
        story.append(anchored_section_title("RELATÓRIO TÉCNICO — ANÁLISE DIMENSIONAL E TOMOGRÁFICA", styles['subtitulo'], "introducao", contexto_extra.get("section_anchor_map")))
        story.append(Paragraph(f"{dados_parseados.componente}", styles['titulo']))
        story.append(Spacer(1, 8))

        total_fora = sum(1 for i in dados_parseados.itens_medicao if i.status == "Fora")

        estilo_titulo_tabela = ParagraphStyle(
            'TituloTabelaCabecalho',
            parent=styles['texto'],
            textColor=colors.white,
            fontName="Helvetica-Bold"
        )

        # Gestão dinâmica de fotos por seção
        fotos_secao = contexto_extra.get("fotos_secoes", {}).get("cabecalho", [])
        if not fotos_secao:
            foto_legada = contexto_extra.get("opcoes_extras", {}).get("caminho_foto_peca")
            if foto_legada:
                fotos_secao = [foto_legada]

        caminho_foto_principal = fotos_secao[0] if fotos_secao else None

        # Usando o ImageHandler robusto com auto-proporção que criamos
        conteudo_coluna_foto = ReportImageHandler.criar_elemento_foto(
            caminho_foto_principal, styles=styles
        )

        # 2. Construção da Tabela Unificada de Introdução
        dados_tabela_unica = [
            # Linha 0: Título Objetivo
            [
                Paragraph("OBJETIVO", estilo_titulo_tabela),
                conteudo_coluna_foto 
            ],
            # Linha 1: Conteúdo Objetivo
            [
                Paragraph(f"Apresentar os resultados da inspeção dimensional realizada no componente identificado como <b>{dados_parseados.componente}</b>, com base no relatório ZEISS CALYPSO.", styles['texto']),
                "" 
            ],
            # Linha 2: Título Escopo
            [
                Paragraph("ESCOPO DA ANÁLISE", estilo_titulo_tabela),
                "" 
            ],
            # Linha 3: Conteúdo Escopo
            [
                Paragraph("A análise contempla as características cadastradas, avaliando conformidade com os limites nominais e de tolerância.", styles['texto']),
                "" 
            ],
            # Linha 4: Título Referência
            [
                Paragraph("REFERÊNCIA DE MEDIÇÃO", estilo_titulo_tabela),
                "" 
            ],
            # Linha 5: Conteúdo Referência
            [
                Paragraph("Valores nominais e limites conforme relatório emitido pelo software ZEISS CALYPSO.", styles['texto']),
                "" 
            ],
            # Linha 6: Títulos Amostra e Valores Avaliados
            [
                Paragraph("AMOSTRA", estilo_titulo_tabela),
                Paragraph("VALORES AVALIADOS", estilo_titulo_tabela)
            ],
            # Linha 7: Conteúdos Amostra e Valores Avaliados
            [
                Paragraph("1 peça", styles['texto']),
                Paragraph(f"<b>{dados_parseados.numero_medicoes_cabecalho}</b>", styles['texto'])
            ],
            # Linha 8: Títulos Fora dos Limites e MMC
            [
                Paragraph("FORA DOS LIMITES", estilo_titulo_tabela),
                Paragraph("MÁQUINA DE MEDIÇÃO (MMC)", estilo_titulo_tabela)
            ],
            # Linha 9: Conteúdos Fora dos Limites e MMC
            [
                Paragraph(f"<font color='{ReportTheme.COR_ALERTA.hexval()}'><b>{total_fora} valores</b></font>", styles['texto']),
                Paragraph(f"<b>{dados_parseados.maquina_mmc}</b>", styles['texto'])
            ]
        ]

        tabela_unica = Table(dados_tabela_unica, colWidths=[270, 270])
        
        tabela_unica.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BACKGROUND', (0,0), (-1,-1), colors.white),
            
            ('BACKGROUND', (0, 0), (0, 0), ReportTheme.COR_PRIMARIA),
            ('BACKGROUND', (0, 2), (0, 2), ReportTheme.COR_PRIMARIA),
            ('BACKGROUND', (0, 4), (0, 4), ReportTheme.COR_PRIMARIA),
            ('BACKGROUND', (0, 6), (0, 6), ReportTheme.COR_PRIMARIA),
            ('BACKGROUND', (0, 8), (0, 8), ReportTheme.COR_PRIMARIA),
            ('BACKGROUND', (1, 6), (1, 6), ReportTheme.COR_PRIMARIA),
            ('BACKGROUND', (1, 8), (1, 8), ReportTheme.COR_PRIMARIA),

            ('BOX', (0,0), (-1,-1), 0.5, ReportTheme.COR_LINHA),
            ('INNERGRID', (0,0), (-1,-1), 0.5, ReportTheme.COR_LINHA),
            ('PADDING', (0,0), (-1,-1), 4),
            
            ('SPAN', (1, 0), (1, 5)),
            ('BACKGROUND', (1, 0), (1, 5), colors.HexColor("#F2F4F7")),
        ]))

        story.append(tabela_unica)
        story.append(Spacer(1, 10))