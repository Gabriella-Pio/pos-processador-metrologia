"""Rótulos e tooltips das abas de documento do workspace."""
from __future__ import annotations

from src.core.application.piece_ordering import extract_piece_number_from_name
from src.core.domain.ports import ReportDocument
from src.core.domain.project_session import ProjectDocumentSlot


def document_tab_label(slot: ProjectDocumentSlot) -> str:
    """Rótulo da aba — número natural do arquivo quando existir."""
    number = extract_piece_number_from_name(slot.source_pdf_path.name)
    if number is not None:
        stem = f"Peça {number}"
    elif slot.source_pdf_path.name:
        stem = slot.source_pdf_path.stem[:20]
    else:
        stem = (slot.evaluated_component or "Relatório")[:20]
    kind = getattr(slot, "source_kind", "") or (
        slot.document.source_kind if slot.document else ""
    )
    badge = "Tomo" if kind == "insp_ect" else "MMC"
    return f"{stem} [{badge}]"


def document_tab_tooltip(slot: ProjectDocumentSlot) -> str:
    path = slot.source_pdf_path.resolve()
    kind = getattr(slot, "source_kind", "") or (
        slot.document.source_kind if slot.document else ""
    )
    lines = [path.name, str(path), f"Origem: {kind or 'desconhecida'}"]
    component = slot.evaluated_component.strip()
    if component and component != path.stem:
        lines.append(f"Componente avaliado: {component}")
    if slot.template_id:
        lines.append(f"Template: {slot.template_id}")
    return "\n".join(lines)


def document_header_label(document: ReportDocument, session) -> str:
    base = f"{document.client_project} — {document.evaluated_component}"
    if session is not None and len(session.documents) > 1:
        slot = session.documents[session.active_index]
        return f"{slot.source_pdf_path.name} · {base}"
    return base


