"""
Estado de sessão centralizado da aplicação.
"""
from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal

from src.core.domain.project_session import ProjectSession
from src.core.domain.ports import ReportDocument


class AppState(QObject):
    document_changed = pyqtSignal(object)
    project_changed = pyqtSignal(object)
    images_changed = pyqtSignal()
    version_added = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._active_document: ReportDocument | None = None
        self._project_session: ProjectSession | None = None

    @property
    def active_document(self) -> ReportDocument | None:
        return self._active_document

    @property
    def project_session(self) -> ProjectSession | None:
        return self._project_session

    def set_project_session(self, session: ProjectSession | None) -> None:
        self._project_session = session
        self.project_changed.emit(session)
        if session and session.active_document:
            self.set_active_document(session.active_document)
        elif session is None:
            self.set_active_document(None)

    def set_active_document(self, document: ReportDocument | None) -> None:
        self._active_document = document
        if self._project_session and document is not None:
            slot = self._project_session.active_slot
            if slot is not None:
                slot.document = document
        self.document_changed.emit(document)

    def notify_images_changed(self) -> None:
        self.images_changed.emit()

    def register_version(self, entry) -> None:
        if self._active_document is None:
            return
        self._active_document.version_history.append(entry)
        self.version_added.emit()

    def clear(self) -> None:
        self._project_session = None
        self.set_active_document(None)
