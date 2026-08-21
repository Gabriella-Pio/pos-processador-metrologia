"""Definições de campos editáveis, mídia e colunas de medição."""
from __future__ import annotations

from dataclasses import dataclass

from src.core.domain.prose_templates import INTRODUCAO_BODY_TITLE_KEYS
from src.core.domain.section_catalog import catalog_by_id


@dataclass(frozen=True)
class SectionFieldDef:
    key: str
    label: str
    field_type: str = "text"  # text | textarea | computed
    editable: bool = True
    supports_formatting: bool = False


def _prose(
    key: str,
    label: str,
    field_type: str = "textarea",
    *,
    editable: bool = True,
    supports_formatting: bool = True,
) -> SectionFieldDef:
    return SectionFieldDef(
        key,
        label,
        field_type,
        editable=editable,
        supports_formatting=supports_formatting and field_type == "textarea",
    )


@dataclass(frozen=True)
class GlobalFieldDef:
    key: str
    label: str
    source: str  # dto | session | control
    dto_key: str | None = None
    used_in_sections: tuple[str, ...] = ()


@dataclass(frozen=True)
class SectionMediaDef:
    kind: str  # photos | graphics | tables
    label: str


_SECTION_FOOTER_NOTE = _prose("nota", "Nota de rodapé")

_SECTION_FIELDS: dict[str, tuple[SectionFieldDef, ...]] = {
    "introducao": (
        _prose("objetivo", "Objetivo"),
        _prose("escopo", "Escopo da análise"),
        _prose("referencia", "Referência de medição"),
        _SECTION_FOOTER_NOTE,
    ),
    "identificacao": (
        _prose("intro", "Texto introdutório"),
        _SECTION_FOOTER_NOTE,
    ),
    "metodo_escopo": (
        _prose("body", "Texto do método e escopo"),
        _SECTION_FOOTER_NOTE,
    ),
    "registro_componente": (
        _prose("intro", "Texto introdutório"),
        _SECTION_FOOTER_NOTE,
    ),
    "inspecao_optica": (
        _prose("body", "Texto da inspeção visual/óptica"),
        _SECTION_FOOTER_NOTE,
    ),
    "resultados_superficies": (
        _prose("intro", "Texto introdutório"),
        _prose("bullet_1", "Resultado 1"),
        _prose("bullet_2", "Resultado 2"),
        _prose("bullet_3", "Resultado 3"),
        _prose("bullet_4", "Resultado 4"),
        _SECTION_FOOTER_NOTE,
    ),
    "discussao_falha": (
        _prose("intro", "Texto introdutório"),
        _SECTION_FOOTER_NOTE,
    ),
    "controle_tecnico": (
        _prose("intro", "Texto introdutório / subtítulo"),
        _SECTION_FOOTER_NOTE,
    ),
    "resultados": (
        _prose("intro", "Texto introdutório"),
        _prose("resumo", "Resumo dimensional"),
        _SECTION_FOOTER_NOTE,
    ),
    "grafica": (
        _prose("intro", "Texto introdutório"),
        _SECTION_FOOTER_NOTE,
    ),
    "tomografia": (
        _prose("intro", "Texto introdutório"),
        _SECTION_FOOTER_NOTE,
    ),
    "resultados_inspecao": (
        _prose("body", "Texto dos resultados"),
        _SECTION_FOOTER_NOTE,
    ),
    "interpretacao": (
        _prose("intro", "Texto introdutório"),
        _prose("bullet_1", "Interpretação 1"),
        _prose("bullet_2", "Interpretação 2"),
        _prose("bullet_3", "Interpretação 3"),
        _prose("bullet_4", "Interpretação 4"),
        _SECTION_FOOTER_NOTE,
    ),
    "conclusao": (
        _prose("texto", "Texto da conclusão"),
        SectionFieldDef("modo", "Modo", "text", editable=False),
        SectionFieldDef("aprovacao", "Aprovação / Coordenação CEM", "text"),
        _SECTION_FOOTER_NOTE,
    ),
    "observacoes_limitacoes": (
        _prose("body", "Texto das observações"),
        _SECTION_FOOTER_NOTE,
    ),
    "historico_versoes": (
        _prose("intro", "Texto introdutório"),
        _SECTION_FOOTER_NOTE,
    ),
    "anexos": (
        _prose("intro", "Texto introdutório"),
        _SECTION_FOOTER_NOTE,
    ),
}

