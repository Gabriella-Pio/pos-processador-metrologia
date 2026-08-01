"""
Ponto de entrada da aplicação.

Usa implementações "fake" em memória das portas (``ReportParser``,
``ReportExporter``, ``RecentFilesRepository``, ``TemplateRepository``)
apenas para permitir rodar e validar visualmente a camada de UI de
forma isolada — o time responsável pelo ``src/core/`` substitui estas
classes pelas implementações reais (parser de PDF ZEISS + ReportLab +
SQLite) sem precisar tocar em nada dentro de ``src/ui/``.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from src.core.ports import ReportDocument, TechnicalControlInfo
from src.ui.main_window import MainWindow


class FakeReportParser:
    """Implementação de demonstração de ``ReportParser``."""

    def parse(self, pdf_path: Path) -> ReportDocument:
        return ReportDocument(
            source_pdf_path=pdf_path,
            client_project="",
            evaluated_component="",
            control_info=TechnicalControlInfo(measured_by="", reviewed_by=""),
        )


class FakeReportExporter:
    """Implementação de demonstração de ``ReportExporter``."""

    def export(self, document: ReportDocument, output_path: Path) -> Path:
        output_path.write_bytes(b"%PDF-1.4 fake export placeholder")
        return output_path


class InMemoryRecentFilesRepository:
    """Implementação de demonstração de ``RecentFilesRepository``."""

    def __init__(self) -> None:
        self._files = [
            {
                "id": "1",
                "file_name": "Relatorio_Peca_A.pdf",
                "client_project": "Cliente Alfa",
                "version": "3",
                "updated_at": datetime.now(),
            },
        ]

    def list_recent(self, limit: int = 20):
        return self._files[:limit]

    def save(self, document: ReportDocument, file_name: str) -> str:
        new_id = str(len(self._files) + 1)
        self._files.insert(
            0,
            {
                "id": new_id,
                "file_name": file_name,
                "client_project": document.client_project,
                "version": "1",
                "updated_at": datetime.now(),
            },
        )
        return new_id


class InMemoryTemplateRepository:
    """Implementação de demonstração de ``TemplateRepository``."""

    def __init__(self) -> None:
        self._templates = [
            {"id": "default", "name": "Padrão SENAI/ZEISS", "is_default": True},
        ]

    def list_templates(self):
        return self._templates

    def save_template(self, template_id: str, sections_config: dict) -> None:
        pass  # implementação real grava em JSON


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow(
        report_parser=FakeReportParser(),
        report_exporter=FakeReportExporter(),
        recent_files_repo=InMemoryRecentFilesRepository(),
        template_repo=InMemoryTemplateRepository(),
    )
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
