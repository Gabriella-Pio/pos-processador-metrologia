"""Preview assíncrono com debounce — compartilhado entre workspace e template editor."""
from __future__ import annotations

import logging
import traceback
from collections.abc import Callable

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, QTimer, pyqtSignal, pyqtSlot

from src.core.domain.ports import ReportDocument
from src.ui.features.workspace.services.preview_service import PreviewService

logger = logging.getLogger(__name__)

PREVIEW_DEBOUNCE_MS = 600


class PreviewWorkerSignals(QObject):
    finished = pyqtSignal(int, list, dict)
    failed = pyqtSignal(int, str)


class PreviewWorker(QRunnable):
    def __init__(
        self,
        generation: int,
        document: ReportDocument,
        preview_service: PreviewService,
    ) -> None:
        super().__init__()
        self._generation = generation
        self._document = document
        self._preview_service = preview_service
        self.signals = PreviewWorkerSignals()

    @pyqtSlot()
    def run(self) -> None:
        try:
            pages = self._preview_service.render_pages(self._document)
            anchor_map: dict = {}
            exporter = self._preview_service._exporter
            if hasattr(exporter, "_last_section_anchor_map"):
                anchor_map = dict(getattr(exporter, "_last_section_anchor_map", {}))
            self.signals.finished.emit(self._generation, pages, anchor_map)
        except Exception:
            logger.exception("Falha ao gerar preview em background")
            self.signals.failed.emit(self._generation, traceback.format_exc())


class DebouncedPreviewRunner(QObject):
    """Timer de debounce + geração monotônica para renderização de preview PDF."""

    generating = pyqtSignal(bool)
    finished = pyqtSignal(list, dict)
    failed = pyqtSignal(str)

    def __init__(
        self,
        preview_service: PreviewService,
        *,
        debounce_ms: int = PREVIEW_DEBOUNCE_MS,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._preview_service = preview_service
        self._generation = 0
        self._document_getter: Callable[[], ReportDocument | None] | None = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(debounce_ms)
        self._timer.timeout.connect(self._run)

    def set_document_getter(self, getter: Callable[[], ReportDocument | None]) -> None:
        self._document_getter = getter

    def schedule(self) -> None:
        self.generating.emit(True)
        self._timer.start()

    def _run(self) -> None:
        if self._document_getter is None:
            self.generating.emit(False)
            return
        document = self._document_getter()
        if document is None:
            self.generating.emit(False)
            return
        self._generation += 1
        generation = self._generation
        worker = PreviewWorker(generation, document, self._preview_service)
        worker.signals.finished.connect(self._on_finished)
        worker.signals.failed.connect(self._on_failed)
        QThreadPool.globalInstance().start(worker)

    def _on_finished(self, generation: int, pages: list[bytes], anchor_map: dict) -> None:
        if generation != self._generation:
            return
        self.generating.emit(False)
        self.finished.emit(pages, anchor_map)

    def _on_failed(self, generation: int, details: str) -> None:
        if generation != self._generation:
            return
        self.generating.emit(False)
        self.failed.emit(details)
