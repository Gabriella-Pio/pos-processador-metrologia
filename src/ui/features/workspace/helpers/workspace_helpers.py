"""Helpers puros do workspace (sem Qt / signals)."""
from __future__ import annotations

from dataclasses import replace

from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession
from src.core.domain.ports import ReportDocument, ReportExporter, VersionEntry


def slot_progress_label(slot: ProjectDocumentSlot, index: int = 0) -> str:
    """Rótulo curto para overlay/progresso de parse."""
    if slot.source_pdf_path and slot.source_pdf_path.name:
        return slot.source_pdf_path.name
    if slot.evaluated_component:
        return slot.evaluated_component
    return f"arquivo {index + 1}"


def preview_error_summary(details: str, *, max_len: int = 240) -> str:
    lines = [line.strip() for line in details.strip().splitlines() if line.strip()]
    if not lines:
        return "Não foi possível determinar a causa do erro."
    message = lines[-1]
    if len(message) > max_len:
        return f"{message[: max_len - 3]}..."
    return message


def document_with_timeline(
    document: ReportDocument | None,
    timeline: list[VersionEntry],
) -> ReportDocument | None:
    if document is None:
        return None
    if not timeline or timeline == document.version_history:
        return document
    return replace(document, version_history=list(timeline))


def dimensional_document_for_edit(
    session: ProjectSession | None,
    active: ReportDocument | None,
    *,
    unified_editing: bool,
) -> ReportDocument | None:
    """Documento onde persistem medições dimensionais (peça CALYPSO base no unificado)."""
    if not unified_editing:
        return active
    if session is None:
        return active
    for slot in session.documents:
        doc = slot.document
        if doc is None:
            continue
        kind = slot.source_kind or doc.source_kind or "calypso"
        if kind == "calypso":
            return doc
    return active


def catalog_section_presence(
    document: ReportDocument,
    exporter: ReportExporter,
    session: ProjectSession | None,
    *,
    unified_editing: bool,
) -> tuple[set[str], set[str]]:
    """Retorna (present_ids, deleted_ids) para o seletor de catálogo."""
    try:
        present = {section["id"] for section in exporter.list_sections(document)}
    except Exception:
        present = set()
    present.update(
        sid for sid in (getattr(document, "extra_section_ids", None) or []) if sid
    )
    present.update(
        str(item.get("id"))
        for item in document.custom_sections
        if item.get("id")
    )
    if unified_editing and session is not None:
        present.update(session.unified_extra_section_ids)
        present.update(
            str(item.get("id"))
            for item in session.unified_custom_sections
            if item.get("id")
        )
        deleted = set(session.unified_deleted_section_ids)
    else:
        deleted = set(document.deleted_section_ids)
    return present, deleted


def version_status_text(
    *,
    viewing_version: int | None,
    editing_from_version: int | None,
    last_registered_version: int | None,
) -> str:
    if viewing_version is not None:
        return f"Visualizando versão v{viewing_version}"
    if editing_from_version is not None:
        return f"Editando a partir da v{editing_from_version}"
    if last_registered_version is not None:
        return f"Versão v{last_registered_version} registrada"
    return "Rascunho salvo"
