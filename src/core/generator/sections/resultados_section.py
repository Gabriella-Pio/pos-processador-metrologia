from reportlab.lib import colors
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from .base import BaseSection, anchored_section_title
from ..constants import ReportTheme
from ..prose_helpers import get_section_prose, get_section_heading
from src.core.domain.report_field_registry import PROSE_TEMPLATES
from src.core.domain.table_row_registry import SECTION_HEADING_DEFAULTS

class ResultadosSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        heading = get_section_heading(
            contexto_extra, "resultados", SECTION_HEADING_DEFAULTS["resultados"],
        )
        story.append(anchored_section_title(heading, styles['secao'], "resultados", contexto_extra.get("section_anchor_map")))
        intro_default = PROSE_TEMPLATES.get("resultados", {}).get("intro", "")
        intro_text = get_section_prose(contexto_extra, "resultados", "intro", intro_default)
        story.append(Paragraph(intro_text, styles['texto']))

        estilo_cabecalho_tabela = ParagraphStyle('CelulaCabecalho', parent=styles['celula_centro'], textColor=colors.white, fontName="Helvetica-Bold")
        estilo_cabecalho_esquerda = ParagraphStyle('CelulaCabecalhoEsquerda', parent=styles['celula'], textColor=colors.white, fontName="Helvetica-Bold")

        cabecalho_tabela = [
            Paragraph("Item", estilo_cabecalho_tabela),
            Paragraph("Tipo", estilo_cabecalho_esquerda),
            Paragraph("Característica", estilo_cabecalho_esquerda),
            Paragraph("Medido", estilo_cabecalho_tabela),
            Paragraph("Nominal", estilo_cabecalho_tabela),
            Paragraph("Tol. +", estilo_cabecalho_tabela),
            Paragraph("Tol. -", estilo_cabecalho_tabela),
            Paragraph("Desvio", estilo_cabecalho_tabela),
            Paragraph("Status", estilo_cabecalho_tabela)
        ]

        linhas_tabela = [cabecalho_tabela]

        for idx, item in enumerate(dados_parseados.itens_medicao, 1):
            cor_status = ReportTheme.COR_ALERTA if item.status == "Fora" else ReportTheme.COR_SUCESSO
            status_parag = Paragraph(f"<font color='{cor_status.hexval()}'><b>{item.status}</b></font>", styles['celula_centro'])
            
            linha = [
                Paragraph(str(idx), styles['celula_centro']),
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

        tabela_itens = Table(linhas_tabela, colWidths=[30, 80, 110, 65, 55, 50, 50, 55, 45])
        tabela_itens.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), ReportTheme.COR_PRIMARIA),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F2F4F7")]),
            ('GRID', (0,0), (-1,-1), 0.5, ReportTheme.COR_LINHA),
            ('PADDING', (0,0), (-1,-1), 4),
        ]))

        story.append(tabela_itens)
        story.append(Spacer(1, 10))