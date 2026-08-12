"""Testes de seções do catálogo disponíveis para inclusão no relatório."""
from __future__ import annotations

from pathlib import Path

from src.core.application.catalog_section_add import add_catalog_section
from src.core.application.template_block_resolver import (
    apply_section_order,
    inject_extra_catalog_sections,
)
from src.core.domain.ports import ReportDocument
from src.core.domain.section_schema import list_addable_catalog_sections


def test_list_addable_includes_missing_and_disabled() -> None:
    options = list_addable_catalog_sections(
        present_section_ids={"introducao", "identificacao", "grafica", "anexos"},
        deleted_section_ids={"grafica"},
    )
    by_id = {item["id"]: item for item in options}
    assert by_id["grafica"]["action"] == "restore"
    assert by_id["metodo_escopo"]["action"] == "add"
    assert "introducao" not in by_id


def test_add_catalog_section_injects_before_anexos() -> None:
    document = ReportDocument(
        source_pdf_path=Path("sample.pdf"),
        client_project="Cliente",
        evaluated_component="Peça",
    )
    assert add_catalog_section(document, "metodo_escopo") == "metodo_escopo"
    assert document.extra_section_ids == ["metodo_escopo"]

    blocks = apply_section_order(
        [{"tipo": "introducao", "config": {}}, {"tipo": "anexos", "config": {}}],
        document,
    )
    assert [b["tipo"] for b in blocks] == ["introducao", "metodo_escopo", "anexos"]


def test_add_catalog_section_restores_deleted() -> None:
    document = ReportDocument(
        source_pdf_path=Path("sample.pdf"),
        client_project="Cliente",
        evaluated_component="Peça",
        deleted_section_ids=["grafica"],
    )
    assert add_catalog_section(document, "grafica") == "grafica"
    assert "grafica" not in document.deleted_section_ids
    assert "grafica" in document.extra_section_ids


def test_inject_skips_already_present() -> None:
    document = ReportDocument(
        source_pdf_path=Path("sample.pdf"),
        client_project="Cliente",
        evaluated_component="Peça",
        extra_section_ids=["grafica"],
    )
    blocks = inject_extra_catalog_sections(
        [{"tipo": "grafica", "config": {}}, {"tipo": "anexos", "config": {}}],
        document,
    )
    assert [b["tipo"] for b in blocks] == ["grafica", "anexos"]
