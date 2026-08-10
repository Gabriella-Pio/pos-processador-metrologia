"""Testes do clipboard de marcações entre fotos."""
from __future__ import annotations

from src.core.application.annotation_clipboard import (
    copy_from_image,
    has_clipboard,
    take_clipboard_copy,
)
from src.core.domain.ports import Annotation, ImageCrop


def test_copy_and_paste_roundtrip() -> None:
    annotations = [
        Annotation(kind="arrow", x=0.1, y=0.2, width=0.2, height=0.2, text=""),
        Annotation(kind="number", x=0.5, y=0.5, width=0.0, height=0.0, text="1", legend="Defeito"),
    ]
    crop = ImageCrop(x=0.05, y=0.05, width=0.9, height=0.9)
    copy_from_image(annotations, crop)

    assert has_clipboard()
    payload = take_clipboard_copy()
    assert payload is not None
    assert len(payload.annotations) == 2
    assert payload.annotations[0].kind == "arrow"
    assert payload.annotations[1].legend == "Defeito"
    assert payload.crop is not None
    assert payload.crop.width == 0.9

    # Clones — mutar cópia não altera clipboard original.
    payload.annotations[0].x = 0.99
    second = take_clipboard_copy()
    assert second is not None
    assert second.annotations[0].x == 0.1


def test_empty_clipboard() -> None:
    copy_from_image([], None)
    assert not has_clipboard()
