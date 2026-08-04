"""Sessão de projeto com múltiplos PDFs (aba por arquivo no workspace)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from src.core.domain.ports import ReportDocument


@dataclass
class ProjectDocumentSlot:
    """Um PDF dentro do projeto — um documento editável por aba."""

    source_pdf_path: Path
    evaluated_component: str
    document: ReportDocument | None = None


@dataclass
class ProjectSession:
    """Projeto de medição: cliente + template + N relatórios PDF."""

    client_project: str
    template_id: str = "default"
    documents: list[ProjectDocumentSlot] = field(default_factory=list)
    active_index: int = 0

    @property
    def active_slot(self) -> ProjectDocumentSlot | None:
        if not self.documents or self.active_index < 0:
            return None
        if self.active_index >= len(self.documents):
            return None
        return self.documents[self.active_index]

    @property
    def active_document(self) -> ReportDocument | None:
        slot = self.active_slot
        return slot.document if slot else None

    def set_active_index(self, index: int) -> None:
        if 0 <= index < len(self.documents):
            self.active_index = index
