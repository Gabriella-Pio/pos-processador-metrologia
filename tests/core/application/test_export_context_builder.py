"""Testes de montagem do contexto de exportação."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.core.application.export_context_builder import (
    build_historico_versoes,
    version_entries_to_historico_rows,
)
from src.core.domain.ports import ReportDocument, VersionEntry


def test_build_historico_versoes_prefers_explicit_entries() -> None:
    document = ReportDocument(
        source_pdf_path=Path("/tmp/a.pdf"),
        client_project="Cliente",
        evaluated_component="Peça",
        version_history=[
            VersionEntry(1, datetime(2026, 1, 1, 10, 0), "A", "doc v1"),
        ],
    )
    override = [
        VersionEntry(2, datetime(2026, 2, 1, 11, 0), "B", "project v2"),
    ]
    rows = build_historico_versoes(document, version_entries=override)
    assert rows == version_entries_to_historico_rows(override)
    assert rows[0]["version_number"] == 2
    assert rows[0]["responsible_name"] == "B"
