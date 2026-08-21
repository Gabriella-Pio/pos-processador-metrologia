"""Helpers de merge e detecção de overrides de campos de seção."""
from __future__ import annotations

from src.core.domain.field_definitions import get_edit_fields
from src.core.domain.prose_templates import PROSE_TEMPLATES
from src.core.domain.table_row_specs import INTRODUCAO_BLOCK_TITLES


def default_prose_values(section_id: str, context: dict[str, str] | None = None) -> dict[str, str]:
    """Templates de prosa com placeholders — não resolve valores globais."""
    base = dict(PROSE_TEMPLATES.get(section_id, {}))
    kind = (context or {}).get("report_kind") or ""
    if kind in {"tomografia", "insp_ect"}:
        from src.core.domain.tomo_template_defaults import TOMO_PROSE_DEFAULTS

        base.update(TOMO_PROSE_DEFAULTS.get(section_id, {}))
    elif kind == "falha":
        from src.core.domain.falha_template_defaults import FALHA_PROSE_DEFAULTS

        base.update(FALHA_PROSE_DEFAULTS.get(section_id, {}))
    return base


def merge_section_prose(
    section_id: str,
    overrides: dict[str, str],
    context: dict[str, str] | None = None,
) -> dict[str, str]:
    defaults = default_prose_values(section_id, context)
    merged = {
        **defaults,
        **{
            k: v
            for k, v in overrides.items()
            if v is not None
            and not k.startswith("title_")
            and k not in {"section_title", "table_rows", "media_kinds"}
        },
    }
    return merged


def is_field_overridden(section_id: str, field_key: str, overrides: dict[str, dict]) -> bool:
    section_ov = overrides.get(section_id, {})
    if field_key not in section_ov:
        return False
    defaults = default_prose_values(section_id)
    return section_ov.get(field_key, "") != defaults.get(field_key, "")


def section_has_overrides(section_id: str, overrides: dict[str, dict]) -> bool:
    section_ov = overrides.get(section_id, {})
    if section_ov.get("section_title"):
        return True
    if section_ov.get("table_rows"):
        return True
    for key in INTRODUCAO_BLOCK_TITLES:
        if key in section_ov:
            return True
    for field_def in get_edit_fields(section_id):
        if field_def.editable and is_field_overridden(section_id, field_def.key, overrides):
            return True
    return bool(section_ov)
