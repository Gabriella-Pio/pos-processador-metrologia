"""Codec compartilhado do estado editável de um ``ReportDocument``."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.domain.image_workspace import deserialize_report_image, serialize_report_image
from src.core.domain.ports import ReportDocument


def serialize_document_workspace(document: ReportDocument) -> dict[str, Any]:
    return {
        "template_id": document.template_id,
        "section_overrides": document.section_overrides,
        "parsed_overrides": document.parsed_overrides,
        "section_order": document.section_order,
        "images": [serialize_report_image(img) for img in document.images],
        "bosello_captured_paths": [str(path) for path in document.bosello_captured_paths],
        "custom_sections": document.custom_sections,
        "deleted_section_ids": document.deleted_section_ids,
        "extra_section_ids": list(getattr(document, "extra_section_ids", None) or []),
        "attachment_pdf_paths": [str(path) for path in document.attachment_pdf_paths],
    }


def apply_workspace_to_document(document: ReportDocument, workspace: dict[str, Any]) -> None:
    document.template_id = workspace.get("template_id") or document.template_id
    document.section_overrides = dict(workspace.get("section_overrides") or {})
    document.parsed_overrides = dict(workspace.get("parsed_overrides") or {})
    order_raw = workspace.get("section_order")
    document.section_order = list(order_raw) if order_raw else None
    images_raw = workspace.get("images") or []
    document.images = [
        image
        for item in images_raw
        if isinstance(item, dict) and (image := deserialize_report_image(item)) is not None
    ]
    document.custom_sections = list(workspace.get("custom_sections") or [])
    document.deleted_section_ids = list(workspace.get("deleted_section_ids") or [])
    document.extra_section_ids = list(workspace.get("extra_section_ids") or [])
    attachment_raw = workspace.get("attachment_pdf_paths") or []
    document.attachment_pdf_paths = [Path(path) for path in attachment_raw if path]
    bosello_raw = workspace.get("bosello_captured_paths") or []
    document.bosello_captured_paths = [Path(path) for path in bosello_raw if path]
