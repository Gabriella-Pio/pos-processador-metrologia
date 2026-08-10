"""Seção Anexos — lista os PDFs de origem e antecipa as páginas anexadas."""
from pathlib import Path

from reportlab.platypus import PageBreak, Paragraph, Spacer

from .base import BaseSection, anchored_section_title
from ..prose_helpers import format_prose_paragraph, get_section_heading, get_section_prose
from src.core.domain.report_field_registry import PROSE_TEMPLATES
from src.core.domain.table_row_registry import SECTION_HEADING_DEFAULTS


class AnexosSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        # Páginas dos PDFs de origem começam após a folha de sumário desta seção.
        story.append(PageBreak())
        heading = get_section_heading(
            contexto_extra,
            "anexos",
            SECTION_HEADING_DEFAULTS["anexos"],
        )
        story.append(
            anchored_section_title(
                heading,
                styles["secao"],
                "anexos",
                contexto_extra.get("section_anchor_map"),
            )
        )

        intro = get_section_prose(
            contexto_extra,
            "anexos",
            "intro",
            PROSE_TEMPLATES.get("anexos", {}).get("intro", ""),
        )
        if intro.strip():
            story.append(Paragraph(format_prose_paragraph(intro), styles["texto"]))
            story.append(Spacer(1, 8))

        anexos = list(contexto_extra.get("anexo_pdfs") or [])
        if not anexos:
            story.append(
                Paragraph(
                    "<i>Nenhum PDF de origem disponível para anexar.</i>",
                    styles["texto"],
                )
            )
            story.append(Spacer(1, 10))
            return

        story.append(Paragraph("<b>Arquivos anexados:</b>", styles["texto"]))
        story.append(Spacer(1, 4))
        for index, caminho in enumerate(anexos, start=1):
            nome = Path(str(caminho)).name
            story.append(Paragraph(f"{index}. {nome}", styles["texto"]))
        story.append(Spacer(1, 8))
        story.append(
            Paragraph(
                "<i>As páginas dos PDFs de origem seguem a partir da próxima página.</i>",
                styles["texto"],
            )
        )
        story.append(Spacer(1, 10))
