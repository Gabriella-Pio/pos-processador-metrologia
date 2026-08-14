"""Monta o sumário de seções a partir do documento e do exportador."""
from __future__ import annotations

from src.core.application.export_context_builder import build_table_rows, resolve_report_kind
from src.core.application.statistical_aggregator import (
    build_estat_section_editor_rows,
    tipo_from_estat_section_id,
)
from src.core.domain.chart_figure_defs import enabled_chart_count, section_has_graphics
from src.core.domain.parsed_overrides import (
    build_effective_dto,
    build_prose_context,
    is_itens_overridden,
)
from src.core.domain.ports import ReportDocument, ReportExporter
from src.core.domain.report_field_registry import (
    default_prose_values,
    effective_media_kinds,
    get_global_fields_for_section,
    section_has_overrides,
)
from src.core.domain.section_numbering import strip_number_prefix
from src.core.domain.section_schema import PROTECTED_SECTION_IDS
from src.core.domain.table_row_registry import (
    SECTION_HEADING_DEFAULTS,
    TABLE_SECTIONS,
    apply_control_info_to_rows,
    merge_table_rows,
)
from src.ui.features.workspace.models.section_summary import SectionSummaryItem


def _is_estat_table_section(section_id: str) -> bool:
    return bool(tipo_from_estat_section_id(section_id))


_IDENT_LIKE_ROW_IDS = frozenset({
    "client_project",
    "evaluated_component",
    "cliente",
    "componente",
    "n_pecas",
    "maquina",
    "maquina_mmc",
    "numero_mmc",
    "operador",
    "software",
    "data_hora",
})


def _looks_like_identificacao_rows(rows: list | None) -> bool:
    if not rows:
        return False
    ids = {str(row.get("id") or "") for row in rows}
    return bool(ids & _IDENT_LIKE_ROW_IDS)


