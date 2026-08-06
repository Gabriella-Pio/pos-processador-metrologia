"""Adaptadores fake para demo e testes de UI."""
from __future__ import annotations

from pathlib import Path

from src.core.domain.ports import ReportDocument, TechnicalControlInfo


class FakeReportParser:
    def parse(self, pdf_path: Path) -> ReportDocument:
        return ReportDocument(
            source_pdf_path=pdf_path,
            client_project="",
            evaluated_component="",
            control_info=TechnicalControlInfo(measured_by="", reviewed_by=""),
        )


class FakeReportExporter:
    def export(self, document: ReportDocument, output_path: Path) -> Path:
        output_path.write_bytes(b"%PDF-1.4 fake export placeholder")
        return output_path
