"""Persistência de sessão de edição."""
from __future__ import annotations

from src.core.application.bosello_image_import import (
    ensure_bosello_capture_library,
    prune_bosello_logo_images,
    refresh_bosello_auto_images_if_needed,
)
from src.core.domain.pdf_source import is_usable_source_pdf
from src.core.domain.ports import ReportDocument, WorkspaceSessionPort


def save_workspace_session(repo: WorkspaceSessionPort, document: ReportDocument) -> None:
    repo.save(document)


def load_workspace_session(repo: WorkspaceSessionPort, document: ReportDocument) -> bool:
    loaded = repo.load(document)
    if loaded:
        prune_bosello_logo_images(document)
        if is_usable_source_pdf(document.source_pdf_path) and not document.bosello_captured_paths:
            ensure_bosello_capture_library(document, document.source_pdf_path)
        refresh_bosello_auto_images_if_needed(document)
    return loaded
