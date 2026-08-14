"""Testes de detecção CALYPSO vs Bosello/INSP ECT."""
from __future__ import annotations

from src.core.application.batch_processing import infer_report_mode, template_id_for_kind
from src.core.parser.source_kind import detect_source_kind_from_text


def test_detect_bosello_marker() -> None:
    assert detect_source_kind_from_text("ZEISS BOSELLO MAX 80-150") == "insp_ect"
    assert detect_source_kind_from_text("Generated with ZEISS INSP ECT") == "insp_ect"


def test_detect_calypso_marker() -> None:
    assert detect_source_kind_from_text("ZEISS CALYPSO Protocolo de medição") == "calypso"


def test_infer_mode_and_template_for_bosello() -> None:
    assert infer_report_mode(["insp_ect"]) == "tomo_only"
    assert template_id_for_kind("insp_ect") == "tomografia"


def test_infer_mode_mixed() -> None:
    assert infer_report_mode(["calypso", "insp_ect"]) == "mixed"
