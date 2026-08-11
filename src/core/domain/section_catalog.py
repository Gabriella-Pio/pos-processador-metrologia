"""
Catálogo canônico de metadados de seção do relatório.

Fonte única para IDs, rótulos UI, cabeçalhos PDF, numeração, posição fixa
e perfis de template (MMC vs tomografia). Outros módulos derivam deste catálogo.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

FixedPosition = Literal["start", "end", "none"]


@dataclass(frozen=True)
class SectionMeta:
    id: str
    label: str
    pdf_heading: str = ""
    enabled_by_default: bool = True
    navigable: bool = True
    fixed_position: FixedPosition = "none"
    numbered: bool = False
    renderer_id: str | None = None
    block_config: dict | None = None

    @property
    def registry_key(self) -> str:
        return self.renderer_id or self.id

    def to_block(self) -> dict:
        config = dict(self.block_config or {})
        return {"tipo": self.id, "config": config}


def _meta(
    id: str,
    label: str,
    *,
    pdf_heading: str = "",
    enabled_by_default: bool = True,
    navigable: bool = True,
    fixed_position: FixedPosition = "none",
    numbered: bool = False,
    renderer_id: str | None = None,
    block_config: dict | None = None,
) -> SectionMeta:
    return SectionMeta(
        id=id,
        label=label,
        pdf_heading=pdf_heading,
        enabled_by_default=enabled_by_default,
        navigable=navigable,
        fixed_position=fixed_position,
        numbered=numbered,
        renderer_id=renderer_id,
        block_config=block_config,
    )


SECTION_CATALOG: tuple[SectionMeta, ...] = (
    _meta("cabecalho", "Cabeçalho institucional", navigable=False, fixed_position="start"),
    _meta(
        "introducao",
        "Introdução",
        pdf_heading="RELATÓRIO TÉCNICO — ANÁLISE DIMENSIONAL",
        fixed_position="start",
    ),
    _meta(
        "identificacao",
        "Identificação e condições de medição",
        pdf_heading="IDENTIFICAÇÃO E CONDIÇÕES DE MEDIÇÃO",
        numbered=True,
    ),
    _meta(
        "metodo_escopo",
        "Método e escopo da avaliação",
        pdf_heading="MÉTODO E ESCOPO DA AVALIAÇÃO",
        enabled_by_default=False,
        numbered=True,
    ),
    _meta(
        "registro_componente",
        "Registro do componente",
        pdf_heading="REGISTRO DO COMPONENTE",
        enabled_by_default=False,
        numbered=True,
    ),
    _meta(
        "controle_tecnico",
        "Controle técnico",
        pdf_heading="CONTROLE TÉCNICO",
        numbered=True,
    ),
    _meta(
        "resultados",
        "Resultados dimensionais",
        pdf_heading="RESULTADOS DIMENSIONAIS",
        numbered=True,
    ),
    _meta(
        "grafica",
        "Análise gráfica dos resultados",
        pdf_heading="ANÁLISE GRÁFICA DOS RESULTADOS",
        numbered=True,
    ),
    _meta(
        "tomografia",
        "Inspeção tomográfica",
        pdf_heading="INSPEÇÃO TOMOGRÁFICA",
        enabled_by_default=False,
        numbered=True,
    ),
    _meta(
        "resultados_inspecao",
        "Resultados da inspeção",
        pdf_heading="RESULTADOS DA INSPEÇÃO",
        enabled_by_default=False,
        numbered=True,
    ),
    _meta(
        "interpretacao",
        "Interpretação dos resultados",
        pdf_heading="INTERPRETAÇÃO DOS RESULTADOS",
        numbered=True,
    ),
    _meta(
        "conclusao",
        "Conclusão",
        pdf_heading="CONCLUSÃO",
        numbered=True,
    ),
    _meta(
        "observacoes_limitacoes",
        "Observações e limitações",
        pdf_heading="OBSERVAÇÕES E LIMITAÇÕES",
        enabled_by_default=False,
        numbered=True,
    ),
    _meta(
        "historico_versoes",
        "Histórico de versões",
        pdf_heading="HISTÓRICO DE VERSÕES",
        numbered=True,
    ),
    _meta(
        "anexos",
        "Anexos",
        pdf_heading="ANEXOS",
        fixed_position="end",
        numbered=True,
    ),
)

TEMPLATE_PROFILE_MMC: dict[str, dict] = {
    meta.id: {"enabled": meta.enabled_by_default, "order": idx}
    for idx, meta in enumerate(SECTION_CATALOG)
}

TEMPLATE_PROFILE_TOMOGRAFIA: dict[str, dict] = {
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

_TOMOGRAPHY_BLOCK_ORDER: tuple[str, ...] = (
    "cabecalho",
    "introducao",
    "identificacao",
    "metodo_escopo",
    "registro_componente",
    "tomografia",
    "resultados_inspecao",
    "interpretacao",
    "conclusao",
    "observacoes_limitacoes",
    "controle_tecnico",
    "historico_versoes",
    "anexos",
)

_TOMOGRAPHY_BLOCK_CONFIG: dict[str, dict] = {
    "introducao": {"variant": "tomografia"},
}


def catalog_by_id() -> dict[str, SectionMeta]:
    return {meta.id: meta for meta in SECTION_CATALOG}


def section_ids() -> tuple[str, ...]:
    return tuple(meta.id for meta in SECTION_CATALOG)


def default_enabled_blocks() -> list[dict]:
    """Blocos do template MMC padrão (seções com ``enabled_by_default``)."""
    return [meta.to_block() for meta in SECTION_CATALOG if meta.enabled_by_default]


def tomography_blocks() -> list[dict]:
    """Blocos do template tomográfico oficial (ordem e configs específicas)."""
    by_id = catalog_by_id()
    blocks: list[dict] = []
    for section_id in _TOMOGRAPHY_BLOCK_ORDER:
        meta = by_id[section_id]
        config = dict(meta.block_config or {})
        config.update(_TOMOGRAPHY_BLOCK_CONFIG.get(section_id, {}))
        blocks.append({"tipo": section_id, "config": config})
    return blocks


def section_titles() -> dict[str, str]:
    return {meta.id: meta.label for meta in SECTION_CATALOG}


def fixed_section_ids() -> frozenset[str]:
    """Seções com posição fixa no PDF/sumário (início ou fim) — não arrastáveis."""
    return frozenset(
        meta.id for meta in SECTION_CATALOG if meta.fixed_position != "none"
    )


def protected_section_ids() -> frozenset[str]:
    """Seções obrigatórias — não podem ser desativadas no workspace nem no template."""
    return frozenset({"cabecalho", "introducao"})


def fixed_position_start_ids() -> tuple[str, ...]:
    """Ordem canônica das seções fixas no início do relatório."""
    return tuple(
        meta.id for meta in SECTION_CATALOG if meta.fixed_position == "start"
    )


def section_heading_defaults() -> dict[str, str]:
    return {
        meta.id: meta.pdf_heading
        for meta in SECTION_CATALOG
        if meta.pdf_heading
    }


def numbered_section_ids() -> frozenset[str]:
    return frozenset(meta.id for meta in SECTION_CATALOG if meta.numbered)
