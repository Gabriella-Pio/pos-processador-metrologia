"""Testes do parser INSP ECT / detecção de source kind."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.core.infrastructure.adapters import RealReportParserAdapter
from src.core.parser.insp_ect_parser import InspEctParser
from src.core.parser.parser import PDFParserService
from src.core.parser.source_kind import detect_source_kind, detect_source_kind_from_text

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "insp_ect_peca_uf.pdf"


@pytest.mark.skipif(not FIXTURE.exists(), reason="fixture INSP ECT ausente")
def test_detect_insp_ect_from_fixture() -> None:
    assert detect_source_kind(FIXTURE) == "insp_ect"


def test_detect_from_text_markers() -> None:
    assert detect_source_kind_from_text("Generated with ZEISS INSP EC T 2025") == "insp_ect"
    assert detect_source_kind_from_text("ZEISS CALYPSO 7.4 Protocolo de medição") == "calypso"


@pytest.mark.skipif(not FIXTURE.exists(), reason="fixture INSP ECT ausente")
def test_insp_ect_extracts_volume_and_pores() -> None:
    dto = InspEctParser.parse(str(FIXTURE))
    assert dto.source_kind == "insp_ect"
    assert dto.software.startswith("ZEISS INSP ECT")
    assert dto.pore_count == 370
    assert len(dto.defect_items) == 370
    assert len(dto.itens_medicao) == 370
    assert dto.itens_medicao[0].tipo == "Vp"
    assert dto.itens_medicao[0].desvio
    assert dto.volume_total_mm3  # e.g. 1099.64
    assert dto.equipamento_default.startswith("ZEISS BOSELLO")


@pytest.mark.skipif(not FIXTURE.exists(), reason="fixture INSP ECT ausente")
def test_pdf_parser_service_dispatches_insp_ect() -> None:
    dto = PDFParserService.extrair_dados_avancados(str(FIXTURE))
    assert getattr(dto, "source_kind") == "insp_ect"
    assert len(dto.itens_medicao) == 370


@pytest.mark.skipif(not FIXTURE.exists(), reason="fixture INSP ECT ausente")
def test_adapter_sets_source_kind() -> None:
    doc = RealReportParserAdapter().parse(FIXTURE)
    assert doc.source_kind == "insp_ect"
    assert doc.raw_parsed_data is not None
    assert doc.evaluated_component
