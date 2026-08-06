"""Comandos de histórico de versões do documento."""
from __future__ import annotations

from datetime import datetime

from src.core.domain.ports import ReportDocument, VersionEntry


class VersionCommands:
    @staticmethod
    def create_entry(
        document: ReportDocument,
        responsible_name: str,
        description: str,
    ) -> VersionEntry:
        existing = document.version_history
        next_number = max((entry.version_number for entry in existing), default=0) + 1
        return VersionEntry(
            version_number=next_number,
            timestamp=datetime.now(),
            responsible_name=responsible_name,
            description=description,
        )
