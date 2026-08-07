"""Casos de uso de edição de campos e overrides."""
from __future__ import annotations

from src.core.domain.field_definitions import GLOBAL_FIELDS
from src.core.domain.field_sync import sync_measured_by_to_operador, sync_operador_control_info
from src.core.domain.parsed_overrides import (
    build_effective_dto,
    extract_scalar_overrides,
    get_itens_medicao_as_dicts,
    is_scalar_overridden,
)
from src.core.domain.ports import ReportDocument
from src.core.domain.report_field_registry import (
    default_prose_values,
    get_edit_fields,
    get_global_fields_for_section,
    get_media_blocks,
    merge_section_prose,
    section_has_overrides,
)


def build_effective_document_dto(document: ReportDocument):
    return build_effective_dto(document.raw_parsed_data, document.parsed_overrides)


def get_measurement_rows(document: ReportDocument) -> list[dict[str, str]]:
    effective = build_effective_document_dto(document)
    return get_itens_medicao_as_dicts(effective)


def extract_global_field_values(document: ReportDocument) -> tuple[dict[str, str], set[str]]:
    effective = build_effective_document_dto(document)
    scalars = extract_scalar_overrides(document.raw_parsed_data, document.parsed_overrides)
    values = {
        **scalars,
        "client_project": document.client_project,
        "evaluated_component": document.evaluated_component,
    }
    overridden: set[str] = set()
    session_keys = {field.key for field in GLOBAL_FIELDS if field.source == "session"}
    for key in scalars:
        if key in session_keys:
            continue
        if is_scalar_overridden(key, document.parsed_overrides):
            overridden.add(key)
    return values, overridden


def sync_operador(document: ReportDocument, value: str) -> None:
    sync_operador_control_info(document, value)


def sync_measured_by(document: ReportDocument, measured_by: str) -> None:
    sync_measured_by_to_operador(document, measured_by)


__all__ = [
    "build_effective_document_dto",
    "default_prose_values",
    "extract_global_field_values",
    "get_edit_fields",
    "get_global_fields_for_section",
    "get_measurement_rows",
    "get_media_blocks",
    "merge_section_prose",
    "section_has_overrides",
    "sync_measured_by",
    "sync_operador",
]
