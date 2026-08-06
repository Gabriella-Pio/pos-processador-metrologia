from reportlab.platypus import Paragraph, Spacer

from .base import BaseSection
from ..prose_helpers import (
    append_anchored_section_title,
    append_section_prose_paragraph,
    get_section_prose,
)
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
        has_edited_bullets = bool(bullet_keys)

        if report_kind in {"tomografia", "insp_ect"} or has_edited_bullets:
            keys = bullet_keys or [f"bullet_{i}" for i in range(1, 5)]
            for key in keys:
                bullet = get_section_prose(contexto_extra, "interpretacao", key, "")
                if bullet:
                    story.append(Paragraph(f"•  {bullet}", styles["bullet"]))
            story.append(Spacer(1, 10))
            return

        alert_color = ReportTheme.COR_ALERTA.hexval()
        for item in dados_parseados.itens_medicao:
            story.append(Paragraph(
                format_item_bullet_html(item, alert_color=alert_color),
                styles["bullet"],
            ))

        story.append(Spacer(1, 10))
