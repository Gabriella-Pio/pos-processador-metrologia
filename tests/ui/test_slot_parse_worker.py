"""Testes da fila de parse em background."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QCoreApplication, QThreadPool
from PyQt6.QtWidgets import QApplication

from src.core.domain.ports import ReportDocument, TechnicalControlInfo
from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession
from src.ui.features.workspace.services.document_session_service import DocumentSessionService
from src.ui.features.workspace.services.slot_parse_worker import BackgroundSlotParseQueue


class _ParserStub:
    def parse(self, pdf_path: Path) -> ReportDocument:
        return ReportDocument(
            source_pdf_path=pdf_path,
            client_project="C",
            evaluated_component="P",
            control_info=TechnicalControlInfo(
                measured_by="op",
                reviewed_by="",
                approved_by="",
                role="",
                institutional_email="",
            ),
            source_kind="calypso",
        )


def _app() -> QCoreApplication:
    existing = QApplication.instance()
    if existing is not None:
        return existing
    return QApplication([])


def test_background_queue_attaches_via_signal() -> None:
    app = _app()
    service = DocumentSessionService(_ParserStub())
    session = ProjectSession(
        client_project="Cliente",
        template_id="default",
        report_mode="mmc_only",
        documents=[
            ProjectDocumentSlot(
                source_pdf_path=Path("/tmp/a.pdf"),
                evaluated_component="A",
                source_kind="calypso",
            ),
            ProjectDocumentSlot(
                source_pdf_path=Path("/tmp/b.pdf"),
                evaluated_component="B",
                source_kind="calypso",
            ),
        ],
    )
    # Simula peça ativa já parseada
    session.documents[0].document = ReportDocument(
        source_pdf_path=session.documents[0].source_pdf_path,
        client_project="Cliente",
        evaluated_component="A",
        control_info=TechnicalControlInfo(
            measured_by="op",
            reviewed_by="",
            approved_by="",
            role="",
            institutional_email="",
        ),
        source_kind="calypso",
    )

    queue = BackgroundSlotParseQueue(service)
    queue._pool = QThreadPool.globalInstance() or QThreadPool()
    ready: list[tuple[int, object]] = []
    idle: list[int] = []

    queue.slot_ready.connect(lambda gen, idx, doc, notice: ready.append((idx, doc)))
    queue.queue_idle.connect(lambda gen: idle.append(gen))

    generation = queue.enqueue(session, [1])

    # Espera worker (QueuedConnection) processar
    for _ in range(50):
        QCoreApplication.processEvents()
        if idle:
            break
        import time

        time.sleep(0.02)

    assert generation in idle or idle
    assert ready
    idx, document = ready[0]
    assert idx == 1
    assert document is not None
    service.attach_document_to_slot(session, idx, document)  # type: ignore[arg-type]
    assert session.documents[1].document is not None
