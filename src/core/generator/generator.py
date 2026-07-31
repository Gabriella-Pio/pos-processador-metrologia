import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from src.core.parser.utils import ParserUtils

class ReportTheme:
    """Centraliza a identidade visual corporativa SENAI / ZEISS (Princípio DRY e Coesão)."""
    COR_PRIMARIA = colors.HexColor("#003366")    # Azul Corporativo
    COR_SECUNDARIA = colors.HexColor("#4A607A")  # Cinza Metálico
    COR_ALERTA = colors.HexColor("#D9534F")      # Vermelho para itens Fora
    COR_SUCESSO = colors.HexColor("#5CB85C")     # Verde para itens Dentro
    COR_LINHA = colors.HexColor("#E0E0E0")       # Cinza claro para grades

class ReportStyles:
    """Centraliza a criação de estilos tipográficos do ReportLab."""
    @staticmethod
    def criar_estilos():
        styles = getSampleStyleSheet()
        return {
            'titulo': ParagraphStyle('TituloRelatorio', parent=styles['Heading1'], fontSize=15, textColor=ReportTheme.COR_PRIMARIA, spaceAfter=4, alignment=1, fontName="Helvetica-Bold"),
            'subtitulo': ParagraphStyle('SubTituloRelatorio', parent=styles['Normal'], fontSize=10, textColor=ReportTheme.COR_SECUNDARIA, spaceAfter=10, alignment=1, fontName="Helvetica"),
            'secao': ParagraphStyle('SecaoCabecalho', parent=styles['Heading2'], fontSize=11, textColor=ReportTheme.COR_PRIMARIA, spaceBefore=10, spaceAfter=4, fontName="Helvetica-Bold"),
            'texto': ParagraphStyle('TextoPadrao', parent=styles['Normal'], fontSize=9, textColor=colors.black, fontName="Helvetica", spaceAfter=4),
            'celula': ParagraphStyle('CelulaTabela', parent=styles['Normal'], fontSize=8, textColor=colors.black, fontName="Helvetica"),
            'celula_centro': ParagraphStyle('CelulaTabelaCentro', parent=styles['Normal'], fontSize=8, textColor=colors.black, fontName="Helvetica", alignment=1),
            'bullet': ParagraphStyle('TextoBullet', parent=styles['Normal'], fontSize=8.5, textColor=colors.black, fontName="Helvetica", leftIndent=15, spaceAfter=4)
        }

