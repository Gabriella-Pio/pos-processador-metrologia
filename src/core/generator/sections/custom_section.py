"""Seção personalizada inserida pelo workspace."""
from reportlab.platypus import Paragraph, Spacer

from ..prose_helpers import append_section_footer_note, render_kv_table
from .base import anchored_section_title


class CustomSection:
    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}

    def render(self, story, styles, dados_parseados, contexto_extra) -> None:
        section_id = self.config.get("section_id", "custom")
        prose = (contexto_extra.get("section_prose") or {}).get(section_id, {})
        title = prose.get("section_title") or prose.get("title") or "Seção personalizada"
        body = (prose.get("body") or "").strip()
        story.append(anchored_section_title(
            title.upper(),
            styles["secao"],
            section_id,
            contexto_extra.get("section_anchor_map"),
        ))
        if body:
            story.append(Paragraph(body, styles["texto"]))
        table_rows = (contexto_extra.get("table_rows") or {}).get(section_id, [])
        if table_rows:
            ctx = contexto_extra.get("placeholder_context") or {}
            render_kv_table(story, styles, table_rows, ctx)
        append_section_footer_note(story, styles, section_id, contexto_extra)
        story.append(Spacer(1, 12))
