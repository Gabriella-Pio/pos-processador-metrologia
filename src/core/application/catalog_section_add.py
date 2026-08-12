"""Incluir seções do catálogo em um relatório além do template atual."""
from __future__ import annotations

from src.core.domain.ports import ReportDocument
from src.core.domain.section_schema import PROTECTED_SECTION_IDS, SECTION_TITLES


def add_catalog_section(document: ReportDocument, section_id: str) -> str | None:
    """Inclui ou reativa uma seção do catálogo neste relatório."""
    sid = (section_id or "").strip()
    if not sid or sid in PROTECTED_SECTION_IDS or sid not in SECTION_TITLES:
        return None
    if sid in document.deleted_section_ids:
        document.deleted_section_ids = [
            item for item in document.deleted_section_ids if item != sid
        ]
    extras = list(getattr(document, "extra_section_ids", None) or [])
    if sid not in extras:
        extras.append(sid)
        document.extra_section_ids = extras
    if document.section_order is not None and sid not in document.section_order:
        document.section_order = list(document.section_order) + [sid]
    return sid
