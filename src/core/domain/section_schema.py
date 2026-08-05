"""
Fonte única de verdade para IDs, rótulos e ordem das seções do relatório.

Usado por: generator, adapters, TemplateEditor e Workspace.
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
    SectionDefinition("metodo_escopo", "Método e escopo da avaliação", enabled_by_default=False),
    SectionDefinition("registro_componente", "Registro do componente", enabled_by_default=False),
    SectionDefinition("controle_tecnico", "Controle técnico"),
    SectionDefinition("resultados", "Resultados dimensionais"),
    SectionDefinition("grafica", "Análise gráfica dos resultados"),
    SectionDefinition("tomografia", "Inspeção tomográfica", enabled_by_default=False),
    SectionDefinition("resultados_inspecao", "Resultados da inspeção", enabled_by_default=False),
    SectionDefinition("interpretacao", "Interpretação dos resultados"),
    SectionDefinition("conclusao", "Conclusão"),
    SectionDefinition("observacoes_limitacoes", "Observações e limitações", enabled_by_default=False),
    SectionDefinition("historico_versoes", "Histórico de versões"),
    SectionDefinition("anexos", "Anexos"),
)

SECTION_TITLES: dict[str, str] = {s.id: s.label for s in SECTION_DEFINITIONS}

TEMPLATE_PADRAO_OFICIAL: list[dict] = [
    {"tipo": s.id, "config": {}}
    for s in SECTION_DEFINITIONS
    if s.enabled_by_default
]

# Template oficial de inspeção tomográfica (modelo CEMSZ / Bosello).
TEMPLATE_TOMOGRAFIA_OFICIAL: list[dict] = [
    {"tipo": "cabecalho", "config": {}},
    {"tipo": "introducao", "config": {"variant": "tomografia"}},
    {"tipo": "identificacao", "config": {}},
    {"tipo": "metodo_escopo", "config": {}},
    {"tipo": "registro_componente", "config": {}},
    {"tipo": "tomografia", "config": {}},
    {"tipo": "resultados_inspecao", "config": {}},
    {"tipo": "interpretacao", "config": {}},
    {"tipo": "conclusao", "config": {}},
    {"tipo": "observacoes_limitacoes", "config": {}},
    {"tipo": "controle_tecnico", "config": {}},
    {"tipo": "historico_versoes", "config": {}},
    {"tipo": "anexos", "config": {}},
]

TEMPLATE_TOMOGRAFIA_SECTIONS_CONFIG: dict[str, dict] = {
    "cabecalho": {"enabled": True, "order": 0},
    "introducao": {"enabled": True, "order": 1},
    "identificacao": {"enabled": True, "order": 2},
    "metodo_escopo": {"enabled": True, "order": 3},
    "registro_componente": {"enabled": True, "order": 4},
    "controle_tecnico": {"enabled": True, "order": 5},
    "resultados": {"enabled": False, "order": 6},
    "grafica": {"enabled": False, "order": 7},
    "tomografia": {"enabled": True, "order": 8},
    "resultados_inspecao": {"enabled": True, "order": 9},
    "interpretacao": {"enabled": True, "order": 10},
    "conclusao": {"enabled": True, "order": 11},
    "observacoes_limitacoes": {"enabled": True, "order": 12},
    "historico_versoes": {"enabled": True, "order": 13},
    "anexos": {"enabled": True, "order": 14},
}

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
