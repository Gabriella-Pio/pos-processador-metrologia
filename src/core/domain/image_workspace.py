"""Serialização e utilitários de edição de imagens no workspace."""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from src.core.domain.ports import Annotation, ImageCrop, ReportDocument, ReportImage


def normalize_image_path(path: str | Path) -> str:
    """Chave estável para lookup de edições (resolve symlinks quando o arquivo existe)."""
    raw = Path(path)
    if raw.is_file():
        return str(raw.resolve())
    return str(raw)


def image_matches_reference(
    image: ReportImage,
    *,
    path: str = "",
    image_id: str = "",
) -> bool:
    """Compara foto do documento com path ou image_id vindos do preview/PDF."""
    if image_id and resolve_image_id(image) == image_id:
        return True
    if not path:
        return False
    stored = str(image.image_path)
    if stored == path:
        return True
    if normalize_image_path(stored) == normalize_image_path(path):
        return True
    return Path(stored).name == Path(path).name


def lookup_foto_edits(foto_edits: dict[str, dict] | None, path: str) -> dict:
    """Resolve edições da foto mesmo com path relativo/absoluto diferente."""
    if not foto_edits:
        return {}
    direct = foto_edits.get(path)
    if direct:
        return direct
    normalized = normalize_image_path(path)
    if normalized in foto_edits:
        return foto_edits[normalized]
    name = Path(path).name
    for key, value in foto_edits.items():
        if Path(key).name == name:
            return value
    return {}


def build_foto_edits_index(document: ReportDocument) -> dict[str, dict]:
    """Índice de edições por path normalizado, path original e image_id."""
    index: dict[str, dict] = {}
    for imagem in document.images:
        if not imagem.crop and not imagem.annotations:
            continue
        image_id = resolve_image_id(imagem)
        payload: dict[str, Any] = {"image_id": image_id}
        crop = serialize_crop(imagem.crop)
        if crop is not None:
            payload["crop"] = crop
        if imagem.annotations:
            payload["annotations"] = [serialize_annotation(item) for item in imagem.annotations]
        keys = {
            str(imagem.image_path),
            normalize_image_path(imagem.image_path),
            image_id,
        }
        for key in keys:
            if key:
                index[key] = payload
    return index


def format_number_marker_legend(annotations: list[dict[str, Any]] | None) -> str:
    """Monta legenda automática para marcadores numerados (ex.: ``1 — fissura; 2 — poro``)."""
    if not annotations:
        return ""
    lines: list[str] = []
    for raw in annotations:
        if not isinstance(raw, dict) or raw.get("kind") != "number":
            continue
        number = str(raw.get("text") or "").strip()
        legend = str(raw.get("legend") or "").strip()
        if number and legend:
            lines.append(f"{number} — {legend}")
    lines.sort(key=lambda item: int(item.split("—", 1)[0].strip()) if item.split("—", 1)[0].strip().isdigit() else item)
    return "; ".join(lines)


def new_image_id() -> str:
    return uuid.uuid4().hex[:12]


def resolve_image_id(image: ReportImage) -> str:
    if image.image_id:
        return image.image_id
    digest = uuid.uuid5(uuid.NAMESPACE_URL, str(image.image_path)).hex[:12]
    image.image_id = digest
    return digest


def serialize_annotation(annotation: Annotation) -> dict[str, Any]:
    return {
        "kind": annotation.kind,
        "x": annotation.x,
        "y": annotation.y,
        "width": annotation.width,
        "height": annotation.height,
        "text": annotation.text,
        "color": annotation.color,
        "legend": annotation.legend,
    }


def deserialize_annotation(raw: dict[str, Any]) -> Annotation | None:
    kind = str(raw.get("kind") or "").strip()
    if not kind:
        return None
    return Annotation(
        kind=kind,
        x=float(raw.get("x") or 0.0),
        y=float(raw.get("y") or 0.0),
        width=float(raw.get("width") or 0.0),
        height=float(raw.get("height") or 0.0),
        text=str(raw.get("text") or ""),
        color=str(raw.get("color") or "#E85D04"),
        legend=str(raw.get("legend") or ""),
    )


def serialize_crop(crop: ImageCrop | None) -> dict[str, float] | None:
    if crop is None:
        return None
    return {
        "x": crop.x,
        "y": crop.y,
        "width": crop.width,
        "height": crop.height,
    }


def deserialize_crop(raw: Any) -> ImageCrop | None:
    if not isinstance(raw, dict):
        return None
    width = float(raw.get("width") or 0.0)
    height = float(raw.get("height") or 0.0)
    if width <= 0 or height <= 0:
        return None
    return ImageCrop(
        x=float(raw.get("x") or 0.0),
        y=float(raw.get("y") or 0.0),
        width=width,
        height=height,
    )


def serialize_report_image(image: ReportImage) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "path": str(image.image_path),
        "section_id": image.section_id,
        "image_id": resolve_image_id(image),
        "caption": image.caption or "",
        "bosello_import": bool(image.bosello_import),
    }
    if image.annotations:
        payload["annotations"] = [serialize_annotation(item) for item in image.annotations]
    crop = serialize_crop(image.crop)
    if crop is not None:
        payload["crop"] = crop
    return payload


def deserialize_report_image(raw: dict[str, Any]) -> ReportImage | None:
    path_raw = raw.get("path")
    section_id = raw.get("section_id")
    if not path_raw or not section_id:
        return None
    annotations = [
        item
        for item in (
            deserialize_annotation(entry)
            for entry in (raw.get("annotations") or [])
            if isinstance(entry, dict)
        )
        if item is not None
    ]
    image_id = str(raw.get("image_id") or "").strip()
    if not image_id:
        image_id = uuid.uuid5(uuid.NAMESPACE_URL, str(path_raw)).hex[:12]
    return ReportImage(
        image_path=Path(path_raw),
        section_id=str(section_id),
        image_id=image_id,
        annotations=annotations,
        crop=deserialize_crop(raw.get("crop")),
        caption=str(raw.get("caption") or ""),
        bosello_import=bool(raw.get("bosello_import")),
    )


def image_edit_key(image: ReportImage) -> str:
    return resolve_image_id(image)


def workspace_images_dir(document: ReportDocument) -> Path:
    """Diretório persistente para fotos adicionadas manualmente no workspace."""
    if document.source_pdf_path and str(document.source_pdf_path).strip():
        base = document.source_pdf_path.parent
    else:
        base = Path.cwd() / "output_pdfs" / "workspace"
    dest = base / ".pos-metrologia" / "section-photos"
    dest.mkdir(parents=True, exist_ok=True)
    return dest
