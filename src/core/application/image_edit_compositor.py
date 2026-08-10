"""Aplica crop e marcações em imagens para preview/PDF."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.core.domain.image_workspace import serialize_annotation, serialize_crop
from src.core.domain.ports import Annotation, ImageCrop

_CACHE_DIR = Path("output_pdfs/temp/edited")


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    raw = (color or "#E85D04").lstrip("#")
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    if len(raw) != 6:
        return (232, 93, 4)
    return tuple(int(raw[i : i + 2], 16) for i in (0, 2, 4))


def _pixel_rect(
    width: int,
    height: int,
    crop: ImageCrop | None,
) -> tuple[int, int, int, int]:
    if crop is None:
        return 0, 0, width, height
    left = int(_clamp01(crop.x) * width)
    top = int(_clamp01(crop.y) * height)
    right = int(_clamp01(crop.x + crop.width) * width)
    bottom = int(_clamp01(crop.y + crop.height) * height)
    if right <= left:
        right = min(width, left + 1)
    if bottom <= top:
        bottom = min(height, top + 1)
    return left, top, right, bottom


def _map_annotation_to_cropped(
    annotation: Annotation,
    crop: ImageCrop | None,
) -> Annotation | None:
    if crop is None:
        return annotation
    x0, y0 = crop.x, crop.y
    x1, y1 = crop.x + crop.width, crop.y + crop.height
    ax1 = annotation.x + max(annotation.width, 0.0)
    ay1 = annotation.y + max(annotation.height, 0.0)
    if ax1 < x0 or annotation.x > x1 or ay1 < y0 or annotation.y > y1:
        return None
    return Annotation(
        kind=annotation.kind,
        x=(annotation.x - x0) / crop.width,
        y=(annotation.y - y0) / crop.height,
        width=annotation.width / crop.width if annotation.width else 0.0,
        height=annotation.height / crop.height if annotation.height else 0.0,
        text=annotation.text,
        color=annotation.color,
    )


_FONT_SEARCH_DIRS = (
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/liberation",
    "/usr/share/fonts/truetype/freefont",
)


def _marker_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = (
        "DejaVuSans-Bold.ttf",
        "LiberationSans-Bold.ttf",
        "FreeSansBold.ttf",
        "Arial Bold.ttf",
        "arialbd.ttf",
        "Arial.ttf",
    )
    for directory in _FONT_SEARCH_DIRS:
        for name in names:
            candidate = Path(directory) / name
            if candidate.is_file():
                return ImageFont.truetype(str(candidate), size)
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _number_marker_radius(width: int, height: int) -> int:
    return max(12, min(width, height) // 30)


def _fit_text_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    box_w: int,
    box_h: int,
    padding: int,
) -> tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, int, int]:
    """Escala a fonte para preencher a caixa (mesma lógica visual do editor)."""
    inner_w = max(1, box_w - 2 * padding)
    inner_h = max(1, box_h - 2 * padding)
    target = max(12, int(min(inner_w, inner_h) * 0.72))
    for size in range(target, 9, -1):
        font = _marker_font(size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        if tw <= inner_w and th <= inner_h:
            return font, tw, th
    font = _marker_font(10)
    bbox = draw.textbbox((0, 0), text, font=font)
    return font, bbox[2] - bbox[0], bbox[3] - bbox[1]


def _draw_arrow(
    draw: ImageDraw.ImageDraw,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    color: tuple[int, int, int],
    *,
    width: int = 3,
) -> None:
    draw.line((x0, y0, x1, y1), fill=color, width=width)
    angle = math.atan2(y1 - y0, x1 - x0)
    head = max(10, width * 4)
    left = (
        x1 - head * math.cos(angle - math.pi / 6),
        y1 - head * math.sin(angle - math.pi / 6),
    )
    right = (
        x1 - head * math.cos(angle + math.pi / 6),
        y1 - head * math.sin(angle + math.pi / 6),
    )
    draw.polygon([(x1, y1), left, right], fill=color)


def _draw_annotations(
    draw: ImageDraw.ImageDraw,
    annotations: list[Annotation],
    width: int,
    height: int,
    crop: ImageCrop | None,
) -> None:
    for raw in annotations:
        mapped = _map_annotation_to_cropped(raw, crop)
        if mapped is None:
            continue
        color = _hex_to_rgb(mapped.color)
        x = int(_clamp01(mapped.x) * width)
        y = int(_clamp01(mapped.y) * height)
        w = int(abs(mapped.width) * width)
        h = int(abs(mapped.height) * height)

        if mapped.kind == "arrow":
            _draw_arrow(draw, x, y, x + w, y + h, color)
        elif mapped.kind == "circle":
            draw.ellipse((x, y, x + w, y + h), outline=color, width=3)
        elif mapped.kind == "text_box":
            text = mapped.text.strip() or "Texto"
            padding = max(6, int(min(w, h) * 0.08))
            box_w = max(w, 48)
            box_h = max(h, 24)
            draw.rectangle((x, y, x + box_w, y + box_h), fill=(255, 255, 255), outline=color, width=2)
            text_font, tw, th = _fit_text_font(draw, text, box_w, box_h, padding)
            text_x = x + (box_w - tw) // 2
            text_y = y + (box_h - th) // 2
            draw.text((text_x, text_y), text, fill=(26, 26, 26), font=text_font)
        elif mapped.kind == "number":
            label = mapped.text.strip() or "1"
            radius = _number_marker_radius(width, height)
            draw.ellipse(
                (x - radius, y - radius, x + radius, y + radius),
                fill=color,
                outline=color,
            )
            font = _marker_font(max(12, int(radius * 0.85)))
            tw, th = draw.textbbox((0, 0), label, font=font)[2:]
            draw.text((x - tw // 2, y - th // 2 - 1), label, fill=(255, 255, 255), font=font)


def render_edited_image(
    source_path: str | Path,
    *,
    crop: ImageCrop | None = None,
    annotations: list[Annotation] | None = None,
) -> Path | None:
    """Gera PNG temporário com crop e marcações aplicados."""
    path = Path(source_path)
    if not path.is_file():
        return None

    marks = list(annotations or [])
    if crop is None and not marks:
        return path

    try:
        with Image.open(path) as opened:
            base = opened.convert("RGBA")
    except OSError:
        return None

    width, height = base.size
    left, top, right, bottom = _pixel_rect(width, height, crop)
    cropped = base.crop((left, top, right, bottom))
    draw = ImageDraw.Draw(cropped)
    _draw_annotations(draw, marks, cropped.width, cropped.height, crop)

    digest = hashlib.md5(
        json.dumps(
            {
                "path": str(path.resolve()),
                "crop": serialize_crop(crop),
                "annotations": [serialize_annotation(item) for item in marks],
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8"),
        usedforsecurity=False,
    ).hexdigest()[:16]
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _CACHE_DIR / f"edit_{digest}.png"
    cropped.convert("RGB").save(out_path, "PNG")
    return out_path


def image_has_edits(
    *,
    crop: ImageCrop | None = None,
    annotations: list[Annotation] | None = None,
) -> bool:
    return crop is not None or bool(annotations)
