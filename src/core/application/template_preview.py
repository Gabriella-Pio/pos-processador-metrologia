"""Documento sintético para preview PDF no editor de templates."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.core.domain.ports import ReportDocument, TechnicalControlInfo, VersionEntry
from src.core.domain.section_schema import is_custom_section_id, merge_saved_template_config
from src.core.parser.parser import RelatorioCalypsoDto
from src.core.parser.table_extractor import MedicaoItemDto

_TEMPLATE_GLOBAL_KEY = "_global"
_PROTECTED_SECTION_IDS = frozenset({"cabecalho", "historico_versoes"})


def split_template_content_defaults(content_defaults: dict) -> tuple[dict, dict]:
    """Separa defaults globais (`_global`) dos defaults por seção."""
    raw = {k: dict(v) for k, v in content_defaults.items() if isinstance(v, dict)}
    global_defaults = dict(raw.pop(_TEMPLATE_GLOBAL_KEY, {}))
    return raw, global_defaults


def merge_template_content_defaults(
    section_defaults: dict,
    global_defaults: dict,
) -> dict:
    merged = {sid: dict(values) for sid, values in section_defaults.items()}
    if global_defaults:
        merged[_TEMPLATE_GLOBAL_KEY] = dict(global_defaults)
    return merged


def build_template_preview_document(
    template_id: str,
    sections_config: dict,
    content_defaults: dict,
    global_defaults: dict | None = None,
) -> ReportDocument:
    """Monta ``ReportDocument`` mock para renderizar preview institucional."""
    section_defaults, stored_global = split_template_content_defaults(content_defaults)
    globals_map = {**stored_global, **(global_defaults or {})}

    client_project = globals_map.get("client_project", "Cliente Exemplo")
    evaluated_component = globals_map.get("evaluated_component", "Componente Exemplo")
    scalar = dict(globals_map.get("scalar", {}))

    dto = RelatorioCalypsoDto(
        componente=scalar.get("componente", evaluated_component),
        operador=scalar.get("operador", "Operador Metrologista"),
        maquina_mmc=scalar.get("maquina_mmc", "MMC ZEISS"),
        numero_mmc=scalar.get("numero_mmc", "001"),
        data_hora=scalar.get("data_hora", "01/01/2026 10:00"),
        software=scalar.get("software", "ZEISS CALYPSO"),
        versao_software=scalar.get("versao_software", "2024"),
        numero_medicoes_cabecalho=int(scalar.get("numero_medicoes_cabecalho", 3) or 3),
        itens_medicao=[
            MedicaoItemDto(
                caracteristica="Diâmetro externo",
                tipo="Comprimento",
                valor_medido="50,02",
                nominal="50,00",
                tol_superior="50,10",
                tol_inferior="49,90",
                desvio="+0,02",
                status="Dentro",
            ),
            MedicaoItemDto(
                caracteristica="Comprimento total",
                tipo="Comprimento",
                valor_medido="120,00",
                nominal="120,00",
                tol_superior="120,20",
                tol_inferior="119,80",
                desvio="0,00",
                status="Dentro",
            ),
        ],
    )

    enabled_ids = [
        sid
        for sid, _label, enabled in _ordered_sections(sections_config)
        if enabled and sid not in _PROTECTED_SECTION_IDS
    ]
    disabled_ids = [
        sid
        for sid, _label, enabled in _ordered_sections(sections_config)
        if not enabled and sid not in _PROTECTED_SECTION_IDS
    ]

    control = TechnicalControlInfo(
        measured_by=scalar.get("operador", "Operador Metrologista"),
        reviewed_by="Supervisor SENAI",
        approved_by="",
        role="Técnico de Laboratório",
        institutional_email="metrologia@senaigo.com.br",
    )

    custom_sections = [
        {
            "id": section_id,
            "title": sections_config[section_id].get("title", section_id),
            "custom": True,
        }
        for section_id in sections_config
        if is_custom_section_id(section_id)
    ]

    return ReportDocument(
        source_pdf_path=Path("/tmp/template_preview.pdf"),
        client_project=client_project,
        evaluated_component=evaluated_component,
        control_info=control,
        version_history=[
            VersionEntry(1, datetime.now(), control.measured_by, "Preview do template"),
        ],
        template_id=template_id,
        template_layout_override=dict(sections_config),
        section_overrides={sid: dict(values) for sid, values in section_defaults.items()},
        section_order=enabled_ids,
        deleted_section_ids=disabled_ids,
        custom_sections=custom_sections,
        raw_parsed_data=dto,
        parsed_overrides={"scalar": scalar},
    )


def build_template_sections_summary(
    sections_config: dict,
    content_defaults: dict,
    active_section_id: str | None = None,
    *,
    report_kind: str = "mmc",
) -> list[dict]:
    """Lista de seções para o sumário do editor de templates."""
    from src.core.application.interpretacao_edit import build_interpretacao_editor_fields
    from src.core.domain.report_field_registry import default_prose_values

    section_defaults, _global = split_template_content_defaults(content_defaults)
    result: list[dict] = []
    for section_id, label, enabled in _ordered_sections(sections_config):
        defaults = dict(default_prose_values(section_id, {"report_kind": report_kind}))
        defaults.update(section_defaults.get(section_id, {}))
        if section_id == "interpretacao":
            defaults = build_interpretacao_editor_fields(
                None,
                report_kind=report_kind,
                existing=defaults,
            )
        cfg = sections_config.get(section_id, {})
        result.append(
            {
                "id": section_id,
                "title": label,
                "display_title": cfg.get("title", label) if is_custom_section_id(section_id) else label,
                "enabled": enabled,
                "protected": section_id in _PROTECTED_SECTION_IDS,
                "custom": is_custom_section_id(section_id),
                "fields": defaults,
                "table_rows": defaults.get("table_rows"),
                "media_kinds": defaults.get("media_kinds"),
                "has_overrides": bool(section_defaults.get(section_id)),
                "override_keys": sorted(section_defaults.get(section_id, {}).keys()),
            }
        )
    if active_section_id:
        for section in result:
            section["active"] = section["id"] == active_section_id
    return result


def _ordered_sections(sections_config: dict) -> list[tuple[str, str, bool]]:
    merged = merge_saved_template_config(sections_config)
    order_map = {
        sid: sections_config.get(sid, {}).get("order", index)
        for index, sid in enumerate(s["id"] for s in merged)
    }
    ordered = sorted(merged, key=lambda s: order_map.get(s["id"], 999))
    return [
        (
            section["id"],
            section.get("label") or sections_config.get(section["id"], {}).get("title", section["id"]),
            sections_config.get(section["id"], {}).get("enabled", section["enabled"]),
        )
        for section in ordered
    ]


__all__ = [
    "_TEMPLATE_GLOBAL_KEY",
    "build_template_preview_document",
    "build_template_sections_summary",
    "merge_template_content_defaults",
    "split_template_content_defaults",
]
