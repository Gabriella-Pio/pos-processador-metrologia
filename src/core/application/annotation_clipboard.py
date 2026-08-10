"""Clipboard em memória para copiar marcações entre fotos."""
from __future__ import annotations

from dataclasses import dataclass, replace

from src.core.domain.ports import Annotation, ImageCrop


@dataclass
class AnnotationClipboardPayload:
    annotations: list[Annotation]
    crop: ImageCrop | None = None


_CLIPBOARD: AnnotationClipboardPayload | None = None


def clone_annotations(annotations: list[Annotation]) -> list[Annotation]:
    return [replace(item) for item in annotations]


def clone_crop(crop: ImageCrop | None) -> ImageCrop | None:
    if crop is None:
        return None
    return replace(crop)


def copy_from_image(annotations: list[Annotation], crop: ImageCrop | None) -> None:
    global _CLIPBOARD
    _CLIPBOARD = AnnotationClipboardPayload(
        annotations=clone_annotations(annotations),
        crop=clone_crop(crop),
    )


def has_clipboard() -> bool:
    return _CLIPBOARD is not None and bool(_CLIPBOARD.annotations or _CLIPBOARD.crop is not None)


def take_clipboard_copy() -> AnnotationClipboardPayload | None:
    if _CLIPBOARD is None:
        return None
    return AnnotationClipboardPayload(
        annotations=clone_annotations(_CLIPBOARD.annotations),
        crop=clone_crop(_CLIPBOARD.crop),
    )
