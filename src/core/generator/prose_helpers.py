"""Helpers para leitura de prosa editável no generator."""
from __future__ import annotations

from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Spacer

from src.core.domain.placeholder_utils import resolve_placeholders
from src.core.domain.section_numbering import format_numbered_heading, strip_number_prefix
from .constants import ReportTheme


def get_section_prose(contexto_extra: dict, section_id: str, key: str, default: str = "") -> str:
    prose = contexto_extra.get("section_prose", {}).get(section_id, {})
    value = prose.get(key)
    if value is not None and str(value).strip():
        raw = str(value)
    else:
        raw = default
    ctx = contexto_extra.get("placeholder_context", {})
    return resolve_placeholders(raw, ctx)


def get_section_heading(contexto_extra: dict, section_id: str, default: str) -> str:
    prose = contexto_extra.get("section_prose", {}).get(section_id, {})
    default_base = strip_number_prefix(default)
    stored = prose.get("section_title")
    if stored is not None and str(stored).strip():
        raw = str(stored)
    else:
        raw = default_base
    ctx = contexto_extra.get("placeholder_context", {})
    resolved = resolve_placeholders(raw, ctx)
    number_map = contexto_extra.get("section_number_map", {})
    return format_numbered_heading(section_id, resolved, number_map)


def append_section_footer_note(story, styles, section_id: str, contexto_extra: dict) -> None:
    """Nota de rodapé editável — comum a todas as seções."""
    prose = contexto_extra.get("section_prose", {}).get(section_id, {}) or {}
    if section_id == "introducao":
        fallback = str(
            prose.get("nota")
            or prose.get("intro")
            or prose.get("nota_deteccao")
            or ""
        )
    else:
        fallback = str(prose.get("nota") or "")
    note = get_section_prose(contexto_extra, section_id, "nota", fallback)
    if not str(note or "").strip() and section_id == "introducao":
        note = get_section_prose(contexto_extra, section_id, "intro", fallback)
    if not str(note or "").strip():
        return
    estilo = ParagraphStyle(
        f"SectionNota_{section_id}",
        parent=styles["texto"],
        fontSize=8,
        textColor=ReportTheme.COR_SECUNDARIA,
        leading=11,
    )
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"<i>{note}</i>", estilo))
    story.append(Spacer(1, 6))
