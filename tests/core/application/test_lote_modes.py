"""Testes de modos de lote (MMC / tomo / misto)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.core.application.batch_processing import (
    export_batch,
    infer_report_mode,
    parse_batch,
    template_id_for_kind,
)
from src.core.domain.ports import ReportDocument
from src.core.infrastructure.adapters import RealReportParserAdapter
from src.ui.features.workspace.services.document_session_service import DocumentSessionService

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "insp_ect_peca_uf.pdf"


def test_infer_report_mode() -> None:
    assert infer_report_mode(["calypso", "calypso"]) == "mmc_only"
    assert infer_report_mode(["insp_ect"]) == "tomo_only"
    assert infer_report_mode(["calypso", "insp_ect"]) == "mixed"


def test_template_id_for_kind() -> None:
    assert template_id_for_kind("calypso") == "default"
    assert template_id_for_kind("insp_ect") == "tomografia"


@pytest.mark.skipif(not FIXTURE.exists(), reason="fixture INSP ECT ausente")
def test_parse_batch_tomo_only() -> None:
    parser = RealReportParserAdapter()
    slots, rejected = parse_batch(
        parser,
        [FIXTURE],
        report_mode="tomo_only",
        client_project="Cliente",
        default_component="Peça",
    )
    assert not rejected
    assert len(slots) == 1
    assert slots[0].source_kind == "insp_ect"
    assert slots[0].template_id == "tomografia"
    assert slots[0].document.template_id == "tomografia"


@pytest.mark.skipif(not FIXTURE.exists(), reason="fixture INSP ECT ausente")
def test_mixed_project_assigns_templates_by_source_kind() -> None:
    parser = RealReportParserAdapter()
    service = DocumentSessionService(parser)
    session = service.build_project_session(
        "Cliente",
        [(FIXTURE, "Peça UF")],
        template_id="default",
        report_mode="mixed",
    )
    assert session.report_mode in {"mixed", "tomo_only"}
    ok, _ = service.parse_slot(session, 0)
    assert ok
    slot = session.documents[0]
    assert slot.source_kind == "insp_ect"
    assert slot.document is not None
    assert slot.document.template_id == "tomografia"


def test_export_batch_calls_exporter(tmp_path: Path) -> None:
    exporter = MagicMock()
    exporter.export.side_effect = lambda doc, path: path
    docs = [
        ReportDocument(
            source_pdf_path=Path(f"/tmp/a{i}.pdf"),
            client_project="C",
            evaluated_component="P",
        )
        for i in range(2)
    ]
    paths = export_batch(exporter, docs, tmp_path)
    assert len(paths) == 2
    assert exporter.export.call_count == 2
