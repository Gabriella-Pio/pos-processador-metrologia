"""Testes do SectionSummaryPresenter."""
from __future__ import annotations

from pathlib import Path

from src.core.domain.ports import ReportDocument
from src.core.parser.parser import RelatorioCalypsoDto
from src.ui.features.workspace.presenters.section_summary_presenter import SectionSummaryPresenter


class _FakeExporter:
    def list_sections(self, document: ReportDocument) -> list[dict]:
        return [
            {"id": "introducao", "title": "INTRODUÇÃO", "section_number": None},
            {"id": "identificacao", "title": "1. IDENTIFICAÇÃO", "section_number": 1},
        ]


def test_presenter_strips_number_prefix_from_display_title() -> None:
    doc = ReportDocument(
        source_pdf_path=Path("/tmp/x.pdf"),
        client_project="Cliente",
        evaluated_component="Peça",
    )
    doc.raw_parsed_data = RelatorioCalypsoDto(componente="Peça")
    presenter = SectionSummaryPresenter(_FakeExporter())
    items = presenter.build(doc)
    ident = next(i for i in items if i.id == "identificacao")
    assert not ident.display_title.startswith("1.")
    assert ident.section_number == 1


def test_presenter_builds_display_title_with_overrides() -> None:
    doc = ReportDocument(
        source_pdf_path=Path("/tmp/x.pdf"),
        client_project="Cliente",
        evaluated_component="Peça",
    )
    doc.raw_parsed_data = RelatorioCalypsoDto(componente="Peça")
    doc.section_overrides["introducao"] = {"section_title": "Intro custom"}
    presenter = SectionSummaryPresenter(_FakeExporter())
    items = presenter.build(doc)
    intro = next(i for i in items if i.id == "introducao")
    assert intro.display_title == "Intro custom"
    assert intro.has_overrides


def test_presenter_keeps_disabled_sections_in_summary() -> None:
    doc = ReportDocument(
        source_pdf_path=Path("/tmp/x.pdf"),
        client_project="Cliente",
        evaluated_component="Peça",
    )
    doc.raw_parsed_data = RelatorioCalypsoDto(componente="Peça")
    doc.deleted_section_ids = ["identificacao"]
    presenter = SectionSummaryPresenter(_FakeExporter())
    items = presenter.build(doc)
    ident = next(i for i in items if i.id == "identificacao")
    assert ident.enabled is False
