from reportlab.lib import colors
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from .base import BaseSection, anchored_section_title
from ..constants import ReportTheme
from ..prose_helpers import get_section_heading
from src.core.domain.placeholder_utils import resolve_placeholders
from src.core.domain.table_row_registry import SECTION_HEADING_DEFAULTS

class IdentificacaoSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        heading = get_section_heading(
            contexto_extra,
            "identificacao",
            SECTION_HEADING_DEFAULTS["identificacao"],
        )
        story.append(anchored_section_title(heading, styles['secao'], "identificacao", contexto_extra.get("section_anchor_map")))

        ctx = contexto_extra.get("placeholder_context", {})
        table_rows = (contexto_extra.get("table_rows") or {}).get("identificacao", [])

        dados_cab = []
        for row in table_rows:
            label = resolve_placeholders(str(row.get("label", "")), ctx)
            value = resolve_placeholders(str(row.get("value", "")), ctx)
            value_html = f"<b>{value}</b>" if row.get("id") == "numero_mmc" else value
            dados_cab.append([
                Paragraph(f"<b>{label}</b>", styles['texto']),
                Paragraph(value_html, styles['texto']),
            ])

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
