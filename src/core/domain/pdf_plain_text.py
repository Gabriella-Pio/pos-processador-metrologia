"""Texto de usuário seguro para layout PDF (ReportLab)."""
from __future__ import annotations

import html
import unicodedata

# Português usa pré-compostos após NFC; 2 marcas cobrem acentos raros sem overflow.
_MAX_COMBINING_PER_BASE = 2
_ALLOWED_CONTROLS = {"\n", "\t"}


def limit_combining_marks(
    text: str,
    *,
    max_per_base: int = _MAX_COMBINING_PER_BASE,
) -> str:
    """Normaliza NFC e limita marcas combinantes por caractere-base.

    Texto “zalgo” (centenas de diacríticos empilhados) explode a altura da
    linha no ReportLab e gera ``LayoutError`` em tabelas que não cabem na página.
    """
    if not text:
        return ""
    normalized = unicodedata.normalize("NFC", text)
    out: list[str] = []
    combining_run = 0
    for char in normalized:
        category = unicodedata.category(char)
        if category == "Cc" and char not in _ALLOWED_CONTROLS:
            continue
        if unicodedata.combining(char):
            if combining_run < max_per_base:
                out.append(char)
            combining_run += 1
            continue
        combining_run = 0
        if category == "Cf":
            continue
        out.append(char)
    return "".join(out)


def pdf_paragraph_text(text: str) -> str:
    """Texto plano para ``Paragraph``: sem marcas combinantes excessivas e com ``<>&`` escapados."""
    cleaned = limit_combining_marks(str(text or ""))
    return html.escape(cleaned, quote=False)
