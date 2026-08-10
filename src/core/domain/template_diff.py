"""Comparação de layout do documento vs template salvo."""
from __future__ import annotations

import json
from typing import Any

from src.core.domain.parsed_overrides import get_dto_scalar, get_itens_medicao_as_dicts, is_itens_overridden
from src.core.domain.ports import ReportDocument, TemplateRepository


def serialize_layout_snapshot(document: ReportDocument) -> dict[str, Any]:
    """Snapshot de layout (prosa, ordem) — exclui dados de medição."""
    section_overrides: dict[str, Any] = {}
    for section_id, overrides in document.section_overrides.items():
        serializable = {
            k: v for k, v in overrides.items()
            if isinstance(v, (str, int, float, bool, list, dict))
        }
        if serializable:
            section_overrides[section_id] = serializable
    return {
        "section_overrides": section_overrides,
        "section_order": document.section_order,
        "deleted_section_ids": list(document.deleted_section_ids),
        "custom_sections": list(document.custom_sections),
    }


def normalize_snapshot(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, ensure_ascii=False)


def is_layout_dirty_vs_template(
    document: ReportDocument,
    template_repo: TemplateRepository | None,
) -> bool:
    if template_repo is None:
        return bool(document.section_overrides or document.section_order)
    saved = template_repo.get_content_defaults(document.template_id)
    baseline = {
        "section_overrides": saved or {},
        "section_order": None,
        "deleted_section_ids": [],
        "custom_sections": [],
    }
    current = serialize_layout_snapshot(document)
    return normalize_snapshot(current) != normalize_snapshot(baseline)


def is_data_dirty(document: ReportDocument) -> bool:
    """Dados de medição alterados em relação ao PDF de origem (não layout/prosa)."""
    raw = document.raw_parsed_data

    scalar = document.parsed_overrides.get("scalar", {})
    for key, value in scalar.items():
        if str(value) != get_dto_scalar(raw, key):
            return True

    if is_itens_overridden(document.parsed_overrides):
        current = document.parsed_overrides.get("itens_medicao")
        baseline = get_itens_medicao_as_dicts(raw)
        if current != baseline:
            return True

    if any(img.annotations for img in document.images):
        return True

    if any(img.crop is not None for img in document.images):
        return True

    return False
