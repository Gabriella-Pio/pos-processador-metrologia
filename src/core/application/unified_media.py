"""Mídia do relatório unificado (PDF único) — store no ProjectSession."""
from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path

from src.core.domain.image_workspace import new_image_id
from src.core.domain.ports import ReportDocument, ReportImage
from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession


def copy_report_image(image: ReportImage) -> ReportImage:
    return replace(
        image,
        annotations=list(image.annotations),
        crop=image.crop,
    )


def unified_images_storage_dir(session: ProjectSession) -> Path:
    """Pasta persistente para fotos do PDF unificado."""
    if session.project_id:
        base = Path("output_pdfs") / "projects" / session.project_id
    elif session.documents:
        first = session.documents[0].source_pdf_path
        base = first.parent if first and str(first).strip() else Path("output_pdfs") / "workspace"
    else:
        base = Path("output_pdfs") / "workspace"
    dest = base / ".pos-metrologia" / "unified-photos"
    dest.mkdir(parents=True, exist_ok=True)
    return dest


def add_unified_image(
    session: ProjectSession,
    image_path: Path,
    section_id: str,
    *,
    bosello_import: bool = False,
) -> ReportImage:
    src = Path(image_path)
    image_id = new_image_id()
    stored_path = src
    if src.is_file():
        dest = unified_images_storage_dir(session) / f"{image_id}{src.suffix.lower() or '.png'}"
        shutil.copy2(src, dest)
        stored_path = dest
    image = ReportImage(
        image_path=stored_path,
        section_id=section_id,
        image_id=image_id,
        bosello_import=bosello_import,
    )
    session.unified_images.append(image)
    return image


def remove_unified_image(session: ProjectSession, image: ReportImage) -> None:
    session.unified_images = [
        img
        for img in session.unified_images
        if not (
            img.section_id == image.section_id
            and str(img.image_path) == str(image.image_path)
            and (img.image_id or "") == (image.image_id or "")
        )
    ]


def update_unified_image_caption(
    session: ProjectSession,
    image: ReportImage,
    caption: str,
) -> None:
    for img in session.unified_images:
        if (
            img.section_id == image.section_id
            and str(img.image_path) == str(image.image_path)
            and (not image.image_id or img.image_id == image.image_id)
        ):
            img.caption = caption
            break


def collect_layout_images_from_slots(
    slots: list[ProjectDocumentSlot],
    *,
    layout: dict[str, dict],
) -> list[ReportImage]:
    """Fotos das peças para seções ativas do layout unificado."""
    allowed = {
        section_id
        for section_id, cfg in layout.items()
        if cfg.get("enabled", True) and not str(section_id).startswith("_")
    }
    collected: list[ReportImage] = []
    seen: set[tuple[str, str]] = set()
    for slot in slots:
        document = slot.document
        if document is None:
            continue
        for image in document.images:
            if image.bosello_import:
                continue
            if image.section_id not in allowed:
                continue
            key = (str(image.image_path), image.section_id)
            if key in seen:
                continue
            seen.add(key)
            collected.append(copy_report_image(image))
    return collected


def filter_unified_images_for_layout(
    session: ProjectSession,
    *,
    layout: dict[str, dict],
) -> list[ReportImage]:
    allowed = {
        section_id
        for section_id, cfg in layout.items()
        if cfg.get("enabled", True) and not str(section_id).startswith("_")
    }
    return [
        copy_report_image(image)
        for image in session.unified_images
        if image.section_id in allowed
    ]


def resolve_unified_layout_images(
    session: ProjectSession,
    slots: list[ProjectDocumentSlot],
    *,
    layout: dict[str, dict],
) -> list[ReportImage]:
    """Prefere ``session.unified_images``; senão agrega fotos das peças."""
    if session.unified_images:
        return filter_unified_images_for_layout(session, layout=layout)
    return collect_layout_images_from_slots(slots, layout=layout)


def seed_unified_images_from_pieces(session: ProjectSession) -> bool:
    """Copia fotos das peças para o store unificado (só se ainda estiver vazio)."""
    if session.unified_images:
        return False
    seen: set[tuple[str, str]] = set()
    seeded: list[ReportImage] = []
    for slot in session.documents:
        document = slot.document
        if document is None:
            continue
        for image in document.images:
            key = (str(image.image_path), image.section_id)
            if key in seen:
                continue
            seen.add(key)
            seeded.append(copy_report_image(image))
    if not seeded:
        return False
    session.unified_images = seeded
    return True


def storage_document_for_unified(session: ProjectSession) -> ReportDocument | None:
    """Documento de referência para paths/workspace (primeira peça parseada)."""
    for slot in session.documents:
        if slot.document is not None:
            return slot.document
    return None
