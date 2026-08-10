"""Testes do compositor de crop e marcações."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from src.core.application.image_edit_compositor import render_edited_image
from src.core.domain.ports import Annotation, ImageCrop


def test_render_edited_image_applies_crop_and_arrow(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    Image.new("RGB", (200, 100), (255, 255, 255)).save(source)
    edited = render_edited_image(
        source,
        crop=ImageCrop(x=0.25, y=0.1, width=0.5, height=0.8),
        annotations=[Annotation(kind="arrow", x=0.1, y=0.2, width=0.3, height=0.2)],
    )
    assert edited is not None
    assert edited != source
    assert edited.is_file()
    with Image.open(edited) as img:
        assert img.size[0] == 100
        assert img.size[1] == 80


def test_render_edited_image_text_box_fills_large_area(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    Image.new("RGB", (1000, 800), (90, 90, 90)).save(source)
    edited = render_edited_image(
        source,
        annotations=[
            Annotation(kind="text_box", x=0.1, y=0.1, width=0.5, height=0.2, text="TESTE"),
        ],
    )
    assert edited is not None
    with Image.open(edited) as img:
        region = img.crop((90, 70, 620, 250)).convert("L")
        dark_pixels = sum(1 for value in region.get_flattened_data() if value < 120)
        assert dark_pixels > 80
