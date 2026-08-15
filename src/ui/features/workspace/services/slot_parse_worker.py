"""Parse de slots de projeto em QThreadPool (fora da UI thread)."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot

from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession
from src.core.domain.ports import ReportDocument
from src.ui.features.workspace.services.document_session_service import DocumentSessionService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SlotParseJob:
    """Snapshot imutável dos dados necessários para parse em background."""

    generation: int
    index: int
    client_project: str
    report_mode: str
    session_template_id: str
    source_pdf_path: Path
    evaluated_component: str
    source_kind: str
    template_id: str | None


def build_slot_parse_job(
    generation: int,
    session: ProjectSession,
    index: int,
) -> SlotParseJob:
    slot = session.documents[index]
    return SlotParseJob(
        generation=generation,
        index=index,
        client_project=session.client_project,
        report_mode=session.report_mode,
        session_template_id=session.template_id,
        source_pdf_path=slot.source_pdf_path,
        evaluated_component=slot.evaluated_component,
        source_kind=slot.source_kind or "calypso",
        template_id=slot.template_id,
    )


def _session_stub_for_job(job: SlotParseJob) -> tuple[ProjectSession, ProjectDocumentSlot]:
    """Sessão mínima só para create_document_for_slot (sem mutar a sessão real)."""
    slot = ProjectDocumentSlot(
        source_pdf_path=job.source_pdf_path,
        evaluated_component=job.evaluated_component,
        source_kind=job.source_kind,
        template_id=job.template_id,
    )
    session = ProjectSession(
        client_project=job.client_project,
        template_id=job.session_template_id,
        report_mode=job.report_mode,  # type: ignore[arg-type]
        documents=[slot],
    )
    return session, slot


class SlotParseWorkerSignals(QObject):
    finished = pyqtSignal(int, int, object, str)  # generation, index, document, notice
    failed = pyqtSignal(int, int, str)  # generation, index, error_details


class SlotParseWorker(QRunnable):
    def __init__(self, job: SlotParseJob, doc_service: DocumentSessionService) -> None:
        super().__init__()
        self._job = job
        self._doc_service = doc_service
        self.signals = SlotParseWorkerSignals()

    @pyqtSlot()
    def run(self) -> None:
        job = self._job
        try:
            session, slot = _session_stub_for_job(job)
            document, notice, error = self._doc_service.create_document_for_slot(session, slot)
            if document is None:
                self.signals.failed.emit(job.generation, job.index, error or "Falha ao ler o PDF")
                return
            self.signals.finished.emit(job.generation, job.index, document, notice)
        except Exception:
            logger.exception("Falha no parse em background (slot %s)", job.index)
            import traceback

            self.signals.failed.emit(job.generation, job.index, traceback.format_exc())


class BackgroundSlotParseQueue(QObject):
    """Fila sequencial: um slot por vez no global thread pool."""

    slot_ready = pyqtSignal(int, int, object, str)  # generation, index, document, notice
    slot_failed = pyqtSignal(int, int, str)  # generation, index, error
    queue_idle = pyqtSignal(int)  # generation

    def __init__(self, doc_service: DocumentSessionService, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._doc_service = doc_service
        self._generation = 0
        self._pending: list[int] = []
        self._session: ProjectSession | None = None
        self._active_workers = 0
        self._claimed: set[int] = set()
        self._pool = QThreadPool.globalInstance()
        if self._pool is None:
            self._pool = QThreadPool(self)

    @property
    def generation(self) -> int:
        return self._generation

    @property
    def pending_indices(self) -> list[int]:
        return list(self._pending)

    def cancel(self) -> None:
        self._generation += 1
        self._pending.clear()
        self._session = None
        self._claimed.clear()
        # Workers em voo terminam e são ignorados (generation); _active_workers decresce no callback.

    def claim_for_sync(self, index: int) -> None:
        """Marca índice para parse síncrono — resultado de worker em voo é ignorado."""
        self._claimed.add(index)
        self._pending = [i for i in self._pending if i != index]

    def unclaim(self, index: int) -> None:
        self._claimed.discard(index)

    def enqueue(self, session: ProjectSession, indices: list[int]) -> int:
        self._generation += 1
        self._claimed.clear()
        self._session = session
        self._pending = [i for i in indices if 0 <= i < len(session.documents)]
        self._pump()
        return self._generation

    def resume_if_needed(self) -> None:
        if self._session is not None and self._pending and self._active_workers == 0:
            self._pump()

    def _pump(self) -> None:
        if self._active_workers > 0 or self._session is None:
            return
        while self._pending:
            index = self._pending.pop(0)
            if index in self._claimed:
                continue
            slot = self._session.documents[index]
            if slot.document is not None:
                continue
            job = build_slot_parse_job(self._generation, self._session, index)
            worker = SlotParseWorker(job, self._doc_service)
            worker.signals.finished.connect(self._on_worker_finished)
            worker.signals.failed.connect(self._on_worker_failed)
            self._active_workers += 1
            self._pool.start(worker)
            return
        if self._active_workers == 0:
            self.queue_idle.emit(self._generation)

    def _on_worker_finished(self, generation: int, index: int, document: object, notice: str) -> None:
        self._active_workers = max(0, self._active_workers - 1)
        if generation != self._generation or index in self._claimed:
            self._pump()
            return
        if not isinstance(document, ReportDocument):
            self._pump()
            return
        self.slot_ready.emit(generation, index, document, notice)
        self._pump()

    def _on_worker_failed(self, generation: int, index: int, error: str) -> None:
        self._active_workers = max(0, self._active_workers - 1)
        if generation != self._generation or index in self._claimed:
            self._pump()
            return
        self.slot_failed.emit(generation, index, error)
        self._pending.clear()
        self.queue_idle.emit(generation)
