"""Seção personalizada inserida pelo workspace."""
from reportlab.platypus import Paragraph, Spacer

from .base import anchored_section_title


class CustomSection:
    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}

    def render(self, story, styles, dados_parseados, contexto_extra) -> None:
        section_id = self.config.get("section_id", "custom")
        prose = (contexto_extra.get("section_prose") or {}).get(section_id, {})
        title = prose.get("section_title") or prose.get("title") or "Seção personalizada"
        body = prose.get("body") or prose.get("subtitle") or ""
        story.append(anchored_section_title(
            title.upper(),
            styles["secao"],
            section_id,
            contexto_extra.get("section_anchor_map"),
        ))
        if body.strip():
            story.append(Paragraph(body, styles["corpo"]))
        story.append(Spacer(1, 12))
