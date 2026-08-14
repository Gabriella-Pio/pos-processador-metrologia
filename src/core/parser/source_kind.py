"""Detecção do tipo de PDF de origem (CALYPSO vs INSPECT / Bosello)."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import fitz

SourceKind = Literal["calypso", "insp_ect"]

_INSP_ECT_MARKERS = (
    "Generated with ZEISS INSP EC T",
    "Generated with ZEISS INSPECT",
    "ZEISS INSP EC T",
    "ZEISS INSPECT",
    "Defeito do volume",
    "BOSELLO",
    "ZEISS BOSELLO",
)
_CALYPSO_MARKERS = (
    "CALYPSO",
    "ZEISS CALYPSO",
    "Protocolo de medição",
    "Lista de características",
)


def detect_source_kind(pdf_path: Path | str, sample_pages: int = 2) -> SourceKind:
    """Identifica o vendor/software a partir do texto das primeiras páginas."""
    path = Path(pdf_path)
    doc = fitz.open(path)
    try:
        chunks: list[str] = []
        for index, page in enumerate(doc):
            if index >= sample_pages:
                break
            chunks.append(page.get_text("text") or "")
        sample = "\n".join(chunks)
    finally:
        doc.close()

    sample_upper = sample.upper()
    if any(marker.upper() in sample_upper for marker in _INSP_ECT_MARKERS):
        return "insp_ect"
    if any(marker.upper() in sample_upper for marker in _CALYPSO_MARKERS):
        return "calypso"
    # Default: treat as CALYPSO (legado)
    return "calypso"


def detect_source_kind_from_text(text: str) -> SourceKind:
    upper = (text or "").upper()
    if any(marker.upper() in upper for marker in _INSP_ECT_MARKERS):
        return "insp_ect"
    if any(marker.upper() in upper for marker in _CALYPSO_MARKERS):
        return "calypso"
    return "calypso"
