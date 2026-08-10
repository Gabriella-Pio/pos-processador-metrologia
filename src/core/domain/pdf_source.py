"""Utilitários para caminhos de PDF de origem."""
from __future__ import annotations

from pathlib import Path


def is_blank_source_pdf_path(path: Path | str | None) -> bool:
    """True quando não há referência a PDF (vazio, ``.`` ou ``..``)."""
    text = str(path or "").strip()
    return not text or text in {".", ".."}


def has_source_pdf_reference(path: Path | str | None) -> bool:
    """True quando há um caminho de PDF associado (mesmo que o arquivo não exista)."""
    return not is_blank_source_pdf_path(path)


def is_usable_source_pdf(path: Path | str | None) -> bool:
    """True quando o caminho aponta para um arquivo PDF legível no disco."""
    if is_blank_source_pdf_path(path):
        return False
    candidate = Path(str(path).strip())
    try:
        return candidate.is_file()
    except OSError:
        return False


def source_pdf_path_to_storage(path: Path | str | None) -> str:
    """Serializa caminho de PDF; vazio quando não há arquivo de origem."""
    if is_blank_source_pdf_path(path):
        return ""
    return str(path).strip()


def source_pdf_path_from_storage(value: str | None) -> Path:
    """Restaura caminho de PDF a partir do valor persistido."""
    if is_blank_source_pdf_path(value):
        return Path()
    return Path(str(value).strip())
