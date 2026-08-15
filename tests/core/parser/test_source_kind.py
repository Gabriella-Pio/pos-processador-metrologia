"""Testes de detecção CALYPSO vs Bosello/INSPECT."""
from __future__ import annotations

from src.core.application.batch_processing import infer_report_mode, template_id_for_kind
from src.core.parser.source_kind import detect_source_kind_from_text


def test_detect_bosello_marker() -> None:
    assert detect_source_kind_from_text("ZEISS BOSELLO MAX 80-150") == "insp_ect"
    assert detect_source_kind_from_text("Generated with ZEISS INSPECT") == "insp_ect"


def test_detect_calypso_marker() -> None:
    assert detect_source_kind_from_text("ZEISS CALYPSO Protocolo de medição") == "calypso"


def test_detect_source_kind_cache(tmp_path) -> None:
    from src.core.parser.source_kind import clear_source_kind_cache, detect_source_kind
    import fitz

    clear_source_kind_cache()
    pdf = tmp_path / "sample.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "ZEISS CALYPSO Protocolo de medição")
    doc.save(pdf)
    doc.close()

    assert detect_source_kind(pdf) == "calypso"
    # Segunda chamada deve bater no cache (mesmo path/mtime/size)
    assert detect_source_kind(pdf) == "calypso"
    clear_source_kind_cache()


def test_infer_mode_and_template_for_bosello() -> None:
    assert infer_report_mode(["insp_ect"]) == "tomo_only"
    assert template_id_for_kind("insp_ect") == "tomografia"


def test_infer_mode_mixed() -> None:
    assert infer_report_mode(["calypso", "insp_ect"]) == "mixed"
