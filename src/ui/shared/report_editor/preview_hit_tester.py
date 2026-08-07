"""Mapeia cliques na preview rasterizada para seções do PDF via anchor_rect."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PreviewHit:
    section_id: str
    page_number: int
    field_key: str | None = None


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


def anchor_bounds(info: dict) -> dict | None:
    rect = info.get("anchor_rect") if isinstance(info.get("anchor_rect"), dict) else info
    if not isinstance(rect, dict):
        return None
    if not all(key in rect for key in ("x", "y", "width", "height")):
        return None
    return rect


def anchor_page_number(info: dict, rect: dict) -> int | None:
    page = rect.get("page") or info.get("page_start") or info.get("page")
    if page is None:
        return None
    return int(page)


def point_in_anchor(
    pdf_x: float,
    pdf_y: float,
    rect: dict,
    *,
    padding_pts: float = 6.0,
) -> bool:
    x0 = float(rect["x"]) - padding_pts
    x1 = float(rect["x"]) + float(rect["width"]) + padding_pts
    y0 = float(rect["y"]) - padding_pts
    y1 = float(rect["y"]) + float(rect["height"]) + padding_pts
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
) -> tuple[int, int, int, int]:
    """Retângulo (x, y, w, h) em coordenadas do QLabel para desenhar highlight."""
    offset_x, offset_y = pixmap_display_offset(
        label_width, label_height, pixmap_width, pixmap_height
    )
    x = (float(rect["x"]) - padding_pts) * zoom + offset_x
    top = (page_height_pts - float(rect["y"]) - float(rect["height"]) - padding_pts) * zoom
    width = (float(rect["width"]) + padding_pts * 2) * zoom
    height = (float(rect["height"]) + padding_pts * 2) * zoom
    return int(x), int(top + offset_y), max(1, int(width)), max(1, int(height))


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
