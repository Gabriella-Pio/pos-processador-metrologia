"""Testes de classificação de métodos de laboratório (CMM / O-inspect / Bosello)."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from src.core.application.lab_methods import (
    build_mixed_introducao_metric_rows,
    classify_calypso_method,
    classify_slot_method,
    collect_lab_methods,
    format_methods_phrase,
)
from src.core.domain.ports import ReportDocument
from src.core.domain.project_session import ProjectDocumentSlot
from src.core.parser.table_extractor import MedicaoItemDto


def test_classify_o_inspect_and_cmm() -> None:
    assert classify_calypso_method("O-INSPECT 543") == "o_inspect"
    assert classify_calypso_method("ZEISS O INSPECT") == "o_inspect"
    assert classify_calypso_method("DURAMAX") == "cmm"
    assert classify_calypso_method("PRISMO_USS2") == "cmm"


def test_collect_methods_from_mixed_slots() -> None:
    optic = ReportDocument(
        source_pdf_path=Path("/tmp/oinspect.pdf"),
        client_project="Cargill",
        evaluated_component="Eixo",
        raw_parsed_data=SimpleNamespace(maquina_mmc="O-INSPECT 543", itens_medicao=[]),
        source_kind="calypso",
    )
    cmm = ReportDocument(
        source_pdf_path=Path("/tmp/cmm.pdf"),
        client_project="Cargill",
        evaluated_component="Eixo",
        raw_parsed_data=SimpleNamespace(maquina_mmc="DURAMAX", itens_medicao=[]),
        source_kind="calypso",
    )
    tomo = ReportDocument(
        source_pdf_path=Path("/tmp/bosello.pdf"),
        client_project="Cargill",
        evaluated_component="Eixo",
        raw_parsed_data=SimpleNamespace(maquina_mmc="ZEISS BOSELLO MAX 80-150"),
        source_kind="insp_ect",
    )
    slots = [
        ProjectDocumentSlot(Path("/tmp/oinspect.pdf"), "Eixo", document=optic, source_kind="calypso"),
        ProjectDocumentSlot(Path("/tmp/cmm.pdf"), "Eixo", document=cmm, source_kind="calypso"),
        ProjectDocumentSlot(Path("/tmp/bosello.pdf"), "Eixo", document=tomo, source_kind="insp_ect"),
    ]
    methods = collect_lab_methods(slots)
    assert methods == ["cmm", "o_inspect", "bosello"]
    phrase = format_methods_phrase(methods)
    assert "CMM" in phrase
    assert "O-inspect" in phrase
    assert "Bosello" in phrase


def test_mixed_intro_rows_for_oinspect_and_bosello() -> None:
    item = MedicaoItemDto("Diametro_X", "Diâmetro", "10,0", "10,0", "0,1", "0,1", "0", "Dentro")
    optic = ReportDocument(
        source_pdf_path=Path("/tmp/oinspect.pdf"),
        client_project="Cargill",
        evaluated_component="Eixo",
        raw_parsed_data=SimpleNamespace(
            maquina_mmc="O-INSPECT",
            itens_medicao=[item],
            numero_medicoes_cabecalho=1,
        ),
        source_kind="calypso",
    )
    tomo = ReportDocument(
        source_pdf_path=Path("/tmp/bosello.pdf"),
        client_project="Cargill",
        evaluated_component="Eixo",
        raw_parsed_data=SimpleNamespace(maquina_mmc="ZEISS BOSELLO MAX 80-150"),
        source_kind="insp_ect",
    )
    slots = [
        ProjectDocumentSlot(Path("/tmp/oinspect.pdf"), "Eixo", document=optic, source_kind="calypso"),
        ProjectDocumentSlot(Path("/tmp/bosello.pdf"), "Eixo", document=tomo, source_kind="insp_ect"),
    ]
    assert classify_slot_method(slots[0]) == "o_inspect"
    assert classify_slot_method(slots[1]) == "bosello"
    rows = build_mixed_introducao_metric_rows(slots, dimensional_dto=optic.raw_parsed_data)
    by_id = {row["id"]: row for row in rows}
    assert by_id["tipo_analise"]["value"] == "Óptica e tomográfica"
    assert "óptico (O-inspect)" in by_id["metodos"]["value"]
    assert "tomográfico (Bosello)" in by_id["metodos"]["value"]
    assert "O-INSPECT" in by_id["equipamentos"]["value"]
    assert "BOSELLO" in by_id["equipamentos"]["value"].upper()
    assert by_id["tomografia"]["label"] == "TOMOGRAFIA"
