"""Testes do mapeamento clique → seção na preview."""
from __future__ import annotations

from src.ui.shared.report_editor.preview_hit_tester import (
    anchor_widget_rect,
    click_to_pdf_point,
    hit_test_at_click,
    hit_test_section_at_point,
)


def test_click_to_pdf_point_maps_top_left() -> None:
    page_height = 792.0
    zoom = 1.6
    pixmap_w = int(612 * zoom)
    pixmap_h = int(page_height * zoom)
    point = click_to_pdf_point(
        10,
        10,
        label_width=pixmap_w,
        label_height=pixmap_h,
        pixmap_width=pixmap_w,
        pixmap_height=pixmap_h,
        page_height_pts=page_height,
        zoom=zoom,
    )
    assert point is not None
    pdf_x, pdf_y = point
    assert abs(pdf_x - 10 / zoom) < 0.01
    assert abs(pdf_y - (page_height - 10 / zoom)) < 0.01


def test_hit_test_section_at_point_finds_title() -> None:
    anchor_map = {
        "introducao": {
            "page_start": 2,
            "anchor_rect": {"page": 2, "x": 72, "y": 700, "width": 200, "height": 18},
        }
    }
    section_id = hit_test_section_at_point(2, 100, 710, anchor_map)
    assert section_id == "introducao"


def test_hit_test_at_click_returns_preview_hit() -> None:
    page_height = 792.0
    zoom = 1.6
    pixmap_w = int(612 * zoom)
    pixmap_h = int(page_height * zoom)
    anchor_map = {
        "grafica": {
            "page_start": 1,
            "anchor_rect": {"page": 1, "x": 72, "y": 650, "width": 180, "height": 16},
        }
    }
    top_y = (page_height - 650 - 16) * zoom + 8
    hit = hit_test_at_click(
        1,
        100,
        top_y,
        label_width=pixmap_w,
        label_height=pixmap_h,
        pixmap_width=pixmap_w,
        pixmap_height=pixmap_h,
        page_height_pts=page_height,
        zoom=zoom,
        anchor_map=anchor_map,
    )
    assert hit is not None
    assert hit.section_id == "grafica"
    assert hit.page_number == 1
    assert hit.field_key == "section_title"


def test_anchor_widget_rect_matches_pdf_bounds() -> None:
    page_height = 792.0
    zoom = 1.0
    rect = {"x": 72, "y": 700, "width": 200, "height": 18}
    x, y, w, h = anchor_widget_rect(
        rect,
        page_height_pts=page_height,
        zoom=zoom,
        label_width=612,
        label_height=792,
        pixmap_width=612,
        pixmap_height=792,
    )
    assert x == 68
    assert y == 70
    assert w == 208
    assert h == 26
