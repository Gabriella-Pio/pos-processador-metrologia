"""Testes de baseline de mídia do template."""
from __future__ import annotations

from pathlib import Path

from src.core.application.template_media import (
    locked_workspace_media_kinds,
    merge_workspace_media_kinds,
    sanitize_workspace_media_kinds,
    template_baseline_media_kinds,
)
from src.core.domain.ports import ReportDocument
from src.core.infrastructure.template_repository import JSONTemplateRepository


def test_template_baseline_uses_content_defaults(tmp_path) -> None:
    repo = JSONTemplateRepository(str(tmp_path / "templates.json"))
    repo.save_content_defaults(
        "default",
        {
            "identificacao": {"media_kinds": ["tables", "photos"]},
        },
    )
    kinds = template_baseline_media_kinds("identificacao", "default", repo)
    assert kinds == ["tables", "photos"]


def test_template_baseline_falls_back_to_section_registry() -> None:
    kinds = template_baseline_media_kinds("identificacao", "default", None)
    assert kinds == ["tables"]


def test_locked_workspace_media_skips_custom_sections() -> None:
    doc = ReportDocument(
        source_pdf_path=Path("/tmp/x.pdf"),
        client_project="Cliente",
        evaluated_component="Peça",
    )
    assert locked_workspace_media_kinds("custom_1", doc, None) == []


def test_merge_workspace_media_kinds_keeps_locked() -> None:
    merged = merge_workspace_media_kinds(["tables"], ["photos"])
    assert merged == ["photos", "tables"]
    merged_remove = merge_workspace_media_kinds(["tables"], [])
    assert merged_remove == ["tables"]


def test_sanitize_workspace_media_kinds_drops_table_on_grafica() -> None:
    merged = sanitize_workspace_media_kinds("grafica", [], ["photos", "tables"])
    assert merged == ["photos"]
