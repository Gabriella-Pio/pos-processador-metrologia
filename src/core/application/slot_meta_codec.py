"""Codec de metadados de slot (PDF + componente + kind + template)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.domain.pdf_source import source_pdf_path_from_storage, source_pdf_path_to_storage
from src.core.domain.project_session import ProjectDocumentSlot
from src.core.domain.project_workspace import ProjectSlotSnapshot


def document_slot_to_meta(slot: ProjectDocumentSlot, *, storage_path: bool = True) -> dict[str, Any]:
    path = (
        source_pdf_path_to_storage(slot.source_pdf_path)
        if storage_path
        else str(slot.source_pdf_path)
    )
    return {
        "source_pdf_path": path,
        "evaluated_component": slot.evaluated_component,
        "source_kind": slot.source_kind,
        "template_id": slot.template_id,
    }


def document_slot_from_meta(
    item: dict[str, Any],
    *,
    storage_path: bool = True,
) -> ProjectDocumentSlot | None:
    if not isinstance(item, dict):
        return None
    path_raw = str(item.get("source_pdf_path") or "").strip()
    if storage_path:
        path = source_pdf_path_from_storage(path_raw)
    else:
        if not path_raw:
            return None
        path = Path(path_raw)
    return ProjectDocumentSlot(
        source_pdf_path=path,
        evaluated_component=str(item.get("evaluated_component") or "Componente"),
        source_kind=str(item.get("source_kind") or "calypso"),
        template_id=item.get("template_id"),
    )


def snapshot_slot_to_meta(slot: ProjectSlotSnapshot) -> dict[str, Any]:
    return {
        "source_pdf_path": source_pdf_path_to_storage(slot.source_pdf_path),
        "evaluated_component": slot.evaluated_component,
        "source_kind": slot.source_kind,
        "template_id": slot.template_id,
    }


def snapshot_slot_from_meta(item: dict[str, Any]) -> ProjectSlotSnapshot | None:
    if not isinstance(item, dict):
        return None
    path = str(item.get("source_pdf_path") or "").strip()
    return ProjectSlotSnapshot(
        source_pdf_path=path,
        evaluated_component=str(item.get("evaluated_component") or "Componente"),
        source_kind=str(item.get("source_kind") or "calypso"),
        template_id=item.get("template_id"),
    )
