"""Montagem do contexto de exportação PDF a partir de ``ReportDocument``."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.domain.parsed_overrides import build_effective_dto, build_prose_context
from src.core.domain.image_workspace import (
    build_foto_edits_index,
    resolve_image_id,
    serialize_annotation,
    serialize_crop,
)
from src.core.domain.field_definitions import effective_media_kinds
from src.core.domain.placeholder_utils import build_placeholder_context
from src.core.domain.ports import ReportDocument, VersionEntry
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
    foto_edits: dict[str, dict]
    anexo_pdfs: list[str]
    section_media_settings: dict[str, dict]


def build_section_media_settings(document: ReportDocument) -> dict[str, dict]:
    """media_kinds e gráficos desativados por seção."""
    settings: dict[str, dict] = {}
    section_ids = set(document.section_overrides.keys())
    from src.core.domain.chart_figure_defs import CHART_FIGURES_BY_SECTION

    section_ids |= set(CHART_FIGURES_BY_SECTION.keys())
    for section_id in section_ids:
        overrides = document.section_overrides.get(section_id, {})
        settings[section_id] = {
            "media_kinds": effective_media_kinds(section_id, overrides),
            "disabled_chart_ids": list(overrides.get("disabled_chart_ids") or []),
        }
    return settings


def build_export_context(document: ReportDocument) -> ExportContext:
    report_kind = resolve_report_kind(document)
    if report_kind == "estatistico":
        effective_dto = document.raw_parsed_data
    else:
        effective_dto = build_effective_dto(document.raw_parsed_data, document.parsed_overrides)
    placeholder_context = _build_placeholder_context_for_kind(
        document, effective_dto, report_kind
    )
    return ExportContext(
        effective_dto=effective_dto,
        section_prose=build_section_prose(document, effective_dto, report_kind),
        placeholder_context=placeholder_context,
        table_rows=build_table_rows(document, report_kind),
        fotos_secoes=build_fotos_secoes(document),
        versao_relatorio=resolve_versao_atual(document),
        controle_tecnico=build_controle_tecnico(document),
        historico_versoes=build_historico_versoes(document),
        report_kind=report_kind,
        foto_captions=build_foto_captions(document),
        foto_edits=build_foto_edits(document),
        anexo_pdfs=build_anexo_pdfs(document),
        section_media_settings=build_section_media_settings(document),
    )


def _build_placeholder_context_for_kind(
    document: ReportDocument,
    effective_dto: Any,
    report_kind: str,
) -> dict:
    if report_kind == "estatistico":
        n_pecas = len(getattr(effective_dto, "piece_labels", []) or [])
        return {
            "componente": document.evaluated_component,
            "cliente": document.client_project,
            "n_pecas": str(n_pecas),
            "numero_medicoes": str(getattr(effective_dto, "numero_medicoes_cabecalho", 0) or 0),
            "numero_medicoes_cabecalho": str(
                getattr(effective_dto, "numero_medicoes_cabecalho", 0) or 0
            ),
            "maquina_mmc": str(getattr(effective_dto, "maquina_mmc", "") or ""),
            "operador": str(getattr(effective_dto, "operador", "") or ""),
            "total_fora": str(
                sum(s.fora_count for s in getattr(effective_dto, "series", []) or [])
            ),
        }
    return build_placeholder_context(effective_dto, document)


def resolve_report_kind(document: ReportDocument) -> str:
    from src.core.domain.section_schema import (
        is_falha_template,
        is_mixed_template,
        is_statistical_template,
    )

    if is_statistical_template(document.template_id):
        return "estatistico"
    if is_mixed_template(document.template_id):
        return "mixed"
    if is_falha_template(document.template_id):
        return "falha"
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


def build_foto_edits(document: ReportDocument) -> dict[str, dict]:
    """Metadados de crop/marcações por path de imagem para o generator."""
    return build_foto_edits_index(document)


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


def version_entries_to_historico_rows(entries: list[VersionEntry]) -> list[dict]:
    return [
        {
            "version_number": entrada.version_number,
            "timestamp_str": entrada.timestamp.strftime("%d/%m/%Y %H:%M"),
            "responsible_name": entrada.responsible_name,
            "description": entrada.description,
        }
        for entrada in entries
    ]


def build_historico_versoes(
    document: ReportDocument,
    *,
    version_entries: list[VersionEntry] | None = None,
) -> list[dict]:
    entries = version_entries if version_entries is not None else document.version_history
    return version_entries_to_historico_rows(entries)


def build_section_prose(
    document: ReportDocument,
    effective_dto: Any,
    report_kind: str,
) -> dict[str, dict]:
    ctx = build_prose_context(effective_dto, document)
    ctx["report_kind"] = report_kind
    result: dict[str, dict] = {}
    section_ids = set(PROSE_TEMPLATES.keys()) | set(document.section_overrides.keys()) | set(SECTION_HEADING_DEFAULTS.keys())
    section_ids |= {s["id"] for s in document.custom_sections if s.get("id")}
    if report_kind == "tomografia":
        from src.core.domain.tomo_template_defaults import TOMO_PROSE_DEFAULTS

        section_ids |= set(TOMO_PROSE_DEFAULTS.keys())
    if report_kind == "falha":
        from src.core.domain.falha_template_defaults import FALHA_PROSE_DEFAULTS

        section_ids |= set(FALHA_PROSE_DEFAULTS.keys())
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
        if section_id == "resultados" and not str(overrides.get("resumo") or "").strip():
            from src.core.domain.measurement_interpretation import build_dimensional_summary

            merged["resumo"] = build_dimensional_summary(
                getattr(effective_dto, "itens_medicao", []) or []
            )
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

    from src.core.domain.table_row_merge import merge_with_defaults
    from src.core.domain.table_row_specs import (
        default_falha_identificacao_rows,
        default_table_rows,
    )

    stored_ident = document.section_overrides.get("identificacao", {}).get("table_rows")
    if report_kind == "tomografia" and not stored_ident:
        result["identificacao"] = default_tomo_identificacao_rows()
    elif report_kind == "falha" and not stored_ident:
        result["identificacao"] = default_falha_identificacao_rows()
    elif report_kind == "estatistico" and stored_ident:
        # Só as linhas do export unificado — não anexar defaults MMC vazios.
        result["identificacao"] = merge_with_defaults(
            default_table_rows("identificacao"),
            stored_ident,
            append_missing=False,
        )
    else:
        result["identificacao"] = merge_table_rows("identificacao", stored_ident)

    stored_ctrl = document.section_overrides.get("controle_tecnico", {}).get("table_rows")
    ctrl_rows = merge_table_rows("controle_tecnico", stored_ctrl)
    if not stored_ctrl and document.control_info is not None:
        ctrl_rows = apply_control_info_to_rows(ctrl_rows, document.control_info)
    result["controle_tecnico"] = ctrl_rows

    intro_overrides = document.section_overrides.get("introducao", {})
    if report_kind == "estatistico":
        from src.core.application.statistical_aggregator import (
            build_estatistico_introducao_metric_rows,
        )

        batch = document.raw_parsed_data
        if batch is not None and getattr(batch, "series", None) is not None:
            defaults = build_estatistico_introducao_metric_rows(batch)
            stored = intro_overrides.get("table_rows")
            if stored:
                # Preferir ordem/valores recalculados; rótulos customizados do usuário
                # são preservados quando o id coincide.
                by_stored = {str(r.get("id") or ""): r for r in stored if r.get("id")}
                merged: list[dict[str, str]] = []
                for row in defaults:
                    custom = by_stored.get(row["id"])
                    if custom and str(custom.get("label") or "").strip():
                        item = dict(row)
                        item["label"] = str(custom["label"])
                        merged.append(item)
                    else:
                        merged.append(dict(row))
                result["introducao"] = merged
            else:
                result["introducao"] = defaults
        else:
            result["introducao"] = resolve_introducao_table_rows(
                intro_overrides,
                report_kind=report_kind,
            )
    elif report_kind == "mixed" and intro_overrides.get("table_rows"):
        # Cards montados no unificado (métodos CMM / O-inspect / Bosello).
        result["introducao"] = [
            {
                "id": str(row.get("id") or ""),
                "label": str(row.get("label") or ""),
                "value": str(row.get("value") or ""),
            }
            for row in intro_overrides["table_rows"]
            if str(row.get("id") or "") not in {"objetivo", "escopo", "referencia"}
        ]
    else:
        result["introducao"] = resolve_introducao_table_rows(
            intro_overrides,
            report_kind=report_kind,
        )

    stored_discussao = document.section_overrides.get("discussao_falha", {}).get("table_rows")
    if report_kind == "falha" or stored_discussao:
        result["discussao_falha"] = merge_table_rows("discussao_falha", stored_discussao)

    # Resumos estatísticos editados no workspace unificado.
    for section_id, overrides in document.section_overrides.items():
        if not (
            section_id.startswith("estat_resumo_")
            or section_id.startswith("estat_detalhe_")
        ):
            continue
        stored = overrides.get("table_rows")
        if stored:
            result[section_id] = [
                {
                    "id": str(row.get("id") or ""),
                    "label": str(row.get("label") or ""),
                    **{
                        key: str(row.get(key) or "")
                        for key in (
                            "nominal", "limits", "n", "mean", "stdev",
                            "minimum", "maximum", "fora", "value",
                        )
                        if key in row
                    },
                }
                for row in stored
                if isinstance(row, dict)
            ]

    for custom in document.custom_sections:
        section_id = custom.get("id", "")
        if not section_id:
            continue
        stored = document.section_overrides.get(section_id, {}).get("table_rows")
        if stored:
            result[section_id] = merge_table_rows(section_id, stored)
    return result
