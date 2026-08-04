"""Re-export do registro de campos via camada application."""
from src.core.application.document_editing import (
    default_prose_values,
    get_edit_fields,
    get_global_fields_for_section,
    get_media_blocks,
    merge_section_prose,
    section_has_overrides,
)
from src.core.domain.report_field_registry import (
    GLOBAL_FIELDS,
    MEDICAO_COLUMNS,
    PROSE_TEMPLATES,
    GlobalFieldDef,
    SectionFieldDef,
    SectionMediaDef,
    is_field_overridden,
)

default_field_values = default_prose_values

__all__ = [
    "GLOBAL_FIELDS",
    "MEDICAO_COLUMNS",
    "PROSE_TEMPLATES",
    "GlobalFieldDef",
    "SectionFieldDef",
    "SectionMediaDef",
    "default_field_values",
    "default_prose_values",
    "get_edit_fields",
    "get_global_fields_for_section",
    "get_media_blocks",
    "is_field_overridden",
    "merge_section_prose",
    "section_has_overrides",
]