_SECTION_MEDIA: dict[str, tuple[SectionMediaDef, ...]] = {
    "introducao": (
        SectionMediaDef("tables", "Tabela da introdução"),
        SectionMediaDef("photos", "Fotografias"),
    ),
    "grafica": (
        SectionMediaDef("photos", "Fotografias"),
        SectionMediaDef("graphics", "Gráficos"),
    ),
    "estat_graficos": (SectionMediaDef("graphics", "Gráficos automáticos"),),
    "estat_graficos_comp": (SectionMediaDef("graphics", "Gráficos automáticos"),),
    "estat_resumo_diametros": (SectionMediaDef("tables", "Tabela resumo"),),
    "estat_resumo_alturas": (SectionMediaDef("tables", "Tabela resumo"),),
    "estat_resumo_dimensoes": (SectionMediaDef("tables", "Tabela resumo"),),
    "estat_resumo_cilindricidades": (SectionMediaDef("tables", "Tabela resumo"),),
    "estat_resumo_paralelismos": (SectionMediaDef("tables", "Tabela resumo"),),
    "estat_resumo_perpendicularidades": (SectionMediaDef("tables", "Tabela resumo"),),
    "estat_resumo_coaxialidades": (SectionMediaDef("tables", "Tabela resumo"),),
    "estat_resumo_angulos": (SectionMediaDef("tables", "Tabela resumo"),),
    "estat_resumo_outros": (SectionMediaDef("tables", "Tabela resumo"),),
    "estat_detalhe_diametros": (SectionMediaDef("tables", "Tabela detalhada"),),
    "estat_detalhe_alturas": (SectionMediaDef("tables", "Tabela detalhada"),),
    "estat_detalhe_dimensoes": (SectionMediaDef("tables", "Tabela detalhada"),),
    "estat_detalhe_cilindricidades": (SectionMediaDef("tables", "Tabela detalhada"),),
    "estat_detalhe_paralelismos": (SectionMediaDef("tables", "Tabela detalhada"),),
    "estat_detalhe_perpendicularidades": (SectionMediaDef("tables", "Tabela detalhada"),),
    "estat_detalhe_coaxialidades": (SectionMediaDef("tables", "Tabela detalhada"),),
    "estat_detalhe_angulos": (SectionMediaDef("tables", "Tabela detalhada"),),
    "estat_detalhe_outros": (SectionMediaDef("tables", "Tabela detalhada"),),
    "tomografia": (SectionMediaDef("photos", "Fotografias"),),
    "registro_componente": (SectionMediaDef("photos", "Fotografias"),),
    "inspecao_optica": (SectionMediaDef("photos", "Fotografias"),),
    "resultados": (SectionMediaDef("tables", "Tabela de resultados"),),
    "identificacao": (SectionMediaDef("tables", "Tabela de identificação"),),
    "controle_tecnico": (SectionMediaDef("tables", "Tabela de controle técnico"),),
    "discussao_falha": (SectionMediaDef("tables", "Tabela do mecanismo de falha"),),
}

CHART_SECTION_IDS: frozenset[str] = frozenset(
    {"estat_graficos", "estat_graficos_comp", "grafica"}
)

