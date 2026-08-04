"""
Fonte única de verdade para IDs, rótulos e ordem das seções do relatório.

Usado por: generator, adapters, TemplateView, TemplateEditor e Workspace.
"""
from __future__ import annotations

from dataclasses import dataclass

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


SECTION_DEFINITIONS: tuple[SectionDefinition, ...] = (
    SectionDefinition("cabecalho", "Cabeçalho institucional", navigable=False),
    SectionDefinition("introducao", "Introdução"),
    SectionDefinition("identificacao", "Identificação e condições de medição"),
    SectionDefinition("controle_tecnico", "Controle técnico"),
    SectionDefinition("resultados", "Resultados dimensionais"),
    SectionDefinition("grafica", "Análise gráfica dos resultados"),
    SectionDefinition("tomografia", "Inspeção tomográfica", enabled_by_default=True),
    SectionDefinition("interpretacao", "Interpretação dos resultados"),
    SectionDefinition("conclusao", "Conclusão"),
    SectionDefinition("historico_versoes", "Histórico de versões"),
)

SECTION_TITLES: dict[str, str] = {s.id: s.label for s in SECTION_DEFINITIONS}

TEMPLATE_PADRAO_OFICIAL: list[dict] = [
    {"tipo": s.id, "config": {}}
    for s in SECTION_DEFINITIONS
    if s.enabled_by_default
]

_NAVIGABLE_IDS = frozenset(s.id for s in SECTION_DEFINITIONS if s.navigable)


def default_template_sections() -> list[dict]:
    """Lista para UI de template: id, label, enabled."""
    return [
        {"id": s.id, "label": s.label, "enabled": s.enabled_by_default}
        for s in SECTION_DEFINITIONS
    ]


def merge_saved_template_config(saved_config: dict) -> list[dict]:
    """Reconcilia config salva com schema atual (novas seções entram no fim)."""
    if not saved_config:
        return default_template_sections()

    known = {s.id: s for s in SECTION_DEFINITIONS}
    ordered_ids = sorted(
        saved_config.keys(),
        key=lambda sid: saved_config[sid].get("order", 999),
    )
    result: list[dict] = []
    seen: set[str] = set()
    for section_id in ordered_ids:
        if section_id not in known:
            continue
        seen.add(section_id)
        result.append({
            "id": section_id,
            "label": known[section_id].label,
            "enabled": saved_config[section_id].get("enabled", True),
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
