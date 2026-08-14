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

    from src.core.domain.section_schema import (
        is_falha_template,
        is_mixed_template,
        is_statistical_template,
    )

    if is_statistical_template(document.template_id):
        batch = document.raw_parsed_data
        series = getattr(batch, "series", None) or []
        labels = getattr(batch, "piece_labels", None) or []
        if len(labels) < 2:
            issues.append(ExportIssue("error", "Relatório estatístico exige pelo menos duas peças."))
        if not series:
            issues.append(
                ExportIssue("error", "Nenhuma característica comum encontrada no lote.")
            )
        return issues

    if is_falha_template(document.template_id):
        has_optica = any(img.section_id == "inspecao_optica" for img in document.images)
        has_tomo = any(img.section_id == "tomografia" for img in document.images)
        if not has_optica and not has_tomo:
            issues.append(
                ExportIssue(
                    "error",
                    "Análise de falha exige ao menos uma foto em Inspeção óptica "
                    "ou Tomografia.",
                )
            )
        return issues

    if is_mixed_template(document.template_id):
        if not any(img.section_id == "tomografia" for img in document.images):
            issues.append(
                ExportIssue(
                    "error",
                    "Relatório híbrido sem capturas Bosello na seção Tomografia.",
                )
            )
        if document.raw_parsed_data is None:
            issues.append(ExportIssue("error", "Dados dimensionais CALYPSO ausentes."))
        return issues

    effective = build_effective_dto(document.raw_parsed_data, document.parsed_overrides)
    if not getattr(effective, "operador", "").strip():
        issues.append(ExportIssue("warning", "Operador não informado."))

    # Só alerta falta de foto se a seção realmente tiver imagens esperadas
    # (já associadas) ou media_kinds explícito pedindo photos — prosa sozinha não conta.
    photo_sections = {
        "identificacao",
        "resultados",
        "grafica",
        "tomografia",
        "registro_componente",
        "inspecao_optica",
    }
    for section_id in photo_sections:
        overrides = document.section_overrides.get(section_id, {})
        media_kinds = overrides.get("media_kinds")
        wants_photos = (
            (isinstance(media_kinds, list) and "photos" in media_kinds)
            or any(img.section_id == section_id for img in document.images)
        )
        if not wants_photos:
            continue
        if not any(img.section_id == section_id for img in document.images):
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
