"""Testes da camada application."""
from pathlib import Path

from src.core.application.document_editing import (
    extract_global_field_values,
    sync_operador,
)
from src.core.application.export_report import validate_export
from src.core.application.template_layout import (
    document_has_data_changes,
    document_has_layout_changes,
)
from src.core.domain.ports import ReportDocument
from src.core.infrastructure.template_repository import JSONTemplateRepository


def test_application_sync_operador() -> None:
    doc = ReportDocument(
        source_pdf_path=Path("/tmp/x.pdf"),
        client_project="Cliente",
        evaluated_component="Peça",
    )
    sync_operador(doc, "Maria")
    values, overridden = extract_global_field_values(doc)
    assert values["operador"] == "Maria"
    assert "operador" in overridden


def test_application_layout_vs_data_dirty(tmp_path) -> None:
    repo = JSONTemplateRepository(storage_path=str(tmp_path / "templates.json"))
    doc = ReportDocument(
        source_pdf_path=Path("/tmp/x.pdf"),
        client_project="Cliente",
        evaluated_component="Peça",
    )
    doc.template_id = "default"
    assert not document_has_layout_changes(doc, repo)
    assert not document_has_data_changes(doc)
    doc.parsed_overrides["scalar"] = {"operador": "X"}
    assert document_has_data_changes(doc)
    assert not document_has_layout_changes(doc, repo)


def test_application_validate_export_blocks_empty_client() -> None:
    doc = ReportDocument(
        source_pdf_path=Path("/tmp/x.pdf"),
        client_project="",
        evaluated_component="Peça",
    )
    issues = validate_export(doc)
    assert any(i.level == "error" for i in issues)