GLOBAL_FIELDS: tuple[GlobalFieldDef, ...] = (
    GlobalFieldDef("client_project", "Cliente / Projeto", "session", used_in_sections=("identificacao",)),
    GlobalFieldDef("evaluated_component", "Componente avaliado", "session", used_in_sections=("identificacao",)),
    GlobalFieldDef("componente", "Componente (CALYPSO)", "dto", "componente",
                   ("introducao", "identificacao", "interpretacao", "conclusao")),
    GlobalFieldDef("operador", "Operador", "dto", "operador",
                   ("identificacao", "controle_tecnico")),
    GlobalFieldDef("maquina_mmc", "Máquina de medição (MMC)", "dto", "maquina_mmc",
                   ("introducao", "identificacao")),
    GlobalFieldDef("numero_mmc", "Número da MMC", "dto", "numero_mmc", ("identificacao",)),
    GlobalFieldDef("data_hora", "Data/Hora da medição", "dto", "data_hora", ("identificacao",)),
    GlobalFieldDef("software", "Software", "dto", "software", ("identificacao",)),
    GlobalFieldDef("versao_software", "Versão do software", "dto", "versao_software", ("identificacao",)),
    GlobalFieldDef("numero_medicoes_cabecalho", "Quantidade de características", "dto",
                   "numero_medicoes_cabecalho", ("introducao", "identificacao", "resultados")),
)

_CUSTOM_DEFAULT_FIELDS = (
    SectionFieldDef("title", "Título"),
    _prose("body", "Conteúdo"),
    _SECTION_FOOTER_NOTE,
)
_CUSTOM_DEFAULT_MEDIA = (
    SectionMediaDef("photos", "Fotografias"),
    SectionMediaDef("tables", "Tabela"),
    SectionMediaDef("graphics", "Gráficos"),
)

MEDICAO_COLUMNS: tuple[tuple[str, str], ...] = (
    ("caracteristica", "Característica"),
    ("tipo", "Tipo"),
    ("valor_medido", "Medido"),
    ("nominal", "Nominal"),
    ("tol_superior", "Tol. +"),
    ("tol_inferior", "Tol. -"),
    ("desvio", "Desvio"),
    ("status", "Status"),
)

_MEDIA_KIND_LABELS: dict[str, str] = {
    "photos": "Fotografias",
    "graphics": "Gráficos",
    "tables": "Tabela",
}


def get_edit_fields(section_id: str, *, defaults_mode: bool = False) -> tuple[SectionFieldDef, ...]:
    if section_id.startswith("custom_"):
        return _CUSTOM_DEFAULT_FIELDS
    meta = catalog_by_id().get(section_id)
    if meta is not None and not meta.navigable:
        return ()
    fields = _SECTION_FIELDS.get(
        section_id, (_prose("intro", "Texto introdutório"),)
    )
    if not defaults_mode:
        return fields
    editable: list[SectionFieldDef] = []
    for field in fields:
        if field.editable or (defaults_mode and section_id == "interpretacao" and field.key == "intro"):
            editable.append(
                field
                if field.editable
                else SectionFieldDef(
                    field.key,
                    field.label,
                    field.field_type,
                    editable=True,
                    supports_formatting=field.supports_formatting,
                )
            )
    return tuple(editable)


def get_media_blocks(
    section_id: str,
    media_kinds: list[str] | None = None,
) -> tuple[SectionMediaDef, ...]:
    if media_kinds is not None:
        return tuple(
            SectionMediaDef(kind, _MEDIA_KIND_LABELS[kind])
            for kind in media_kinds
            if kind in _MEDIA_KIND_LABELS
        )
    if section_id.startswith("custom_"):
        return _CUSTOM_DEFAULT_MEDIA
    return _SECTION_MEDIA.get(section_id, ())


def effective_media_kinds(section_id: str, overrides: dict | None = None) -> list[str]:
    stored = (overrides or {}).get("media_kinds")
    if isinstance(stored, list):
        return [k for k in stored if k in _MEDIA_KIND_LABELS]
    return [block.kind for block in get_media_blocks(section_id)]


def get_global_fields_for_section(section_id: str) -> tuple[GlobalFieldDef, ...]:
    return tuple(f for f in GLOBAL_FIELDS if section_id in f.used_in_sections)


# Re-export for consumers that reference INTRODUCAO_BODY_TITLE_KEYS via field_definitions path
__all__ = [
    "GLOBAL_FIELDS",
    "INTRODUCAO_BODY_TITLE_KEYS",
    "MEDICAO_COLUMNS",
    "GlobalFieldDef",
    "SectionFieldDef",
    "SectionMediaDef",
    "effective_media_kinds",
    "get_edit_fields",
    "get_global_fields_for_section",
    "get_media_blocks",
]
