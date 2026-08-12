"""Mapeia cliques na preview rasterizada para seções do PDF via anchor_rect."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PreviewHit:
    section_id: str
    page_number: int
    field_key: str | None = None
    image_path: str | None = None
    image_id: str | None = None


def pixmap_display_offset(
    label_width: int,
    label_height: int,
    pixmap_width: int,
    pixmap_height: int,
) -> tuple[int, int]:
    return (
        max(0, (label_width - pixmap_width) // 2),
        max(0, (label_height - pixmap_height) // 2),
    )


def click_to_pdf_point(
    click_x: float,
    click_y: float,
    *,
    label_width: int,
    label_height: int,
    pixmap_width: int,
    pixmap_height: int,
    page_height_pts: float,
    zoom: float,
) -> tuple[float, float] | None:
    """Converte clique no QLabel para coordenadas PDF (origem inferior esquerda)."""
    offset_x, offset_y = pixmap_display_offset(
        label_width, label_height, pixmap_width, pixmap_height
    )
    pixmap_x = click_x - offset_x
    pixmap_y = click_y - offset_y
    if pixmap_x < 0 or pixmap_y < 0 or pixmap_x > pixmap_width or pixmap_y > pixmap_height:
        return None
    pdf_x = pixmap_x / zoom
    pdf_y = page_height_pts - (pixmap_y / zoom)
    return pdf_x, pdf_y


def _as_float(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def anchor_bounds(info: dict) -> dict | None:
    rect = info.get("anchor_rect") if isinstance(info.get("anchor_rect"), dict) else info
    if not isinstance(rect, dict):
        return None
    x = _as_float(rect.get("x"))
    y = _as_float(rect.get("y"))
    width = _as_float(rect.get("width"))
    height = _as_float(rect.get("height"))
    if None in (x, y, width, height):
        return None
    return {"x": x, "y": y, "width": width, "height": height, **{
        key: value for key, value in rect.items() if key not in {"x", "y", "width", "height"}
    }}


def anchor_page_number(info: dict, rect: dict) -> int | None:
    page = rect.get("page") or info.get("page_start") or info.get("page")
    if page is None:
        return None
    try:
        return int(page)
    except (TypeError, ValueError):
        return None


def point_in_anchor(
    pdf_x: float,
    pdf_y: float,
    rect: dict,
    *,
    padding_pts: float = 6.0,
) -> bool:
    x = _as_float(rect.get("x"))
    y = _as_float(rect.get("y"))
    width = _as_float(rect.get("width"))
    height = _as_float(rect.get("height"))
    if None in (x, y, width, height):
        return False
    x0 = x - padding_pts
    x1 = x + width + padding_pts
    y0 = y - padding_pts
    y1 = y + height + padding_pts
    return x0 <= pdf_x <= x1 and y0 <= pdf_y <= y1


def anchor_widget_rect(
    rect: dict,
    *,
    page_height_pts: float,
    zoom: float,
    label_width: int,
    label_height: int,
    pixmap_width: int,
    pixmap_height: int,
    padding_pts: float = 4.0,
) -> tuple[int, int, int, int] | None:
    """Retângulo (x, y, w, h) em coordenadas do QLabel para desenhar highlight."""
    x = _as_float(rect.get("x"))
    y = _as_float(rect.get("y"))
    width = _as_float(rect.get("width"))
    height = _as_float(rect.get("height"))
    if None in (x, y, width, height):
        return None
    offset_x, offset_y = pixmap_display_offset(
        label_width, label_height, pixmap_width, pixmap_height
    )
    left = (x - padding_pts) * zoom + offset_x
    top = (page_height_pts - y - height - padding_pts) * zoom
    widget_w = (width + padding_pts * 2) * zoom
    widget_h = (height + padding_pts * 2) * zoom
    return int(left), int(top + offset_y), max(1, int(widget_w)), max(1, int(widget_h))


def hit_test_section_at_point(
    page_number: int,
    pdf_x: float,
    pdf_y: float,
    anchor_map: dict[str, dict],
    *,
    padding_pts: float = 6.0,
) -> str | None:
    matches: list[tuple[float, str]] = []
    for section_id, info in anchor_map.items():
        rect = anchor_bounds(info or {})
        if rect is None:
            continue
        page = anchor_page_number(info or {}, rect)
        if page != page_number:
            continue
        if point_in_anchor(pdf_x, pdf_y, rect, padding_pts=padding_pts):
            area = float(rect["width"]) * float(rect["height"])
            matches.append((area, section_id))
    if not matches:
        return None
    matches.sort(key=lambda item: item[0])
    return matches[0][1]


def hit_test_photo_at_point(
    page_number: int,
    pdf_x: float,
    pdf_y: float,
    photo_anchors: list[dict],
    *,
    padding_pts: float = 2.0,
) -> dict | None:
    matches: list[tuple[float, dict]] = []
    for anchor in photo_anchors:
        if int(anchor.get("page") or 0) != page_number:
            continue
        bounds = anchor_bounds(anchor)
        if bounds is None:
            continue
        if point_in_anchor(pdf_x, pdf_y, bounds, padding_pts=padding_pts):
            area = float(bounds["width"]) * float(bounds["height"])
            matches.append((area, anchor))
    if not matches:
        return None
    matches.sort(key=lambda item: item[0])
    return matches[0][1]


def hit_test_at_click(
    page_number: int,
    click_x: float,
    click_y: float,
    *,
    label_width: int,
    label_height: int,
    pixmap_width: int,
    pixmap_height: int,
    page_height_pts: float,
    zoom: float,
    anchor_map: dict[str, dict],
    photo_anchors: list[dict] | None = None,
) -> PreviewHit | None:
    pdf_point = click_to_pdf_point(
        click_x,
        click_y,
        label_width=label_width,
        label_height=label_height,
        pixmap_width=pixmap_width,
        pixmap_height=pixmap_height,
        page_height_pts=page_height_pts,
        zoom=zoom,
    )
    if pdf_point is None:
        return None
    pdf_x, pdf_y = pdf_point

    photo_hit = hit_test_photo_at_point(
        page_number,
        pdf_x,
        pdf_y,
        photo_anchors or [],
    )
    if photo_hit is not None:
        return PreviewHit(
            section_id=str(photo_hit.get("section_id") or ""),
            page_number=page_number,
            field_key="photos",
            image_path=str(photo_hit.get("image_path") or "") or None,
            image_id=str(photo_hit.get("image_id") or "") or None,
        )

    section_id = hit_test_section_at_point(page_number, pdf_x, pdf_y, anchor_map)
    if section_id is not None:
        return PreviewHit(section_id=section_id, page_number=page_number, field_key="section_title")
    section_id = _fallback_section_for_page(page_number, pdf_y, anchor_map)
    if section_id is None:
        return None
    return PreviewHit(section_id=section_id, page_number=page_number, field_key="section_title")


def _fallback_section_for_page(
    page_number: int,
    pdf_y: float,
    anchor_map: dict[str, dict],
) -> str | None:
    """Quando o clique não acerta o título, usa a seção mais próxima acima do ponto."""
    candidates: list[tuple[float, str]] = []
    for section_id, info in anchor_map.items():
        rect = anchor_bounds(info or {})
        if rect is None:
            continue
        page = anchor_page_number(info or {}, rect)
        if page != page_number:
            continue
        title_top = float(rect["y"]) + float(rect["height"])
        if title_top <= pdf_y:
            candidates.append((pdf_y - title_top, section_id))
    if not candidates:
        for section_id, info in anchor_map.items():
            rect = anchor_bounds(info or {})
            if rect is None:
                continue
            if anchor_page_number(info or {}, rect) == page_number:
                return section_id
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]
