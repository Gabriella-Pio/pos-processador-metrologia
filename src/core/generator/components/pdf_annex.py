"""Anexa páginas de PDFs de origem ao relatório gerado (PyMuPDF)."""
from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def append_source_pdfs(report_pdf: str | Path, source_pdfs: list[str | Path]) -> None:
    """Concatena ``source_pdfs`` ao final de ``report_pdf`` (in-place)."""
    report_path = Path(report_pdf)
    paths = [Path(p) for p in source_pdfs if p and Path(p).is_file()]
    if not report_path.is_file() or not paths:
        return

    try:
        import fitz
    except ImportError:
        logger.warning("PyMuPDF indisponível — anexos PDF não foram mesclados.")
        return

    tmp_path = report_path.with_suffix(report_path.suffix + ".annex.tmp")
    try:
        out_doc = fitz.open(report_path)
        for src in paths:
            try:
                with fitz.open(src) as annex:
                    out_doc.insert_pdf(annex)
            except Exception:
                logger.exception("Falha ao anexar PDF: %s", src)
        out_doc.save(tmp_path)
        out_doc.close()
        tmp_path.replace(report_path)
    except Exception:
        logger.exception("Falha ao mesclar anexos em %s", report_path)
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
