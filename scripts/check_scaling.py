"""Verifica se janela e diálogos cabem na tela sob diferentes escalas do Windows.

Uso: python scripts/check_scaling.py [fator]

O fator entra via ``QT_SCALE_FACTOR`` e multiplica a escala já aplicada pelo
sistema, permitindo emular 150%, 175% e 200% num monitor configurado em 125%.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def main() -> int:
    factor = sys.argv[1] if len(sys.argv) > 1 else "1.0"
    os.environ["QT_SCALE_FACTOR"] = factor

    from PyQt6.QtWidgets import QApplication

    from src.ui.components.panels.image_annotation_dialog import ImageAnnotationDialog
    from src.ui.dialogs.help_accessibility_dialog import HelpAccessibilityDialog
    from src.ui.features.home.dialogs.import_dialog import ImportDialog
    from src.ui.shared.report_editor.editor_shell import (
        EDITING_RATIOS,
        PREVIEW_ONLY_RATIOS,
        splitter_sizes,
    )
    from src.ui.styles import available_size, preview_device_pixel_ratio

    app = QApplication.instance() or QApplication([])
    screen_w, screen_h = available_size()
    dpr = preview_device_pixel_ratio()
    print(f"QT_SCALE_FACTOR={factor}  area logica={screen_w}x{screen_h}  dpr={dpr}")

    failures = 0
    for label, build in (
        ("ImportDialog", ImportDialog),
        ("HelpAccessibilityDialog", HelpAccessibilityDialog),
        ("ImageAnnotationDialog", ImageAnnotationDialog),
    ):
        dialog = build()
        dialog.show()
        for _ in range(3):
            app.processEvents()
        width = dialog.width()
        height = dialog.height()
        fits = width <= screen_w and height <= screen_h
        failures += 0 if fits else 1
        scroll = " (com rolagem)" if getattr(dialog, "_fit_scroll", None) is not None else ""
        print(f"  {'ok  ' if fits else 'ESTOURA'} {label}: {width}x{height}{scroll}")
        dialog.close()
        dialog.deleteLater()

    for name, ratios in (("edicao", EDITING_RATIOS), ("preview", PREVIEW_ONLY_RATIOS)):
        sizes = splitter_sizes(screen_w, ratios)
        fits = sum(sizes) <= screen_w
        failures += 0 if fits else 1
        print(f"  {'ok  ' if fits else 'ESTOURA'} splitter {name}: {sizes} soma={sum(sizes)}")

    app.quit()
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
