"""Geração de preview PDF → PNG fora da thread da UI."""
from __future__ import annotations

import tempfile
from pathlib import Path

import fitz

from src.core.domain.ports import ReportDocument, ReportExporter
from src.ui.shared.report_editor.preview_constants import raster_zoom


class PreviewService:
    def __init__(self, exporter: ReportExporter) -> None:
        self._exporter = exporter

    def render_pages(self, document: ReportDocument, zoom: float | None = None) -> list[bytes]:
        with tempfile.TemporaryDirectory(prefix="metrologia_preview_") as tmp_dir:
            rascunho_path = Path(tmp_dir) / "preview.pdf"
            self._exporter.export(document, rascunho_path)
            return self._rasterize(rascunho_path, raster_zoom() if zoom is None else zoom)

    @staticmethod
    def _rasterize(pdf_path: Path, zoom: float) -> list[bytes]:
        paginas: list[bytes] = []
        matriz_zoom = fitz.Matrix(zoom, zoom)
        with fitz.open(pdf_path) as documento_pdf:
            for pagina in documento_pdf:
                pixmap = pagina.get_pixmap(matrix=matriz_zoom)
                paginas.append(pixmap.tobytes("png"))
        return paginas

    def section_anchor_map(self, document: ReportDocument) -> dict[str, dict]:
        exporter = self._exporter
        if hasattr(exporter, "_last_section_anchor_map"):
            self.render_pages(document)
            return dict(getattr(exporter, "_last_section_anchor_map", {}))
        return {}
