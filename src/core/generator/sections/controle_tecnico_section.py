from reportlab.lib import colors
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from .base import BaseSection, anchored_section_title
from ..constants import ReportTheme
from ..prose_helpers import get_section_heading, get_section_prose
from src.core.domain.placeholder_utils import resolve_placeholders
from src.core.domain.report_field_registry import PROSE_TEMPLATES
from src.core.domain.table_row_registry import SECTION_HEADING_DEFAULTS, default_table_rows


class ControleTecnicoSection(BaseSection):
    """Página de Controle Técnico: responsáveis pela medição, revisão e
    aprovação (quando houver), cargo, e-mail institucional, data e horário.

    Prefere ``contexto_extra["table_rows"]["controle_tecnico"]`` (mesmo padrão
    da identificação). Mantém fallback para ``controle_tecnico`` dict legado.
    """

    def render(self, story, styles, dados_parseados, contexto_extra):
        heading = get_section_heading(
            contexto_extra, "controle_tecnico", SECTION_HEADING_DEFAULTS["controle_tecnico"],
        )
        story.append(anchored_section_title(
            heading, styles['secao'], "controle_tecnico", contexto_extra.get("section_anchor_map"),
        ))

        intro_default = PROSE_TEMPLATES.get("controle_tecnico", {}).get("intro", "")
        intro_text = get_section_prose(contexto_extra, "controle_tecnico", "intro", intro_default)
        if intro_text:
            story.append(Paragraph(intro_text, styles['texto']))

        ctx = contexto_extra.get("placeholder_context", {})
        table_rows = (contexto_extra.get("table_rows") or {}).get("controle_tecnico", [])
        if not table_rows:
            info = contexto_extra.get("controle_tecnico") or {}
            table_rows = default_table_rows("controle_tecnico")
            for row in table_rows:
                row_id = row.get("id", "")
                if row_id in info:
                    row["value"] = info[row_id] or row.get("value", "")

        linhas = []
        for row in table_rows:
            label = resolve_placeholders(str(row.get("label", "")), ctx)
            raw_value = resolve_placeholders(str(row.get("value", "")), ctx)
            if not raw_value:
                raw_value = "Não aplicável" if row.get("id") == "approved_by" else "Não informado"
            linhas.append([
                Paragraph(f"<b>{label}</b>", styles['texto']),
                Paragraph(raw_value, styles['texto']),
            ])

        if not linhas:
            linhas = [[
                Paragraph("<b>Medido por</b>", styles['texto']),
                Paragraph("Não informado", styles['texto']),
            ]]

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
