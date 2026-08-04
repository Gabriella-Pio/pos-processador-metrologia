"""Validação pré-exportação do relatório."""
from __future__ import annotations

from dataclasses import dataclass

from src.core.domain.parsed_overrides import build_effective_dto
from src.core.domain.ports import ReportDocument


@dataclass
class ExportIssue:
    level: str  # "warning" | "error"
    message: str


def validate_for_export(document: ReportDocument) -> list[ExportIssue]:
    issues: list[ExportIssue] = []
    if not document.client_project.strip():
        issues.append(ExportIssue("error", "Cliente/projeto não informado."))
    if not document.evaluated_component.strip():
        issues.append(ExportIssue("error", "Componente avaliado não informado."))

    effective = build_effective_dto(document.raw_parsed_data, document.parsed_overrides)
    if not getattr(effective, "operador", "").strip():
        issues.append(ExportIssue("warning", "Operador não informado."))

    sections_with_photos = {"identificacao", "resultados", "grafica"}
    for section_id in sections_with_photos:
        has_media_block = section_id in document.section_overrides or section_id in {
            img.section_id for img in document.images
        }
        if has_media_block and not any(img.section_id == section_id for img in document.images):
            issues.append(ExportIssue(
                "warning",
                f"Seção “{section_id}” sem fotografias associadas.",
            ))

    for item in getattr(effective, "itens_medicao", []) or []:
        status = getattr(item, "status", "")
        if status and status.lower() not in ("dentro", "fora", "ok", "nok"):
            issues.append(ExportIssue(
                "warning",
                f"Status de medição inconsistente: {status}",
            ))
            break

    return issues
