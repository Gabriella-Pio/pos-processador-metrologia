"""Testes de projeto tomográfico sem PDF de origem."""
from __future__ import annotations

from pathlib import Path

from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession
from src.ui.features.workspace.services.document_session_service import DocumentSessionService


class _ParserStub:
    def parse(self, pdf_path: Path):
        raise AssertionError(f"parser não deveria ser chamado: {pdf_path}")


def test_parse_slot_without_pdf_uses_manual_document() -> None:
    service = DocumentSessionService(_ParserStub())
    session = ProjectSession(
        client_project="Cliente",
        template_id="tomografia",
        report_mode="tomo_only",
        documents=[
            ProjectDocumentSlot(
                source_pdf_path=Path("."),
                evaluated_component="Peça UF",
                source_kind="insp_ect",
                template_id="tomografia",
            )
        ],
    )

    ok, _notice = service.parse_slot(session, 0)

    assert ok is True
    document = session.documents[0].document
    assert document is not None
    assert document.template_id == "tomografia"
    assert document.images == []
