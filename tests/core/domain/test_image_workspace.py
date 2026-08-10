"""Testes de serialização e utilitários de imagens no workspace."""
from __future__ import annotations

from pathlib import Path

from src.core.domain.image_workspace import (
    deserialize_report_image,
    format_number_marker_legend,
    image_matches_reference,
    lookup_foto_edits,
    serialize_report_image,
)
from src.core.domain.ports import Annotation, ImageCrop, ReportImage


def test_lookup_foto_edits_resolves_absolute_and_relative_paths(tmp_path: Path) -> None:
    rel = tmp_path / "foto.png"
    rel.touch()
    edits = {str(rel.resolve()): {"annotations": [{"kind": "arrow", "x": 0.1, "y": 0.1}]}}
    found = lookup_foto_edits(edits, str(rel))
    assert found.get("annotations")


def test_lookup_foto_edits_resolves_by_image_id() -> None:
    edits = {"img123": {"image_id": "img123", "annotations": [{"kind": "arrow", "x": 0.1, "y": 0.1}]}}
    found = lookup_foto_edits(edits, "/any/path.png")
    assert not found
    found = lookup_foto_edits(edits, "img123")
    assert found.get("annotations")


def test_image_matches_reference_by_path_and_id(tmp_path: Path) -> None:
    rel = tmp_path / "foto.png"
    rel.touch()
    image = ReportImage(
        image_path=rel,
        section_id="introducao",
        image_id="img123",
    )
    assert image_matches_reference(image, path=str(rel.resolve()))
    assert image_matches_reference(image, path=str(rel))
    assert image_matches_reference(image, path="/other/dir/foto.png")
    assert image_matches_reference(image, image_id="img123")
    assert not image_matches_reference(image, path="/other/dir/outra.png")


def test_format_number_marker_legend() -> None:
    legend = format_number_marker_legend(
        [
            {"kind": "number", "text": "2", "legend": "poro"},
            {"kind": "number", "text": "1", "legend": "fissura"},
        ]
    )
    assert legend == "1 — fissura; 2 — poro"


def test_serialize_round_trip_report_image_with_edits() -> None:
    image = ReportImage(
        image_path=Path("/tmp/foto.png"),
        section_id="tomografia",
        image_id="img123",
        caption="Vista frontal",
        bosello_import=True,
        crop=ImageCrop(x=0.1, y=0.2, width=0.5, height=0.4),
        annotations=[
            Annotation(kind="arrow", x=0.2, y=0.3, width=0.1, height=0.05, color="#ff0000"),
        ],
    )
    raw = serialize_report_image(image)
    restored = deserialize_report_image(raw)
    assert restored is not None
    assert restored.image_id == "img123"
    assert restored.crop is not None
    assert restored.crop.width == 0.5
    assert len(restored.annotations) == 1
    assert restored.annotations[0].kind == "arrow"
