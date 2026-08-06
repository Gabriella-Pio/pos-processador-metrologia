"""Definições de campos editáveis, mídia e colunas de medição."""
from __future__ import annotations

from dataclasses import dataclass

from src.core.domain.prose_templates import INTRODUCAO_BODY_TITLE_KEYS


@dataclass(frozen=True)
class SectionFieldDef:
    key: str
    label: str
    field_type: str = "text"  # text | textarea | computed
    editable: bool = True


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


_SECTION_FOOTER_NOTE = SectionFieldDef("nota", "Nota de rodapé", "textarea")

_SECTION_FIELDS: dict[str, tuple[SectionFieldDef, ...]] = {
    "introducao": (
        SectionFieldDef("objetivo", "Objetivo", "textarea"),
        SectionFieldDef("escopo", "Escopo da análise", "textarea"),
        SectionFieldDef("referencia", "Referência de medição", "textarea"),
        _SECTION_FOOTER_NOTE,
    ),
    "identificacao": (
        SectionFieldDef("intro", "Texto introdutório", "textarea"),
        _SECTION_FOOTER_NOTE,
    ),
    "metodo_escopo": (
        SectionFieldDef("body", "Texto do método e escopo", "textarea"),
        _SECTION_FOOTER_NOTE,
    ),
    "registro_componente": (
        SectionFieldDef("intro", "Texto introdutório", "textarea"),
        _SECTION_FOOTER_NOTE,
    ),
    "controle_tecnico": (
        SectionFieldDef("intro", "Texto introdutório / subtítulo", "textarea"),
        _SECTION_FOOTER_NOTE,
    ),
    "resultados": (
        SectionFieldDef("intro", "Texto introdutório", "textarea"),
        _SECTION_FOOTER_NOTE,
    ),
    "grafica": (
        SectionFieldDef("intro", "Texto introdutório", "textarea"),
        _SECTION_FOOTER_NOTE,
    ),
    "tomografia": (
        SectionFieldDef("intro", "Texto introdutório", "textarea"),
        _SECTION_FOOTER_NOTE,
    ),
    "resultados_inspecao": (
        SectionFieldDef("body", "Texto dos resultados", "textarea"),
        _SECTION_FOOTER_NOTE,
    ),
    "interpretacao": (
        SectionFieldDef("intro", "Texto introdutório", "textarea"),
        SectionFieldDef("bullet_1", "Interpretação 1", "textarea"),
        SectionFieldDef("bullet_2", "Interpretação 2", "textarea"),
        SectionFieldDef("bullet_3", "Interpretação 3", "textarea"),
        SectionFieldDef("bullet_4", "Interpretação 4", "textarea"),
        _SECTION_FOOTER_NOTE,
    ),
    "conclusao": (
        SectionFieldDef("texto", "Texto da conclusão", "textarea"),
        SectionFieldDef("modo", "Modo", "text", editable=False),
        SectionFieldDef("aprovacao", "Aprovação / Coordenação CEM", "text"),
        _SECTION_FOOTER_NOTE,
    ),
    "observacoes_limitacoes": (
        SectionFieldDef("body", "Texto das observações", "textarea"),
        _SECTION_FOOTER_NOTE,
    ),
    "historico_versoes": (
        SectionFieldDef("intro", "Texto introdutório", "textarea"),
        _SECTION_FOOTER_NOTE,
    ),
    "anexos": (
        SectionFieldDef("intro", "Texto introdutório", "textarea"),
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
    "tomografia": (SectionMediaDef("photos", "Fotografias"),),
    "registro_componente": (SectionMediaDef("photos", "Fotografias"),),
    "resultados": (SectionMediaDef("tables", "Tabela de resultados"),),
    "identificacao": (SectionMediaDef("tables", "Tabela de identificação"),),
    "controle_tecnico": (SectionMediaDef("tables", "Tabela de controle técnico"),),
}

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
    SectionFieldDef("subtitle", "Subtítulo"),
    SectionFieldDef("body", "Conteúdo", "textarea"),
)
_CUSTOM_DEFAULT_MEDIA = (SectionMediaDef("photos", "Fotografias"),)

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
    fields = _SECTION_FIELDS.get(
        section_id, (SectionFieldDef("intro", "Texto introdutório", "textarea"),)
    )
    if not defaults_mode:
        return fields
    editable: list[SectionFieldDef] = []
    for field in fields:
        if field.editable or (defaults_mode and section_id == "interpretacao" and field.key == "intro"):
            editable.append(
                field if field.editable else SectionFieldDef(field.key, field.label, field.field_type, editable=True)
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
