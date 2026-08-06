"""Shim de compatibilidade — use os módulos focados diretamente quando possível."""
from src.core.domain.field_definitions import (
    GLOBAL_FIELDS,
    MEDICAO_COLUMNS,
    GlobalFieldDef,
    SectionFieldDef,
    SectionMediaDef,
    effective_media_kinds,
    get_edit_fields,
    get_global_fields_for_section,
    get_media_blocks,
)
from src.core.domain.override_helpers import (
    default_prose_values,
    is_field_overridden,
    merge_section_prose,
    section_has_overrides,
)
from src.core.domain.prose_templates import (
    INTRODUCAO_BODY_TITLE_KEYS,
    INTRODUCAO_CONTENT_BLOCKS,
    INTRODUCAO_HEADER_ONLY_BLOCKS,
    PROSE_TEMPLATES,
    IntroducaoBlockDef,
)

__all__ = [
    "GLOBAL_FIELDS",
    "INTRODUCAO_BODY_TITLE_KEYS",
    "INTRODUCAO_CONTENT_BLOCKS",
    "INTRODUCAO_HEADER_ONLY_BLOCKS",
    "MEDICAO_COLUMNS",
    "PROSE_TEMPLATES",
    "GlobalFieldDef",
    "IntroducaoBlockDef",
    "SectionFieldDef",
    "SectionMediaDef",
    "default_prose_values",
    "effective_media_kinds",
    "get_edit_fields",
    "get_global_fields_for_section",
    "get_media_blocks",
    "is_field_overridden",
    "merge_section_prose",
    "section_has_overrides",
]
