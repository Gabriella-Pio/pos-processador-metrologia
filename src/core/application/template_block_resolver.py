"""Resolução de blocos de template para exportação e sumário."""
from __future__ import annotations

from src.core.domain.section_catalog import fixed_position_start_ids
from src.core.domain.section_schema import (
    PROTECTED_SECTION_IDS,
    TEMPLATE_FALHA_OFICIAL,
    TEMPLATE_TOMOGRAFIA_OFICIAL,
    is_falha_template,
    is_tomography_template,
    sections_config_to_blocks,
)
from src.core.domain.ports import ReportDocument, TemplateRepository
from src.core.generator.constants import TEMPLATE_PADRAO_OFICIAL


def resolve_template_blocks(
    document: ReportDocument,
    template_repository: TemplateRepository | None = None,
) -> list[dict]:
    """Mesma lógica usada em ``export()`` e ``list_sections()``."""
    if document.template_layout_override:
        blocos = sections_config_to_blocks(document.template_layout_override)
    elif is_tomography_template(document.template_id):
        config_salva = (
            template_repository.get_template_config(document.template_id)
            if template_repository is not None
            else {}
        )
        blocos = (
            sections_config_to_blocks(config_salva)
            if config_salva
            else list(TEMPLATE_TOMOGRAFIA_OFICIAL)
        )
    elif is_falha_template(document.template_id):
        config_salva = (
            template_repository.get_template_config(document.template_id)
            if template_repository is not None
            else {}
        )
        blocos = (
            sections_config_to_blocks(config_salva)
            if config_salva
            else list(TEMPLATE_FALHA_OFICIAL)
        )
    elif document.template_id == "default" or template_repository is None:
        blocos = list(TEMPLATE_PADRAO_OFICIAL)
    else:
        config_salva = template_repository.get_template_config(document.template_id)
        blocos = (
            list(TEMPLATE_PADRAO_OFICIAL)
            if not config_salva
            else sections_config_to_blocks(config_salva)
        )
    ordered = apply_section_order(blocos, document)
    return ordered


def resolve_active_template_blocks(
    document: ReportDocument,
    template_repository: TemplateRepository | None = None,
) -> list[dict]:
    """Blocos que entram no PDF — omite seções desativadas no workspace."""
    return apply_deleted_sections(
        resolve_template_blocks(document, template_repository),
        document,
    )


def apply_deleted_sections(blocos: list[dict], document: ReportDocument) -> list[dict]:
    """Remove seções desativadas no workspace (``deleted_section_ids``)."""
    deleted = set(document.deleted_section_ids) - PROTECTED_SECTION_IDS
    if not deleted:
        return blocos
    return [b for b in blocos if b["tipo"] not in deleted]


def apply_section_order(blocos: list[dict], document: ReportDocument) -> list[dict]:
    """Cabeçalho + introdução no início; corpo reordenável; anexos por último."""
    start_order = fixed_position_start_ids()
    by_type = {b["tipo"]: b for b in blocos}
    start = [by_type[sid] for sid in start_order if sid in by_type]
    anexos = [b for b in blocos if b["tipo"] == "anexos"]
    fixed_tail = {"anexos"}
    fixed_start = set(start_order)
    middle = [
        b for b in blocos
        if b["tipo"] not in fixed_start and b["tipo"] not in fixed_tail
    ]
    if document.section_order:
        order_index = {sid: idx for idx, sid in enumerate(document.section_order)}
        middle.sort(key=lambda b: order_index.get(b["tipo"], 10_000))
    ordered = start + middle + anexos
    with_extras = inject_extra_catalog_sections(ordered, document)
    return inject_custom_sections(with_extras, document)


def _insert_before_anexos(blocos: list[dict], extra_blocks: list[dict]) -> list[dict]:
    if not extra_blocks:
        return blocos
    result: list[dict] = []
    inserted = False
    for bloco in blocos:
        if bloco["tipo"] == "anexos" and not inserted:
            result.extend(extra_blocks)
            inserted = True
        result.append(bloco)
    if not inserted:
        result.extend(extra_blocks)
    return result


def inject_extra_catalog_sections(blocos: list[dict], document: ReportDocument) -> list[dict]:
    """Inclui seções do catálogo adicionadas manualmente no workspace."""
    extras = getattr(document, "extra_section_ids", None) or []
    if not extras:
        return blocos
    present = {b["tipo"] for b in blocos}
    extra_blocks = [
        {"tipo": section_id, "config": {}}
        for section_id in extras
        if section_id and section_id not in present
    ]
    return _insert_before_anexos(blocos, extra_blocks)


def inject_custom_sections(blocos: list[dict], document: ReportDocument) -> list[dict]:
    if not document.custom_sections:
        return blocos
    deleted = set(document.deleted_section_ids)
    custom_blocks = [
        {"tipo": section["id"], "config": {"section_id": section["id"]}}
        for section in document.custom_sections
        if section.get("id") not in deleted
    ]
    return _insert_before_anexos(blocos, custom_blocks)
