"""Utilitários de numeração dinâmica de seções no PDF."""
from __future__ import annotations

import re

from src.core.domain.table_row_registry import NUMBERED_SECTION_IDS

_NUMBER_PREFIX_RE = re.compile(r"^\d+\.\s*")


def strip_number_prefix(text: str) -> str:
    return _NUMBER_PREFIX_RE.sub("", (text or "").strip())


def build_section_number_map(template_blocks: list[dict]) -> dict[str, int]:
    numbers: dict[str, int] = {}
    counter = 1
    for bloco in template_blocks:
        section_id = bloco.get("tipo", "")
        if section_id in NUMBERED_SECTION_IDS:
            numbers[section_id] = counter
            counter += 1
    return numbers


def format_numbered_heading(section_id: str, heading: str, number_map: dict[str, int]) -> str:
    if section_id not in NUMBERED_SECTION_IDS:
        return heading
    number = number_map.get(section_id)
    if not number:
        return heading
    base = strip_number_prefix(heading)
    return f"{number}. {base}"
