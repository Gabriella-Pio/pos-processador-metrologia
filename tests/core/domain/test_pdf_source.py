"""Testes de caminhos de PDF de origem."""
from __future__ import annotations

from pathlib import Path

from src.core.domain.pdf_source import (
    is_usable_source_pdf,
    source_pdf_path_from_storage,
    source_pdf_path_to_storage,
)


def test_path_dot_is_not_usable_pdf() -> None:
    assert is_usable_source_pdf(Path(".")) is False
    assert is_usable_source_pdf(Path()) is False
    assert is_usable_source_pdf("") is False


def test_source_pdf_path_roundtrip_empty() -> None:
    assert source_pdf_path_to_storage(Path()) == ""
    assert source_pdf_path_to_storage(Path(".")) == ""
    assert source_pdf_path_from_storage("") == Path()
    assert source_pdf_path_from_storage(".") == Path()


def test_source_pdf_path_roundtrip_existing(tmp_path: Path) -> None:
    pdf = tmp_path / "relatorio.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    assert source_pdf_path_to_storage(pdf) == str(pdf)
    assert source_pdf_path_from_storage(str(pdf)) == pdf
