"""Monta o sumário de seções a partir do documento e do exportador."""
from __future__ import annotations

from src.core.domain.parsed_overrides import (
    build_effective_dto,
    build_prose_context,
    is_itens_overridden,
)
from src.core.domain.ports import ReportDocument, ReportExporter
from src.core.domain.report_field_registry import (
    default_prose_values,
    get_global_fields_for_section,
    section_has_overrides,
)
from src.core.domain.section_numbering import strip_number_prefix
from src.core.domain.table_row_registry import SECTION_HEADING_DEFAULTS, merge_table_rows
from src.ui.features.workspace.models.section_summary import SectionSummaryItem


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
        deleted = set(document.deleted_section_ids)
        merged: list[SectionSummaryItem] = []

        for section in secoes:
            section_id = section["id"]
            if section_id in deleted:
                continue
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
            if section_id == "identificacao":
                table_rows = merge_table_rows("identificacao", overrides.get("table_rows"))

            if section_id == "controle_tecnico" and document.control_info is not None:
                info = document.control_info
                fields.update({
                    "measured_by": info.measured_by,
                    "reviewed_by": info.reviewed_by,
                    "approved_by": info.approved_by,
                    "role": info.role,
                    "institutional_email": info.institutional_email,
                    "label_measured_by": overrides.get("label_measured_by", "Medido por"),
                    "label_reviewed_by": overrides.get("label_reviewed_by", "Revisado por"),
                    "label_approved_by": overrides.get("label_approved_by", "Aprovado por"),
                    "label_role": overrides.get("label_role", "Cargo"),
                    "label_institutional_email": overrides.get(
                        "label_institutional_email", "E-mail institucional"
                    ),
                })

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

            override_keys = [
                k for k in overrides
                if k != "table_rows" and not isinstance(overrides.get(k), list)
            ]
            has_overrides = (
                section_has_overrides(section_id, document.section_overrides)
                or (section_id == "resultados" and is_itens_overridden(document.parsed_overrides))
            )

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
                page_start=section.get("page_start"),
                anchor_rect=section.get("anchor_rect"),
                global_fields=[
                    {"key": f.key, "label": f.label}
                    for f in get_global_fields_for_section(section_id)
                ],
                override_keys=override_keys,
            ))

        seen_ids = {item.id for item in merged}
        for custom in document.custom_sections:
            section_id = custom["id"]
            if section_id in deleted or section_id in seen_ids:
                continue
            overrides = document.section_overrides.get(section_id, {})
            title = overrides.get("title", custom.get("title", "Seção personalizada"))
            img_count = sum(1 for img in document.images if img.section_id == section_id)
            merged.append(SectionSummaryItem(
                id=section_id,
                display_title=title,
                title=title,
                has_overrides=bool(overrides),
                fields=dict(overrides),
                custom=True,
                subtitle=overrides.get("subtitle", ""),
                body=overrides.get("body", ""),
                image_count=img_count,
                has_images=img_count > 0,
                override_keys=list(overrides.keys()),
            ))
        return merged
