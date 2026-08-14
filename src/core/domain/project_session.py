"""Sessão de projeto com múltiplos PDFs (aba por arquivo no workspace)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from src.core.domain.ports import ReportDocument, ReportImage

ReportMode = Literal["mmc_only", "tomo_only", "mixed"]


@dataclass
class ProjectDocumentSlot:
    """Um PDF dentro do projeto — um documento editável por aba."""

    source_pdf_path: Path
    evaluated_component: str
    document: ReportDocument | None = None
    source_kind: str = "calypso"
    template_id: str | None = None


@dataclass
class ProjectSession:
    """Projeto de medição: cliente + template + N relatórios PDF."""

    client_project: str
    template_id: str = "default"
    report_mode: ReportMode = "mixed"
    documents: list[ProjectDocumentSlot] = field(default_factory=list)
    active_index: int = 0
    project_id: str | None = None
    display_name: str = ""
    # Seções desativadas no PDF unificado (estatístico/híbrido), independentes das peças.
    unified_deleted_section_ids: list[str] = field(default_factory=list)
    # Overrides de layout/conteúdo do PDF unificado (gráficos, media_kinds, etc.).
    unified_section_overrides: dict[str, dict] = field(default_factory=dict)
    # Fotos do relatório consolidado (modo PDF único) — independentes das abas.
    unified_images: list[ReportImage] = field(default_factory=list)
    # True após seed/edição no unificado: lista vazia = sem fotos (não reimportar das peças).
    unified_images_ready: bool = False

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

    def effective_template_id(self, slot: ProjectDocumentSlot) -> str:
        if self.report_mode == "mixed" and slot.template_id:
            return slot.template_id
        if self.report_mode == "tomo_only":
            return slot.template_id or "tomografia"
        return self.template_id or "default"
