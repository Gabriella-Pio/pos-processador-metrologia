from reportlab.lib import colors
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from .base import BaseSection, anchored_section_title
from ..constants import ReportTheme
from ..prose_helpers import get_section_heading
from src.core.domain.table_row_registry import SECTION_HEADING_DEFAULTS


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

        heading = get_section_heading(
            contexto_extra, "controle_tecnico", SECTION_HEADING_DEFAULTS["controle_tecnico"],
        )
        story.append(anchored_section_title(heading, styles['secao'], "controle_tecnico", contexto_extra.get("section_anchor_map")))
        story.append(Paragraph(
            "Registro dos responsáveis técnicos pela medição, revisão e, quando "
            "aplicável, aprovação deste relatório.",
            styles['texto']
        ))

        prose = contexto_extra.get("section_prose", {}).get("controle_tecnico", {})
        label_measured = prose.get("label_measured_by") or "Medido por"
        label_reviewed = prose.get("label_reviewed_by") or "Revisado por"
        label_approved = prose.get("label_approved_by") or "Aprovado por"
        label_role = prose.get("label_role") or "Cargo"
        label_email = prose.get("label_institutional_email") or "E-mail institucional"

        linhas = [
            [Paragraph(f"<b>{label_measured}</b>", styles['texto']),
             Paragraph(info.get("measured_by") or "Não informado", styles['texto'])],
            [Paragraph(f"<b>{label_reviewed}</b>", styles['texto']),
             Paragraph(info.get("reviewed_by") or "Não informado", styles['texto'])],
            [Paragraph(f"<b>{label_approved}</b>", styles['texto']),
             Paragraph(info.get("approved_by") or "Não aplicável", styles['texto'])],
            [Paragraph(f"<b>{label_role}</b>", styles['texto']),
             Paragraph(info.get("role") or "Não informado", styles['texto'])],
            [Paragraph(f"<b>{label_email}</b>", styles['texto']),
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
