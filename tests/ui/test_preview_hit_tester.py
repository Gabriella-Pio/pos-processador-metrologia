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


def test_hit_test_at_click_prefers_photo_anchor() -> None:
    page_height = 792.0
    zoom = 1.6
    pixmap_w = int(612 * zoom)
    pixmap_h = int(page_height * zoom)
    anchor_map = {
        "tomografia": {
            "page_start": 1,
            "anchor_rect": {"page": 1, "x": 72, "y": 650, "width": 180, "height": 16},
        }
    }
    photo_anchors = [
        {
            "section_id": "tomografia",
            "image_path": "/tmp/foto.png",
            "image_id": "abc",
            "page": 1,
            "x": 72,
            "y": 400,
            "width": 200,
            "height": 120,
        }
    ]
    photo_top = (page_height - 400 - 120) * zoom + 20
    hit = hit_test_at_click(
        1,
        150,
        photo_top,
        label_width=pixmap_w,
        label_height=pixmap_h,
        pixmap_width=pixmap_w,
        pixmap_height=pixmap_h,
        page_height_pts=page_height,
        zoom=zoom,
        anchor_map=anchor_map,
        photo_anchors=photo_anchors,
    )
    assert hit is not None
    assert hit.section_id == "tomografia"
    assert hit.field_key == "photos"
    assert hit.image_path == "/tmp/foto.png"
    assert hit.image_id == "abc"


def test_anchor_widget_rect_matches_pdf_bounds() -> None:
    page_height = 792.0
    zoom = 1.0
    rect = {"x": 72, "y": 700, "width": 200, "height": 18}
    highlight = anchor_widget_rect(
        rect,
        page_height_pts=page_height,
        zoom=zoom,
        label_width=612,
        label_height=792,
        pixmap_width=612,
        pixmap_height=792,
    )
    assert highlight is not None
    x, y, w, h = highlight
    assert x == 68
    assert y == 70
    assert w == 208
    assert h == 26


def test_anchor_bounds_rejects_none_coordinates() -> None:
    from src.ui.shared.report_editor.preview_hit_tester import anchor_bounds

    assert anchor_bounds({"x": None, "y": 10, "width": 1, "height": 1}) is None
    assert anchor_bounds({"anchor_rect": {"x": None, "y": None, "width": None, "height": None}}) is None
    assert anchor_bounds({"x": 1, "y": 2, "width": 3, "height": 4}) == {
        "x": 1.0,
        "y": 2.0,
        "width": 3.0,
        "height": 4.0,
    }


def test_anchor_widget_rect_returns_none_for_invalid_rect() -> None:
    assert (
        anchor_widget_rect(
            {"x": None, "y": 1, "width": 2, "height": 3},
            page_height_pts=792.0,
            zoom=1.0,
            label_width=100,
            label_height=100,
            pixmap_width=100,
            pixmap_height=100,
        )
        is None
    )