"""Testes do parser INSP ECT / detecção de source kind."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.core.infrastructure.adapters import RealReportParserAdapter
from src.core.parser.insp_ect_parser import InspEctParser
from src.core.parser.parser import PDFParserService
from src.core.parser.source_kind import detect_source_kind, detect_source_kind_from_text


def test_detect_insp_ect_from_fixture(require_insp_ect_fixture: Path) -> None:
    assert detect_source_kind(require_insp_ect_fixture) == "insp_ect"


def test_detect_from_text_markers() -> None:
    assert detect_source_kind_from_text("Generated with ZEISS INSP EC T 2025") == "insp_ect"
    assert detect_source_kind_from_text("ZEISS CALYPSO 7.4 Protocolo de medição") == "calypso"


def test_insp_ect_extracts_volume_and_pores(require_insp_ect_fixture: Path) -> None:
    dto = InspEctParser.parse(str(require_insp_ect_fixture))
    assert dto.source_kind == "insp_ect"
    assert dto.software.startswith("ZEISS INSP ECT")
    assert dto.pore_count == 370
    assert len(dto.defect_items) == 370
    assert len(dto.itens_medicao) == 370
    assert dto.itens_medicao[0].tipo == "Vp"
    assert dto.itens_medicao[0].desvio
    assert dto.volume_total_mm3  # e.g. 1099.64
    assert dto.equipamento_default.startswith("ZEISS BOSELLO")


def test_pdf_parser_service_dispatches_insp_ect(require_insp_ect_fixture: Path) -> None:
    dto = PDFParserService.extrair_dados_avancados(str(require_insp_ect_fixture))
    assert getattr(dto, "source_kind") == "insp_ect"
    assert len(dto.itens_medicao) == 370


def test_adapter_sets_source_kind(require_insp_ect_fixture: Path) -> None:
    doc = RealReportParserAdapter().parse(require_insp_ect_fixture)
    assert doc.source_kind == "insp_ect"
    assert doc.raw_parsed_data is not None
    assert doc.evaluated_component


def test_extract_graphic_images_renders_viewports_with_axes(require_insp_ect_fixture: Path) -> None:
    from PIL import Image

    paths = InspEctParser.extract_graphic_images_from_pdf(str(require_insp_ect_fixture))
    assert len(paths) == 6
    widths = []
    for path in paths:
        with Image.open(path) as img:
            widths.append(img.width)
    assert sum(1 for width in widths if width > 1000) == 2
    assert sum(1 for width in widths if 600 < width < 900) == 4
