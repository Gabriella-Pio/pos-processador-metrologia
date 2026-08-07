"""Regras de ordenação do sumário de seções."""
from __future__ import annotations

from src.core.domain.section_schema import FIXED_SECTION_IDS

_TAIL_FIXED = ("historico_versoes", "anexos")


def is_sidebar_section_draggable(section_id: str) -> bool:
    return section_id not in FIXED_SECTION_IDS


def validate_sidebar_order(ordered_ids: list[str]) -> tuple[bool, str]:
    if not ordered_ids:
        return True, ""

    hist_idx = (
        ordered_ids.index("historico_versoes")
        if "historico_versoes" in ordered_ids
        else len(ordered_ids)
    )
    anex_idx = (
        ordered_ids.index("anexos")
        if "anexos" in ordered_ids
        else len(ordered_ids)
    )

    if "historico_versoes" in ordered_ids and "anexos" in ordered_ids and hist_idx > anex_idx:
        return False, "Histórico de versões permanece antes dos Anexos."

    if "anexos" in ordered_ids and anex_idx != len(ordered_ids) - 1:
        return False, "Anexos permanecem por último no relatório."

    for idx, section_id in enumerate(ordered_ids):
        if (
            section_id not in _TAIL_FIXED
            and "historico_versoes" in ordered_ids
            and idx > hist_idx
        ):
            return False, "Esta seção não pode ficar após o Histórico de versões."

    return True, ""
