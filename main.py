import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def _configurar_logging() -> None:
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

from src.app.bootstrap import create_main_window
from src.ui.accessibility import AppearanceManager


def main() -> None:
    app = QApplication(sys.argv)
    AppearanceManager.instance().load()
    window = create_main_window()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
