from reportlab.lib import colors
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from .base import BaseSection
from ..constants import ReportTheme


class ControleTecnicoSection(BaseSection):
    """Página de Controle Técnico: responsáveis pela medição, revisão e
    aprovação (quando houver), cargo, e-mail institucional, data e horário.

    Os dados chegam via ``contexto_extra["controle_tecnico"]`` — um dict
    simples montado pelo ``RealReportExporterAdapter`` a partir do
    ``TechnicalControlInfo`` da UI, mantendo esta seção desacoplada do
    formato interno usado na camada de apresentação.
    """

    def render(self, story, styles, dados_parseados, contexto_extra):
        info = contexto_extra.get("controle_tecnico") or {}

        story.append(Paragraph("CONTROLE TÉCNICO", styles['secao']))
        story.append(Paragraph(
            "Registro dos responsáveis técnicos pela medição, revisão e, quando "
            "aplicável, aprovação deste relatório.",
            styles['texto']
        ))

        linhas = [
            [Paragraph("<b>Medido por</b>", styles['texto']),
             Paragraph(info.get("measured_by") or "Não informado", styles['texto'])],
            [Paragraph("<b>Revisado por</b>", styles['texto']),
             Paragraph(info.get("reviewed_by") or "Não informado", styles['texto'])],
            [Paragraph("<b>Aprovado por</b>", styles['texto']),
             Paragraph(info.get("approved_by") or "Não aplicável", styles['texto'])],
            [Paragraph("<b>Cargo</b>", styles['texto']),
             Paragraph(info.get("role") or "Não informado", styles['texto'])],
            [Paragraph("<b>E-mail institucional</b>", styles['texto']),
             Paragraph(info.get("institutional_email") or "Não informado", styles['texto'])],
            [Paragraph("<b>Data/Hora</b>", styles['texto']),
             Paragraph(info.get("timestamp_str") or "Não informado", styles['texto'])],
        ]

        tabela = Table(linhas, colWidths=[200, 340])
        tabela.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor("#F2F4F7")]),
            ('BOX', (0, 0), (-1, -1), 0.5, ReportTheme.COR_LINHA),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, ReportTheme.COR_LINHA),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))

        story.append(tabela)
        story.append(Spacer(1, 10))
