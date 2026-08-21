"""Sanitização de texto para o PDF não estourar o layout."""
from __future__ import annotations

from src.core.domain.pdf_plain_text import limit_combining_marks, pdf_paragraph_text


def _zalgo(text: str, marks: int = 80) -> str:
    stack = "".join(chr(0x0300 + (index % 16)) for index in range(marks))
    return "".join(char + stack for char in text)


def test_limit_combining_marks_keeps_portuguese() -> None:
    assert limit_combining_marks("Inspeção da peça maçã") == "Inspeção da peça maçã"


def test_limit_combining_marks_strips_zalgo_overflow() -> None:
    raw = _zalgo("abc")
    cleaned = limit_combining_marks(raw)
    assert len(cleaned) < len(raw)
    combining_runs: list[int] = []
    run = 0
    for char in cleaned:
        if "\u0300" <= char <= "\u036f":
            run += 1
            continue
        if run:
            combining_runs.append(run)
        run = 0
    if run:
        combining_runs.append(run)
    assert all(count <= 2 for count in combining_runs)
    letters = "".join(char for char in cleaned if char.isalpha())
    assert "b" in letters and "c" in letters
    assert any(char.lower() in {"a", "à", "á", "â"} for char in letters)



def test_pdf_paragraph_text_escapes_xml() -> None:
    assert pdf_paragraph_text("a < b & c") == "a &lt; b &amp; c"
