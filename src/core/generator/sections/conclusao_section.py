from reportlab.platypus import Paragraph

from .base import BaseSection, append_section_title
from ..prose_helpers import format_prose_paragraph, get_section_prose, get_section_heading
from src.core.domain.report_field_registry import PROSE_TEMPLATES
from src.core.domain.table_row_registry import SECTION_HEADING_DEFAULTS


class ConclusaoSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        heading = get_section_heading(
            contexto_extra, "conclusao", SECTION_HEADING_DEFAULTS["conclusao"],
        )
        append_section_title(
            story, heading, styles["secao"], "conclusao", contexto_extra.get("section_anchor_map"),
        )
        items = getattr(dados_parseados, "itens_medicao", []) or []
        if getattr(dados_parseados, "series", None) is not None:
            total_fora = sum(getattr(s, "fora_count", 0) for s in dados_parseados.series)
        else:
            total_fora = sum(
                1 for i in items if str(getattr(i, "status", "")).lower() == "fora"
            )

        # Preferência: campo único `texto` (editor / estatístico).
        conclusao_texto = get_section_prose(contexto_extra, "conclusao", "texto", "")
        if not conclusao_texto:
            conclusao_texto = str(self.config.get("texto_personalizado") or "")
        if not conclusao_texto:
            # Templates mistos/tomo: texto_aprovado / texto_reprovado no section_prose.
            tmpl = PROSE_TEMPLATES.get("conclusao", {})
            if total_fora > 0:
                conclusao_texto = get_section_prose(
                    contexto_extra,
                    "conclusao",
                    "texto_reprovado",
                    tmpl.get("texto_reprovado", ""),
                )
            else:
                conclusao_texto = get_section_prose(
                    contexto_extra,
                    "conclusao",
                    "texto_aprovado",
                    tmpl.get("texto_aprovado", ""),
                )

        story.append(Paragraph(format_prose_paragraph(conclusao_texto), styles["texto"]))
        # Assinatura (linha + rótulo) é anexada pelo engine após todas as seções
        # de conteúdo e antes dos anexos — ver ``append_approval_signature``.
