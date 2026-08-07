"""Metadados persistidos de um projeto multi-PDF em edição."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from src.core.domain.project_session import ReportMode


@dataclass
class ProjectSlotSnapshot:
    """Metadados de um slot — sem o ``ReportDocument`` em memória."""

    source_pdf_path: str
    evaluated_component: str
    source_kind: str = "calypso"
    template_id: str | None = None


@dataclass
class ProjectWorkspace:
    """Projeto salvo no banco — lista de PDFs ZEISS + índice ativo."""

    id: str
    client_project: str
    template_id: str = "default"
    report_mode: ReportMode = "mixed"
    slots: list[ProjectSlotSnapshot] = field(default_factory=list)
    active_index: int = 0
    display_name: str = ""
    updated_at: datetime | None = None
