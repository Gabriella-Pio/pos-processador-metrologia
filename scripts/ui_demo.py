"""
Demo da UI com implementações fake em memória.

Para a aplicação completa com parser/exportador reais, use:
    python main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from PyQt6.QtWidgets import QApplication

from src.ui.main_window import MainWindow
from tests.fakes import (
    FakeReportExporter,
    FakeReportParser,
    InMemoryRecentFilesRepository,
    InMemoryTemplateRepository,
)


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
