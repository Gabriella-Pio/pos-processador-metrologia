"""Snapshot de versão de projeto — payload completo (Fase 4)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class VersionSnapshot:
    project_id: str
    version_number: int
    responsible: str
    description: str
    snapshot_json: str
    created_at: datetime | None = None
    id: int | None = None
