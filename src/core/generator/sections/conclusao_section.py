from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import HRFlowable, Paragraph, Spacer

from .base import BaseSection, anchored_section_title
from ..prose_helpers import get_section_prose, get_section_heading
from src.core.domain.report_field_registry import PROSE_TEMPLATES
from src.core.domain.table_row_registry import SECTION_HEADING_DEFAULTS


class ConclusaoSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        heading = get_section_heading(
            contexto_extra, "conclusao", SECTION_HEADING_DEFAULTS["conclusao"],
        )
        story.append(
            anchored_section_title(
                heading, styles["secao"], "conclusao", contexto_extra.get("section_anchor_map")
            )
        )
        total_fora = sum(1 for i in dados_parseados.itens_medicao if i.status == "Fora")

        texto_customizado = get_section_prose(contexto_extra, "conclusao", "texto", "")
        if not texto_customizado:
            texto_customizado = self.config.get("texto_personalizado")
        if texto_customizado:
            conclusao_texto = texto_customizado
        else:
            tmpl = PROSE_TEMPLATES.get("conclusao", {})
            conclusao_texto = (
                tmpl.get("texto_reprovado", "") if total_fora > 0 else tmpl.get("texto_aprovado", "")
            )

        story.append(Paragraph(conclusao_texto, styles["texto"]))

        # Espaço + linha de assinatura + rótulo (gov.br aplica a assinatura depois).
        aprovacao = get_section_prose(
            contexto_extra,
            "conclusao",
            "aprovacao",
            PROSE_TEMPLATES.get("conclusao", {}).get("aprovacao", "Aprovação / Coordenação CEM"),
        )
        if aprovacao.strip():
            story.append(Spacer(1, 48))
            story.append(
                HRFlowable(
                    width="42%",
                    thickness=0.7,
                    color=colors.HexColor("#555555"),
                    spaceBefore=0,
                    spaceAfter=6,
                    hAlign="CENTER",
                )
            )
            estilo = ParagraphStyle(
                "AprovacaoCemLabel",
                parent=styles["texto"],
                alignment=1,
                fontSize=9,
                textColor=colors.HexColor("#333333"),
                spaceBefore=0,
                spaceAfter=4,
            )
            story.append(Paragraph(aprovacao, estilo))
