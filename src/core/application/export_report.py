"""Validação pré-exportação."""
from __future__ import annotations

from src.core.domain.export_validator import ExportIssue, validate_for_export
from src.core.domain.ports import ReportDocument


def validate_export(document: ReportDocument) -> list[ExportIssue]:
    return validate_for_export(document)