class SectionSummaryPresenter:
    def __init__(self, exporter: ReportExporter) -> None:
        self._exporter = exporter

    def build(self, document: ReportDocument) -> list[SectionSummaryItem]:
        try:
            secoes = self._exporter.list_sections(document)
        except Exception:
            return []
        return self._merge_overlays(document, secoes)

    def _merge_overlays(
        self, document: ReportDocument, secoes: list[dict]
    ) -> list[SectionSummaryItem]:
        effective = build_effective_dto(document.raw_parsed_data, document.parsed_overrides)
        ctx = build_prose_context(effective, document)
        report_kind = resolve_report_kind(document)
        ctx["report_kind"] = report_kind
        resolved_tables = build_table_rows(document, report_kind)
        deleted = set(document.deleted_section_ids)
        merged: list[SectionSummaryItem] = []

        for section in secoes:
            section_id = section["id"]
            is_disabled = section_id in deleted and section_id not in PROTECTED_SECTION_IDS
            overrides = document.section_overrides.get(section_id, {})
            prose = default_prose_values(section_id, ctx)
            field_overrides = {
                k: v for k, v in overrides.items()
                if k != "table_rows" and not isinstance(v, list)
            }
            fields = {**prose, **field_overrides}
            display_title = overrides.get(
                "section_title",
                SECTION_HEADING_DEFAULTS.get(section_id, section.get("title", section_id)),
            )
            display_title = strip_number_prefix(display_title)
            section_num = section.get("section_number")

            table_rows = None
            if section_id in TABLE_SECTIONS or section_id in resolved_tables:
                table_rows = list(resolved_tables.get(section_id) or [])
                if (
                    section_id == "controle_tecnico"
                    and document.control_info is not None
                    and not overrides.get("table_rows")
                    and not table_rows
                ):
                    table_rows = apply_control_info_to_rows(
                        merge_table_rows(section_id, None),
                        document.control_info,
                    )
            elif _is_estat_table_section(section_id):
                stored = overrides.get("table_rows")
                computed = build_estat_section_editor_rows(
                    document.raw_parsed_data, section_id
                )
                # Evita reaproveitar linhas da Identificação ou o formato antigo concatenado.
                if (
                    stored
                    and not _looks_like_identificacao_rows(stored)
                    and any(str(row.get("n") or "").strip() for row in stored)
                ):
                    table_rows = list(stored)
                else:
                    table_rows = computed

            if section_id == "introducao" and not str(fields.get("nota") or "").strip():
                fields["nota"] = str(
                    overrides.get("nota")
                    or overrides.get("intro")
                    or overrides.get("nota_deteccao")
                    or fields.get("intro")
                    or fields.get("nota_deteccao")
                    or ""
                )
            if section_id == "introducao":
                for row in overrides.get("table_rows") or []:
                    row_id = row.get("id", "")
                    if row_id in ("objetivo", "escopo", "referencia"):
                        if not str(fields.get(row_id) or "").strip() and row.get("value"):
                            fields[row_id] = str(row.get("value") or "")

            if section_id == "conclusao" and not str(fields.get("texto") or "").strip():
                total_fora = sum(
                    1
                    for item in (getattr(effective, "itens_medicao", []) or [])
                    if getattr(item, "status", "") == "Fora"
                )
                fields["texto"] = (
                    fields.get("texto_reprovado")
                    if total_fora > 0
                    else fields.get("texto_aprovado")
                ) or ""
                fields["modo"] = "reprovado" if total_fora > 0 else "aprovado"

            if section_id == "resultados" and not str(overrides.get("resumo") or "").strip():
                from src.core.domain.measurement_interpretation import build_dimensional_summary

                fields["resumo"] = build_dimensional_summary(
                    getattr(effective, "itens_medicao", []) or []
                )

            if section_id == "interpretacao":
                from src.core.application.interpretacao_edit import build_interpretacao_editor_fields

                fields.update(
                    build_interpretacao_editor_fields(
                        effective,
                        report_kind=report_kind,
                        existing=fields,
                        user_overrides=document.section_overrides.get("interpretacao", {}),
                    )
                )

            override_keys = [
                k for k in overrides
                if k != "table_rows" and not isinstance(overrides.get(k), list)
            ]
            has_overrides = (
                section_has_overrides(section_id, document.section_overrides)
                or (section_id == "resultados" and is_itens_overridden(document.parsed_overrides))
            )
            media_kinds = effective_media_kinds(section_id, overrides)
            disabled_chart_ids = list(overrides.get("disabled_chart_ids") or [])
            has_graphics = section_has_graphics(section_id, overrides) and enabled_chart_count(
                section_id, overrides
            ) > 0

            merged.append(SectionSummaryItem(
                id=section_id,
                display_title=display_title,
                title=overrides.get("section_title", display_title),
                has_overrides=has_overrides,
                section_number=section_num,
                table_rows=table_rows,
                fields=fields,
                custom=section.get("custom", False) or section_id.startswith("custom_"),
                subtitle=overrides.get("subtitle", ""),
                body=overrides.get("body", fields.get("body", "")),
                image_count=section.get("image_count", 0),
                has_images=section.get("has_images", False),
                has_graphics=has_graphics,
                media_kinds=media_kinds,
                disabled_chart_ids=disabled_chart_ids,
                page_start=section.get("page_start"),
                anchor_rect=section.get("anchor_rect"),
                global_fields=[
                    {"key": f.key, "label": f.label}
                    for f in get_global_fields_for_section(section_id)
                ],
                override_keys=override_keys,
                enabled=not is_disabled,
                protected=section_id in PROTECTED_SECTION_IDS,
            ))

        seen_ids = {item.id for item in merged}
        for custom in document.custom_sections:
            section_id = custom["id"]
            if section_id in seen_ids:
                continue
            is_disabled = section_id in deleted and section_id not in PROTECTED_SECTION_IDS
            overrides = document.section_overrides.get(section_id, {})
            title = overrides.get("title", custom.get("title", "Seção personalizada"))
            img_count = sum(1 for img in document.images if img.section_id == section_id)
            stored_rows = overrides.get("table_rows")
            merged.append(SectionSummaryItem(
                id=section_id,
                display_title=title,
                title=title,
                has_overrides=bool(overrides),
                fields=dict(overrides),
                custom=True,
                subtitle=overrides.get("nota", overrides.get("subtitle", "")),
                body=overrides.get("body", ""),
                table_rows=merge_table_rows(section_id, stored_rows),
                image_count=img_count,
                has_images=img_count > 0,
                media_kinds=effective_media_kinds(section_id, overrides),
                override_keys=list(overrides.keys()),
                enabled=not is_disabled,
                protected=False,
            ))
        return merged
