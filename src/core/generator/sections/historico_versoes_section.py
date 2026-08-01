from reportlab.lib import colors
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from .base import BaseSection
from ..constants import ReportTheme


class HistoricoVersoesSection(BaseSection):
    """Histórico de Versões do Relatório: número da versão, data, hora,
    responsável e breve descrição das alterações — deve compor o PDF final
    (funcionalidade obrigatória 5).

    Recebe a lista já pronta via ``contexto_extra["historico_versoes"]``,
    montada pelo ``RealReportExporterAdapter`` a partir de
    ``ReportDocument.version_history``.
    """

    def render(self, story, styles, dados_parseados, contexto_extra):
        entradas = contexto_extra.get("historico_versoes") or []

        story.append(Paragraph("HISTÓRICO DE VERSÕES", styles['secao']))

        if not entradas:
            story.append(Paragraph(
                "Nenhuma alteração adicional registrada além da geração inicial deste relatório.",
                styles['texto']
            ))
            story.append(Spacer(1, 10))
            return

        cabecalho = [
            Paragraph("<font color='white'><b>Versão</b></font>", styles['celula_centro']),
            Paragraph("<font color='white'><b>Data/Hora</b></font>", styles['celula_centro']),
            Paragraph("<font color='white'><b>Responsável</b></font>", styles['celula']),
            Paragraph("<font color='white'><b>Descrição</b></font>", styles['celula']),
        ]
        linhas = [cabecalho]

        for entrada in entradas:
            linhas.append([
                Paragraph(f"v{entrada['version_number']}", styles['celula_centro']),
                Paragraph(entrada['timestamp_str'], styles['celula_centro']),
                Paragraph(entrada['responsible_name'], styles['celula']),
                Paragraph(entrada['description'], styles['celula']),
            ])

        tabela = Table(linhas, colWidths=[45, 110, 140, 245])
        tabela.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), ReportTheme.COR_PRIMARIA),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F4F7")]),
            ('GRID', (0, 0), (-1, -1), 0.5, ReportTheme.COR_LINHA),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))

        story.append(tabela)
        story.append(Spacer(1, 10))
