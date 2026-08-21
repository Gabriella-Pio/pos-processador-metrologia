from reportlab.lib import colors
from reportlab.platypus import KeepInFrame, Paragraph, Spacer, Table, TableStyle
from .base import BaseSection, append_section_title
from ..constants import ReportTheme
from ..prose_helpers import append_section_prose_paragraph, get_section_heading
from src.core.domain.pdf_plain_text import pdf_paragraph_text
from src.core.domain.report_field_registry import PROSE_TEMPLATES
from src.core.domain.table_row_registry import SECTION_HEADING_DEFAULTS

# Frame "Later" do relatório: ~528 × 708 pt. Folga para título + prosa acima da tabela.
_MAX_HISTORY_TABLE_HEIGHT = 620
_HISTORY_TABLE_WIDTH = 540


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

        heading = get_section_heading(
            contexto_extra,
            "historico_versoes",
            SECTION_HEADING_DEFAULTS["historico_versoes"],
        )
        append_section_title(
            story,
            heading,
            styles["secao"],
            "historico_versoes",
            contexto_extra.get("section_anchor_map"),
        )
        append_section_prose_paragraph(
            story,
            styles,
            contexto_extra,
            "historico_versoes",
            "intro",
            PROSE_TEMPLATES.get("historico_versoes", {}).get("intro", ""),
            spacer_after=8,
        )

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
                Paragraph(pdf_paragraph_text(f"v{entrada['version_number']}"), styles['celula_centro']),
                Paragraph(pdf_paragraph_text(entrada['timestamp_str']), styles['celula_centro']),
                Paragraph(pdf_paragraph_text(entrada['responsible_name']), styles['celula']),
                Paragraph(pdf_paragraph_text(entrada['description']), styles['celula']),
            ])

        tabela = Table(linhas, colWidths=[45, 110, 140, 245])
        tabela.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), ReportTheme.COR_PRIMARIA),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F4F7")]),
            ('GRID', (0, 0), (-1, -1), 0.5, ReportTheme.COR_LINHA),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))

        _, height = tabela.wrap(_HISTORY_TABLE_WIDTH, 100_000)
        if height > _MAX_HISTORY_TABLE_HEIGHT:
            story.append(
                KeepInFrame(
                    _HISTORY_TABLE_WIDTH,
                    _MAX_HISTORY_TABLE_HEIGHT,
                    [tabela],
                    mode="shrink",
                    hAlign="LEFT",
                )
            )
        else:
            story.append(tabela)
        story.append(Spacer(1, 10))
