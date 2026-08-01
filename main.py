import logging
import sys
from pathlib import Path

# Este arquivo fica na raiz do projeto (ao lado de app.py); ROOT_DIR aponta
# para essa mesma pasta, que é onde vive o pacote "src".
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def _configurar_logging() -> None:
    """Grava logs (incluindo tracebacks completos de erros) em disco.

    A UI só mostra uma mensagem amigável nas caixas de diálogo — mas o
    motivo técnico completo de qualquer falha (parser, exportador,
    banco de dados) sempre vai parar aqui, mesmo que a pessoa não clique
    em "Mostrar Detalhes" na hora.
    """
    log_dir = ROOT_DIR / "output_pdfs" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "app.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


_configurar_logging()

from PyQt6.QtWidgets import QApplication

from src.core.adapters import RealReportParserAdapter, RealReportExporterAdapter
from src.core.database import DatabaseManager
from src.core.recent_files_repository import SQLiteRecentFilesAdapter
from src.core.template_repository import JSONTemplateRepository
from src.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)

    # Repositórios reais (persistência em disco)
    db_manager = DatabaseManager()
    recent_files_repo = SQLiteRecentFilesAdapter(db_manager)
    template_repo = JSONTemplateRepository()

    # Adaptadores reais do parser/gerador
    report_parser = RealReportParserAdapter()
    report_exporter = RealReportExporterAdapter(template_repository=template_repo)

    # Janela principal com injeção de dependências
    window = MainWindow(
        report_parser=report_parser,
        report_exporter=report_exporter,
        recent_files_repo=recent_files_repo,
        template_repo=template_repo,
    )

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
