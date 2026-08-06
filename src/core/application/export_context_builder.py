"""Montagem do contexto de exportação PDF a partir de ``ReportDocument``."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.domain.parsed_overrides import build_effective_dto, build_prose_context
from src.core.domain.placeholder_utils import build_placeholder_context
from src.core.domain.ports import ReportDocument
from src.core.domain.report_field_registry import PROSE_TEMPLATES, merge_section_prose
from src.core.domain.section_schema import is_tomography_template
from src.core.domain.table_row_registry import INTRODUCAO_BLOCK_TITLES, SECTION_HEADING_DEFAULTS


@dataclass
class ExportContext:
    effective_dto: Any
    section_prose: dict[str, dict]
    placeholder_context: dict
    table_rows: dict[str, list]
    fotos_secoes: dict[str, list[str]]
    versao_relatorio: str
    controle_tecnico: dict
    historico_versoes: list[dict]
    report_kind: str
    foto_captions: dict[str, str]
    anexo_pdfs: list[str]


def build_export_context(document: ReportDocument) -> ExportContext:
    effective_dto = build_effective_dto(document.raw_parsed_data, document.parsed_overrides)
    report_kind = resolve_report_kind(document)
    return ExportContext(
        effective_dto=effective_dto,
        section_prose=build_section_prose(document, effective_dto, report_kind),
        placeholder_context=build_placeholder_context(effective_dto, document),
        table_rows=build_table_rows(document, report_kind),
        fotos_secoes=build_fotos_secoes(document),
        versao_relatorio=resolve_versao_atual(document),
        controle_tecnico=build_controle_tecnico(document),
        historico_versoes=build_historico_versoes(document),
        report_kind=report_kind,
        foto_captions=build_foto_captions(document),
        anexo_pdfs=build_anexo_pdfs(document),
    )


def resolve_report_kind(document: ReportDocument) -> str:
    if is_tomography_template(document.template_id) or document.source_kind == "insp_ect":
        return "tomografia"
    return "mmc"


def build_anexo_pdfs(document: ReportDocument) -> list[str]:
    paths = list(document.attachment_pdf_paths or [])
    if not paths and document.source_pdf_path:
        paths = [document.source_pdf_path]
    seen: set[str] = set()
    result: list[str] = []
    for path in paths:
        key = str(Path(path).resolve()) if Path(path).exists() else str(path)
        if key in seen:
            continue
        seen.add(key)
        result.append(str(path))
    return result


def build_fotos_secoes(document: ReportDocument) -> dict[str, list[str]]:
    """Agrupa ``ReportImage`` no formato ``{"secao_id": [caminho, ...]}``."""
    fotos_por_secao: dict[str, list[str]] = {}
    for imagem in document.images:
        fotos_por_secao.setdefault(imagem.section_id, []).append(str(imagem.image_path))
    return fotos_por_secao


def build_foto_captions(document: ReportDocument) -> dict[str, str]:
    captions: dict[str, str] = {}
    for imagem in document.images:
        if imagem.caption:
            captions[str(imagem.image_path)] = imagem.caption
    return captions


def resolve_versao_atual(document: ReportDocument) -> str:
    if document.version_history:
        return f"v{document.version_history[-1].version_number}"
    return "v1.0"


def build_controle_tecnico(document: ReportDocument) -> dict:
    info = document.control_info
    if info is None:
        return {}
    return {
        "measured_by": info.measured_by,
        "reviewed_by": info.reviewed_by,
        "approved_by": info.approved_by,
        "role": info.role,
        "institutional_email": info.institutional_email,
        "timestamp_str": info.timestamp.strftime("%d/%m/%Y %H:%M"),
    }


def build_historico_versoes(document: ReportDocument) -> list[dict]:
    return [
        {
            "version_number": entrada.version_number,
            "timestamp_str": entrada.timestamp.strftime("%d/%m/%Y %H:%M"),
            "responsible_name": entrada.responsible_name,
            "description": entrada.description,
        }
        for entrada in document.version_history
    ]


def build_section_prose(
    document: ReportDocument,
    effective_dto: Any,
    report_kind: str,
) -> dict[str, dict]:
    ctx = build_prose_context(effective_dto, document)
    ctx["report_kind"] = report_kind
    result: dict[str, dict] = {}
    section_ids = set(PROSE_TEMPLATES.keys()) | set(document.section_overrides.keys()) | set(SECTION_HEADING_DEFAULTS.keys())
    if report_kind == "tomografia":
        from src.core.domain.tomo_template_defaults import TOMO_PROSE_DEFAULTS

        section_ids |= set(TOMO_PROSE_DEFAULTS.keys())
    for section_id in section_ids:
        overrides = dict(document.section_overrides.get(section_id, {}))
        merged = merge_section_prose(section_id, overrides, ctx)
        merged["section_title"] = overrides.get(
            "section_title", SECTION_HEADING_DEFAULTS.get(section_id, merged.get("section_title", ""))
        )
        if section_id == "introducao":
            for key, default in INTRODUCAO_BLOCK_TITLES.items():
                merged.setdefault(key, overrides.get(key, default))
            if not str(merged.get("nota") or "").strip():
                merged["nota"] = str(
                    overrides.get("nota")
                    or overrides.get("intro")
                    or overrides.get("nota_deteccao")
                    or merged.get("intro")
                    or merged.get("nota_deteccao")
                    or ""
                )
            for row in overrides.get("table_rows") or []:
                row_id = row.get("id", "")
                if row_id in ("objetivo", "escopo", "referencia"):
                    if not str(merged.get(row_id) or "").strip() and row.get("value"):
                        merged[row_id] = str(row.get("value") or "")
                    title_key = f"title_{row_id}"
                    if row.get("label") and not str(overrides.get(title_key) or "").strip():
                        merged[title_key] = str(row.get("label") or "")
        result[section_id] = merged
    return result


def build_table_rows(document: ReportDocument, report_kind: str) -> dict[str, list]:
    from src.core.domain.table_row_registry import (
        apply_control_info_to_rows,
        default_tomo_identificacao_rows,
        merge_table_rows,
        resolve_introducao_table_rows,
    )

    result: dict[str, list] = {}

    stored_ident = document.section_overrides.get("identificacao", {}).get("table_rows")
    if report_kind == "tomografia" and not stored_ident:
        result["identificacao"] = default_tomo_identificacao_rows()
    else:
        result["identificacao"] = merge_table_rows("identificacao", stored_ident)

    stored_ctrl = document.section_overrides.get("controle_tecnico", {}).get("table_rows")
    ctrl_rows = merge_table_rows("controle_tecnico", stored_ctrl)
    if not stored_ctrl and document.control_info is not None:
        ctrl_rows = apply_control_info_to_rows(ctrl_rows, document.control_info)
    result["controle_tecnico"] = ctrl_rows

    intro_overrides = document.section_overrides.get("introducao", {})
    result["introducao"] = resolve_introducao_table_rows(
        intro_overrides,
        report_kind=report_kind,
    )
    return result
