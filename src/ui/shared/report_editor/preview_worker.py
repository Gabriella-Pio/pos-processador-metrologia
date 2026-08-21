"""Preview assíncrono com debounce — compartilhado entre workspace e template editor."""
from __future__ import annotations

import logging
import traceback
from collections.abc import Callable

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, QTimer, pyqtSignal, pyqtSlot

from src.core.domain.ports import ReportDocument
from src.ui.shared.report_editor.preview_constants import raster_zoom

logger = logging.getLogger(__name__)

PREVIEW_DEBOUNCE_MS = 600
PREVIEW_INDICATOR_DELAY_MS = 300
PREVIEW_IMAGE_DEBOUNCE_MS = 1200


def build_preview_metadata(exporter) -> dict:
    sections = dict(getattr(exporter, "_last_section_anchor_map", {}) or {})
    photo_anchors = list(getattr(exporter, "_last_photo_anchors", []) or [])
    return {"sections": sections, "photo_anchors": photo_anchors}


class PreviewWorkerSignals(QObject):
    finished = pyqtSignal(int, list, dict)
    failed = pyqtSignal(int, str)


class PreviewWorker(QRunnable):
    def __init__(
        self,
        generation: int,
        document: ReportDocument,
        preview_service,
        zoom: float | None = None,
    ) -> None:
        super().__init__()
        self._generation = generation
        self._document = document
        self._preview_service = preview_service
        self._zoom = zoom
        self.signals = PreviewWorkerSignals()

    @pyqtSlot()
    def run(self) -> None:
        try:
            pages = self._preview_service.render_pages(self._document, self._zoom)
            exporter = self._preview_service._exporter
            metadata = build_preview_metadata(exporter)
            self.signals.finished.emit(self._generation, pages, metadata)
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
        preview_service,
        *,
        debounce_ms: int = PREVIEW_DEBOUNCE_MS,
        indicator_delay_ms: int = PREVIEW_INDICATOR_DELAY_MS,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._preview_service = preview_service
        self._default_debounce_ms = debounce_ms
        self._indicator_delay_ms = indicator_delay_ms
        self._generation = 0
        self._generating = False
        self._document_getter: Callable[[], ReportDocument | None] | None = None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._run)
        self._indicator_timer = QTimer(self)
        self._indicator_timer.setSingleShot(True)
        self._indicator_timer.timeout.connect(self._maybe_show_generating_indicator)

    def set_document_getter(self, getter: Callable[[], ReportDocument | None]) -> None:
        self._document_getter = getter

    def schedule(self, *, debounce_ms: int | None = None) -> None:
        interval = self._default_debounce_ms if debounce_ms is None else debounce_ms
        self._timer.setInterval(interval)
        self._timer.start()
        if not self._generating:
            self._indicator_timer.start(self._indicator_delay_ms)

    def _maybe_show_generating_indicator(self) -> None:
        if self._timer.isActive():
            self._set_generating(True)

    def _run(self) -> None:
        self._indicator_timer.stop()
        if self._document_getter is None:
            self._set_generating(False)
            return
        document = self._document_getter()
        if document is None:
            self._set_generating(False)
            return
        self._set_generating(True)
        self._generation += 1
        generation = self._generation
        # A densidade da tela é lida aqui, na thread da UI, e não no worker.
        worker = PreviewWorker(generation, document, self._preview_service, raster_zoom())
        worker.signals.finished.connect(self._on_finished)
        worker.signals.failed.connect(self._on_failed)
        QThreadPool.globalInstance().start(worker)

    def _set_generating(self, active: bool) -> None:
        if self._generating == active:
            return
        self._generating = active
        self.generating.emit(active)

    def _clear_generating_if_idle(self) -> None:
        if self._timer.isActive():
            return
        self._set_generating(False)

    def _on_finished(self, generation: int, pages: list[bytes], anchor_map: dict) -> None:
        if generation != self._generation:
            return
        self._clear_generating_if_idle()
        self.finished.emit(pages, anchor_map)

    def _on_failed(self, generation: int, details: str) -> None:
        if generation != self._generation:
            return
        self._clear_generating_if_idle()
        self.failed.emit(details)
