"""Adapter SQLite para histórico de versões por documento."""
from __future__ import annotations

from datetime import datetime

from src.core.infrastructure.database import DatabaseManager
from src.core.domain.ports import VersionEntry, VersionHistoryRepository


class SQLiteVersionHistoryAdapter(VersionHistoryRepository):
    _FORMATO_DATA = "%d/%m/%Y %H:%M:%S"

    def __init__(self, db_manager: DatabaseManager) -> None:
        self._db = db_manager

    def list_for_document(
        self,
        source_pdf_path: str,
        client_project: str,
        componente: str,
    ) -> list[VersionEntry]:
        rows = self._db.listar_versoes(source_pdf_path, client_project, componente)
        entries: list[VersionEntry] = []
        for version_number, data_hora, responsavel, descricao in rows:
            entries.append(
                VersionEntry(
                    version_number=int(version_number),
                    timestamp=self._parse_data(data_hora),
                    responsible_name=responsavel,
                    description=descricao,
                )
            )
        return entries

    def append(
        self,
        source_pdf_path: str,
        client_project: str,
        componente: str,
        entry: VersionEntry,
    ) -> None:
        self._db.salvar_versao(
            source_pdf_path=source_pdf_path,
            client_project=client_project,
            componente=componente,
            version_number=entry.version_number,
            data_hora=entry.timestamp.strftime(self._FORMATO_DATA),
            responsavel=entry.responsible_name,
            descricao=entry.description,
        )

    def _parse_data(self, value: str) -> datetime:
        for fmt in (self._FORMATO_DATA, "%d/%m/%Y %H:%M"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return datetime.now()
