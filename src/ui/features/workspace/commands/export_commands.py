"""Comandos de exportação de PDF do workspace."""
from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass
from pathlib import Path

from collections.abc import Callable

from src.core.application.export_report import validate_export
from src.core.domain.ports import RecentFilesRepository, ReportDocument, ReportExporter
from src.core.domain.project_session import ProjectSession

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExportOutcome:
    success: bool
    path: Path | None = None
    error_title: str = ""
    error_message: str = ""
    error_details: str = ""


class ExportCommands:
    def __init__(
        self,
        exporter: ReportExporter,
        recent_files_repo: RecentFilesRepository | None = None,
    ) -> None:
        self._exporter = exporter
        self._recent_files_repo = recent_files_repo

    def export_document(self, document: ReportDocument | None, output_path: Path) -> ExportOutcome:
        if document is None:
            return ExportOutcome(
                success=False,
                error_title="Nenhum documento aberto",
                error_message="Importe um relatório antes de exportar.",
            )
        issues = validate_export(document)
        errors = [i for i in issues if i.level == "error"]
        if errors:
            return ExportOutcome(
                success=False,
                error_title="Exportação bloqueada",
                error_message=errors[0].message,
            )
        try:
            final_path = self._exporter.export(document, output_path)
        except Exception:
            logger.exception("Falha ao exportar o PDF para: %s", output_path)
            if output_path.exists():
                try:
                    output_path.unlink()
                except OSError:
                    pass
            return ExportOutcome(
                success=False,
                error_title="Falha ao exportar o PDF",
                error_message="Ocorreu um erro ao gerar o documento final.",
                error_details=traceback.format_exc(),
            )

        if self._recent_files_repo is not None:
            try:
                self._recent_files_repo.save(document, str(final_path))
            except Exception:
                logger.exception("Falha ao registrar %s no histórico", final_path)

        return ExportOutcome(success=True, path=final_path)

    def export_all_documents(
        self,
        session: ProjectSession | None,
        output_dir: Path,
        *,
        switch_document: Callable[[int], None],
        export_document: Callable[[Path], None],
    ) -> list[Path]:
        if session is None or not session.documents:
            return []
        output_dir.mkdir(parents=True, exist_ok=True)
        exported: list[Path] = []
        original_index = session.active_index
        for index, slot in enumerate(session.documents):
            if slot.document is None:
                continue
            switch_document(index)
            safe_name = slot.evaluated_component.replace(" ", "_")[:40]
            out_path = output_dir / f"{safe_name}_{index + 1}.pdf"
            export_document(out_path)
            exported.append(out_path)
        switch_document(original_index)
        return exported
