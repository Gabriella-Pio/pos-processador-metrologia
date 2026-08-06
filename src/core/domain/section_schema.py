"""
Fonte única de verdade para IDs, rótulos e ordem das seções do relatório.

Usado por: generator, adapters, TemplateEditor e Workspace.
Metadados canônicos em ``section_catalog``; este módulo expõe wrappers e helpers.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.core.domain.section_catalog import (
    SECTION_CATALOG,
    TEMPLATE_PROFILE_TOMOGRAFIA,
    default_enabled_blocks,
    fixed_section_ids,
    section_titles,
    tomography_blocks,
)

# Variáveis disponíveis em templates (modo editor)
TEMPLATE_VARIABLES = [
    {"key": "COMPONENTE", "label": "Componente avaliado"},
    {"key": "CLIENTE", "label": "Cliente / Projeto"},
    {"key": "DATA", "label": "Data da medição"},
    {"key": "RESPONSAVEL", "label": "Responsável pela medição"},
    {"key": "VERSAO", "label": "Versão do relatório"},
]


@dataclass(frozen=True)
class SectionDefinition:
    id: str
    label: str
    enabled_by_default: bool = True
    navigable: bool = True


SECTION_DEFINITIONS: tuple[SectionDefinition, ...] = tuple(
    SectionDefinition(
        id=meta.id,
        label=meta.label,
        enabled_by_default=meta.enabled_by_default,
        navigable=meta.navigable,
    )
    for meta in SECTION_CATALOG
)

SECTION_TITLES: dict[str, str] = section_titles()

# Seções com posição fixa no PDF (cabeçalho no início; histórico e anexos no fim).
FIXED_SECTION_IDS: frozenset[str] = fixed_section_ids()

TEMPLATE_PADRAO_OFICIAL: list[dict] = default_enabled_blocks()

# Template oficial de inspeção tomográfica (modelo CEMSZ / Bosello).
TEMPLATE_TOMOGRAFIA_OFICIAL: list[dict] = tomography_blocks()

TEMPLATE_TOMOGRAFIA_SECTIONS_CONFIG: dict[str, dict] = dict(TEMPLATE_PROFILE_TOMOGRAFIA)

_NAVIGABLE_IDS = frozenset(s.id for s in SECTION_DEFINITIONS if s.navigable)


def default_template_sections() -> list[dict]:
    """Lista para UI de template: id, label, enabled."""
    return [
        {"id": s.id, "label": s.label, "enabled": s.enabled_by_default}
        for s in SECTION_DEFINITIONS
    ]


def is_custom_section_id(section_id: str) -> bool:
    """Seção personalizada criada pelo usuário (não faz parte do schema fixo)."""
    return section_id.startswith("custom_") and section_id not in SECTION_TITLES


def merge_saved_template_config(saved_config: dict) -> list[dict]:
    """Reconcilia config salva com schema atual (novas seções entram no fim)."""
    if not saved_config:
        return default_template_sections()

    known = {s.id: s for s in SECTION_DEFINITIONS}
    ordered_ids = sorted(
        (sid for sid in saved_config if not sid.startswith("_")),
        key=lambda sid: saved_config[sid].get("order", 999),
    )
    result: list[dict] = []
    seen: set[str] = set()
    for section_id in ordered_ids:
        if section_id in known:
            seen.add(section_id)
            result.append({
                "id": section_id,
                "label": known[section_id].label,
                "enabled": saved_config[section_id].get("enabled", True),
            })
        elif is_custom_section_id(section_id):
            cfg = saved_config[section_id]
            seen.add(section_id)
            result.append({
                "id": section_id,
                "label": cfg.get("title") or section_id.replace("_", " ").title(),
                "enabled": cfg.get("enabled", True),
                "custom": True,
            })
    for section in SECTION_DEFINITIONS:
        if section.id not in seen:
            result.append({
                "id": section.id,
                "label": section.label,
                "enabled": section.enabled_by_default,
            })
    return result


def sections_config_to_blocks(sections_config: dict) -> list[dict]:
    """Converte config {id: {enabled, order}} em blocos do generator."""
    merged = merge_saved_template_config(sections_config)
    return [
        {"tipo": item["id"], "config": {}}
        for item in merged
        if item["enabled"]
    ]


def is_navigable_section(section_id: str) -> bool:
    return section_id in _NAVIGABLE_IDS


def is_tomography_template(template_id: str) -> bool:
    return template_id in {"tomografia", "tomo"}
