"""Regras de ordenação do sumário de seções."""
from __future__ import annotations

from src.core.domain.section_schema import FIXED_SECTION_IDS


def is_sidebar_section_draggable(section_id: str) -> bool:
    return section_id not in FIXED_SECTION_IDS


def validate_sidebar_order(ordered_ids: list[str]) -> tuple[bool, str]:
    if not ordered_ids:
        return True, ""

    if "anexos" in ordered_ids:
        anex_idx = ordered_ids.index("anexos")
        if anex_idx != len(ordered_ids) - 1:
            return False, "Anexos permanecem por último no relatório."

    return True, ""
