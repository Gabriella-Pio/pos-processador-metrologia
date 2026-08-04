"""Comparação de layout e dados vs template."""
from __future__ import annotations

from src.core.domain.ports import ReportDocument, TemplateRepository
from src.core.domain.template_diff import is_data_dirty, is_layout_dirty_vs_template, serialize_layout_snapshot


def document_has_layout_changes(
    document: ReportDocument,
    template_repo: TemplateRepository | None,
) -> bool:
    return is_layout_dirty_vs_template(document, template_repo)


def document_has_data_changes(document: ReportDocument) -> bool:
    return is_data_dirty(document)


def layout_snapshot(document: ReportDocument) -> dict:
    return serialize_layout_snapshot(document)
