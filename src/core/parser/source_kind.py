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

# (resolved_path, mtime_ns, size, sample_pages) → kind
_DETECT_CACHE: dict[tuple[str, int, int, int], SourceKind] = {}


def _cache_key(path: Path, sample_pages: int) -> tuple[str, int, int, int] | None:
    try:
        resolved = path.resolve()
        stat = resolved.stat()
    except OSError:
        return None
    return (str(resolved), stat.st_mtime_ns, stat.st_size, sample_pages)


def clear_source_kind_cache() -> None:
    """Limpa o cache (testes / arquivos substituídos no mesmo path)."""
    _DETECT_CACHE.clear()


def detect_source_kind(pdf_path: Path | str, sample_pages: int = 2) -> SourceKind:
    """Identifica o vendor/software a partir do texto das primeiras páginas."""
    path = Path(pdf_path)
    key = _cache_key(path, sample_pages)
    if key is not None and key in _DETECT_CACHE:
        return _DETECT_CACHE[key]

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

    kind = detect_source_kind_from_text(sample)
    if key is not None:
        _DETECT_CACHE[key] = kind
    return kind


def detect_source_kind_from_text(text: str) -> SourceKind:
    upper = (text or "").upper()
    if any(marker.upper() in upper for marker in _INSP_ECT_MARKERS):
        return "insp_ect"
    if any(marker.upper() in upper for marker in _CALYPSO_MARKERS):
        return "calypso"
    return "calypso"
