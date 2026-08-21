from reportlab.platypus import Paragraph, Spacer

from .base import BaseSection
from ..prose_helpers import (
    append_anchored_section_title,
    append_section_prose_paragraph,
    format_prose_paragraph,
    get_section_prose,
)
from src.core.application.interpretacao_edit import iter_mmc_interpretacao_bullets
from src.core.domain.measurement_interpretation import format_item_bullet_html
from src.core.domain.report_field_registry import PROSE_TEMPLATES
from ..constants import ReportTheme


class InterpretacaoSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        append_anchored_section_title(story, styles, contexto_extra, "interpretacao")
        intro_default = PROSE_TEMPLATES.get("interpretacao", {}).get("intro", "")
        append_section_prose_paragraph(
            story, styles, contexto_extra, "interpretacao", "intro", intro_default, spacer_after=4,
        )

        report_kind = contexto_extra.get("report_kind") or getattr(dados_parseados, "source_kind", "")
        prose = contexto_extra.get("section_prose", {}).get("interpretacao", {})
        bullet_keys = sorted(
            (k for k in prose if k.startswith("bullet_") and str(prose.get(k) or "").strip()),
            key=lambda k: int(k.split("_", 1)[1]) if k.split("_", 1)[1].isdigit() else 999,
        )

        if report_kind == "estatistico":
            # Texto completo já veio no intro; não repetir em nota/rodapé.
            story.append(Spacer(1, 10))
            return

        if report_kind in {"tomografia", "insp_ect", "falha"}:
            keys = bullet_keys or [f"bullet_{i}" for i in range(1, 5)]
            for key in keys:
                bullet = get_section_prose(contexto_extra, "interpretacao", key, "")
                if bullet:
                    story.append(Paragraph(f"•  {format_prose_paragraph(bullet)}", styles["bullet"]))
            story.append(Spacer(1, 10))
            return

        items = list(getattr(dados_parseados, "itens_medicao", []) or [])
        if report_kind == "mixed":
            nota = get_section_prose(contexto_extra, "interpretacao", "nota", "")
            if nota:
                story.append(Paragraph(f"•  {format_prose_paragraph(nota)}", styles["bullet"]))

        resolved_prose = {
            key: get_section_prose(contexto_extra, "interpretacao", key, "")
            for key in set(prose) | {f"bullet_{i}" for i in range(1, len(items) + 1)}
            if str(key).startswith("bullet_")
        }
        alert_color = ReportTheme.COR_ALERTA.hexval()
        for kind, payload in iter_mmc_interpretacao_bullets(items, resolved_prose):
            if kind == "prose":
                story.append(Paragraph(f"•  {format_prose_paragraph(str(payload))}", styles["bullet"]))
            else:
                story.append(Paragraph(
                    format_item_bullet_html(payload, alert_color=alert_color),
                    styles["bullet"],
                ))

        story.append(Spacer(1, 10))
