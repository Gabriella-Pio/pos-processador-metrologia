"""
Demo da UI com implementações fake em memória.

Para a aplicação completa com parser/exportador reais, use:
    python main.py
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from PyQt6.QtWidgets import QApplication

from src.core.domain.ports import ReportDocument, TechnicalControlInfo
from src.ui.main_window import MainWindow


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


class InMemoryRecentFilesRepository:
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

    def get_by_id(self, file_id: str):
        for item in self._files:
            if item["id"] == file_id:
                return {
                    "file_path": item["file_name"],
                    "client_project": item["client_project"],
                    "evaluated_component": item["file_name"],
                    "file_name": item["file_name"],
                }
        return None


class InMemoryTemplateRepository:
    def __init__(self) -> None:
        self._templates = [
            {"id": "default", "name": "Padrão SENAI/ZEISS", "is_default": True},
        ]

    def list_templates(self):
        return self._templates

    def save_template(self, template_id: str, sections_config: dict) -> None:
        pass

    def get_template_config(self, template_id: str) -> dict:
        return {}

    def get_content_defaults(self, template_id: str) -> dict:
        return {}

    def save_content_defaults(self, template_id: str, content: dict) -> None:
        pass

    def save_full_template(
        self, template_id: str, sections_config: dict, content_defaults: dict, name: str
    ) -> None:
        pass

    def update_template_name(self, template_id: str, name: str) -> None:
        pass


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