class ReportGenerator:
    """
    Classe principal (Facade) responsável por coordenar a construção 
    do relatório executivo enriquecido.
    """

    @classmethod
    def gerar_relatorio_enriquecido(
        cls, 
        dados_parseados, 
        caminho_saida: str, 
        cliente_projeto: str = "Não informado", 
        componente_avaliado: str = "Não informado",
        opcoes_extras: dict = None
    ):
        if opcoes_extras is None:
            opcoes_extras = {"incluir_tomografia": False}

        doc = SimpleDocTemplate(
            caminho_saida, pagesize=letter,
            rightMargin=36, leftMargin=36,
            topMargin=36, bottomMargin=36
        )
        
        story = []
        styles = ReportStyles.criar_estilos()

        # Constrói o documento por meio de seções isoladas (Métodos Especializados)
        cls._adicionar_cabecalho_institucional(story, styles, dados_parseados)
        cls._adicionar_secao_identificacao(story, styles, dados_parseados, cliente_projeto, componente_avaliado)
        cls._adicionar_secao_resultados_dimensionais(story, styles, dados_parseados)
        cls._adicionar_secao_analise_grafica(story, styles)
        
        if opcoes_extras.get("incluir_tomografia", False):
            cls._adicionar_secao_tomografia(story, styles)
            
        cls._adicionar_secao_interpretacao(story, styles, dados_parseados)
        cls._adicionar_secao_conclusao(story, styles, dados_parseados)

        # Compilação final com rodapé dinâmico
        doc.build(story, onFirstPage=cls._adicionar_rodape, onLaterPages=cls._adicionar_rodape)
        print(f"[Gerador] Relatório PDF enriquecido gerado com sucesso em: {caminho_saida}")

    @staticmethod
    def _adicionar_cabecalho_institucional(story, styles, dados_parseados):
        story.append(Paragraph("CENTRO DE EXCELÊNCIA EM METROLOGIA", styles['subtitulo']))
        story.append(Paragraph("SENAI ZEISS — GOIÂNIA / GO", styles['subtitulo']))
        story.append(Spacer(1, 4))
        story.append(Paragraph("RELATÓRIO TÉCNICO — ANÁLISE DIMENSIONAL E TOMOGRÁFICA", styles['titulo']))
        story.append(Spacer(1, 8))

        story.append(Paragraph(
            f"<b>OBJETIVO:</b> Apresentar os resultados da inspeção dimensional realizada no componente "
            f"identificado como <b>{dados_parseados.componente}</b>, com base no relatório de medição ZEISS CALYPSO.", 
            styles['texto']
        ))
        story.append(Paragraph("<b>ESCOPO DA ANÁLISE:</b> A análise contempla as características cadastradas no programa de medição, avaliando conformidade com os limites nominais e de tolerância.", styles['texto']))
        story.append(Paragraph("<b>REFERÊNCIA DE MEDIÇÃO:</b> Valores nominais, limites de tolerâncias e resultados individuais conforme relatório emitido pelo software ZEISS CALYPSO.", styles['texto']))

        total_fora = sum(1 for i in dados_parseados.itens_medicao if i.status == "Fora")
        
        dados_amostra = [
            [Paragraph("<b>AMOSTRA:</b> 1 peça", styles['texto']), Paragraph(f"<b>VALORES AVALIADOS:</b> {dados_parseados.numero_medicoes_cabecalho}", styles['texto'])],
            [Paragraph(f"<b>FORA DOS LIMITES:</b> <font color='{ReportTheme.COR_ALERTA.hexval()}'><b>{total_fora} valores</b></font>", styles['texto']), Paragraph(f"<b>MMC:</b> {dados_parseados.maquina_mmc}", styles['texto'])]
        ]
        tabela_amostra = Table(dados_amostra, colWidths=[270, 270])
        tabela_amostra.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F9F9F9")),
            ('BOX', (0,0), (-1,-1), 0.5, ReportTheme.COR_SECUNDARIA),
            ('INNERGRID', (0,0), (-1,-1), 0.5, ReportTheme.COR_LINHA),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(tabela_amostra)
        story.append(Spacer(1, 10))

    @staticmethod
    def _adicionar_secao_identificacao(story, styles, dados_parseados, cliente_projeto, componente_avaliado):
        story.append(Paragraph("1. IDENTIFICAÇÃO E CONDIÇÕES DE MEDIÇÃO", styles['secao']))
        
        dados_cab = [
            [Paragraph("<b>Cliente / Projeto:</b>", styles['texto']), Paragraph(cliente_projeto, styles['texto'])],
            [Paragraph("<b>Componente Avaliado:</b>", styles['texto']), Paragraph(componente_avaliado, styles['texto'])],
            [Paragraph("<b>Identificação no Relatório CALYPSO:</b>", styles['texto']), Paragraph(dados_parseados.componente, styles['texto'])],
            [Paragraph("<b>Máquina de Medição (MMC):</b>", styles['texto']), Paragraph(dados_parseados.maquina_mmc, styles['texto'])],
            [Paragraph("<b>Número da MMC:</b>", styles['texto']), Paragraph(f"<b>{dados_parseados.numero_mmc}</b>", styles['texto'])],
            [Paragraph("<b>Software de Medição:</b>", styles['texto']), Paragraph(f"{dados_parseados.software} {dados_parseados.versao_software}", styles['texto'])],
            [Paragraph("<b>Operador:</b>", styles['texto']), Paragraph(f"{dados_parseados.operador}", styles['texto'])],
            [Paragraph("<b>Data/Hora:</b>", styles['texto']), Paragraph(f"{dados_parseados.data_hora}", styles['texto'])],
            [Paragraph("<b>Quantidade de características:</b>", styles['texto']), Paragraph(f"{dados_parseados.numero_medicoes_cabecalho}", styles['texto'])]
        ]

        tabela_cab = Table(dados_cab, colWidths=[160, 380])
        tabela_cab.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, ReportTheme.COR_SECUNDARIA),
            ('INNERGRID', (0,0), (-1,-1), 0.5, ReportTheme.COR_LINHA),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(tabela_cab)
        story.append(Spacer(1, 10))

    @staticmethod
    def _adicionar_secao_resultados_dimensionais(story, styles, dados_parseados):
        story.append(Paragraph("2. RESULTADOS DIMENSIONAIS", styles['secao']))
        story.append(Paragraph(
            "A tabela abaixo apresenta os resultados extraídos do relatório de medição dimensional. "
            "A classificação “Dentro” ou “Fora” foi determinada com base nos limites cadastrados no relatório ZEISS CALYPSO.",
            styles['texto']
        ))

        cabecalho_tabela = [
            Paragraph("<b>Tipo</b>", styles['celula']),
            Paragraph("<b>Característica</b>", styles['celula']),
            Paragraph("<b>Medido</b>", styles['celula_centro']),
            Paragraph("<b>Nominal</b>", styles['celula_centro']),
            Paragraph("<b>Tol. +</b>", styles['celula_centro']),
            Paragraph("<b>Tol. -</b>", styles['celula_centro']),
            Paragraph("<b>Desvio</b>", styles['celula_centro']),
            Paragraph("<b>Status</b>", styles['celula_centro'])
        ]

        linhas_tabela = [cabecalho_tabela]

        for item in dados_parseados.itens_medicao:
            cor_status = ReportTheme.COR_ALERTA if item.status == "Fora" else ReportTheme.COR_SUCESSO
            status_parag = Paragraph(f"<font color='{cor_status.hexval()}'><b>{item.status}</b></font>", styles['celula_centro'])
            
            linha = [
                Paragraph(item.tipo, styles['celula']),
                Paragraph(item.caracteristica, styles['celula']),
                Paragraph(item.valor_medido, styles['celula_centro']),
                Paragraph(item.nominal, styles['celula_centro']),
                Paragraph(item.tol_superior, styles['celula_centro']),
                Paragraph(item.tol_inferior, styles['celula_centro']),
                Paragraph(item.desvio, styles['celula_centro']),
                status_parag
            ]
            linhas_tabela.append(linha)

        tabela_itens = Table(linhas_tabela, colWidths=[70, 110, 60, 65, 55, 55, 55, 50])
        tabela_itens.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), ReportTheme.COR_PRIMARIA),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F2F4F7")]),
            ('GRID', (0,0), (-1,-1), 0.5, ReportTheme.COR_LINHA),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))

        for cell in cabecalho_tabela:
            cell.style.textColor = colors.white

        story.append(tabela_itens)
        story.append(Spacer(1, 10))

    @staticmethod
    def _adicionar_secao_analise_grafica(story, styles):
        story.append(Paragraph("3. ANÁLISE GRÁFICA DOS RESULTADOS", styles['secao']))
        story.append(Paragraph("Espaço reservado para inserção de fotografias, diagramas ou gráficos analíticos do componente.", styles['texto']))
        story.append(Spacer(1, 10))

    @staticmethod
    def _adicionar_secao_tomografia(story, styles):
        story.append(Paragraph("4. INSPEÇÃO TOMOGRÁFICA", styles['secao']))
        story.append(Paragraph("Avaliação qualitativa da integridade interna do componente realizada por ensaio tomográfico.", styles['texto']))
        story.append(Spacer(1, 10))

    @staticmethod
    def _adicionar_secao_interpretacao(story, styles, dados_parseados):
        story.append(Paragraph("5. INTERPRETAÇÃO DOS RESULTADOS", styles['secao']))
        story.append(Paragraph(
            f"Análise detalhada das <b>{len(dados_parseados.itens_medicao)}</b> características inspecionadas no componente <b>{dados_parseados.componente}</b>:",
            styles['texto']
        ))
        story.append(Spacer(1, 4))

        for item in dados_parseados.itens_medicao:
            tem_tol = item.tol_superior != "N/A" and item.tol_inferior != "N/A"
            
            if tem_tol:
                val_medido_f = ParserUtils.converter_para_float(item.valor_medido)
                nominal_f = ParserUtils.converter_para_float(item.nominal)
                sup_f = ParserUtils.converter_para_float(item.tol_superior)
                inf_f = ParserUtils.converter_para_float(item.tol_inferior)

                limite_superior = nominal_f + sup_f
                limite_inferior = nominal_f - abs(inf_f)

                if item.status == "Dentro":
                    texto_item = (
                        f"• A característica <b>{item.caracteristica}</b>, do tipo {item.tipo}, apresentou valor medido de "
                        f"<b>{item.valor_medido}</b>, permanecendo <b>dentro</b> dos limites cadastrados de "
                        f"{limite_inferior:.4f} a {limite_superior:.4f}."
                    )
                else:
                    if val_medido_f > limite_superior:
                        excedente = val_medido_f - limite_superior
                        texto_item = (
                            f"• A característica <b>{item.caracteristica}</b>, do tipo {item.tipo}, apresentou valor medido de "
                            f"<b>{item.valor_medido}</b>, ficando <b>acima</b> dos limites cadastrados de {limite_inferior:.4f} a {limite_superior:.4f}, "
                            f"resultando em um excedente de <font color='{ReportTheme.COR_ALERTA.hexval()}'><b>+{excedente:.4f}</b></font>."
                        )
                    elif val_medido_f < limite_inferior:
                        faltante = limite_inferior - val_medido_f
                        texto_item = (
                            f"• A característica <b>{item.caracteristica}</b>, do tipo {item.tipo}, apresentou valor medido de "
                            f"<b>{item.valor_medido}</b>, ficando <b>abaixo</b> dos limites cadastrados de {limite_inferior:.4f} a {limite_superior:.4f}, "
                            f"resultando em um déficit de <font color='{ReportTheme.COR_ALERTA.hexval()}'><b>-{faltante:.4f}</b></font>."
                        )
                    else:
                        texto_item = (
                            f"• A característica <b>{item.caracteristica}</b> ({item.tipo}) apresentou valor medido de "
                            f"<b>{item.valor_medido}</b> fora dos limites."
                        )
            else:
                texto_item = (
                    f"• A característica <b>{item.caracteristica}</b>, do tipo {item.tipo}, apresentou valor medido de "
                    f"<b>{item.valor_medido}</b>, sem valores de tolerância cadastrados no relatório de origem."
                )

            story.append(Paragraph(texto_item, styles['bullet']))

        story.append(Spacer(1, 10))

    @staticmethod
    def _adicionar_secao_conclusao(story, styles, dados_parseados):
        story.append(Paragraph("6. CONCLUSÃO", styles['secao']))
        total_fora = sum(1 for i in dados_parseados.itens_medicao if i.status == "Fora")
        
        conclusao_texto = (
            "O componente analisado encontra-se reprovado parcialmente devido às divergências dimensionais constatadas, "
            "cabendo avaliação do setor de engenharia e qualidade para liberação ou retrabalho." if total_fora > 0 else
            "O componente analisado atende plenamente aos requisitos dimensionais especificados no relatório de origem, estando aprovado."
        )
        story.append(Paragraph(conclusao_texto, styles['texto']))

    @staticmethod
    def _adicionar_rodape(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(ReportTheme.COR_SECUNDARIA)
        canvas.drawString(36, 18, "CEM SENAI | ZEISS Goiânia - GO • Uso restrito ao cliente")
        canvas.drawRightString(letter[0] - 36, 18, f"Página {doc.page}")
        canvas.restoreState()