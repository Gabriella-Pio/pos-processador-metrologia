"""Fonte única de verdade para campos editáveis do relatório (UI + generator)."""
from __future__ import annotations

from dataclasses import dataclass

from src.core.domain.table_row_registry import INTRODUCAO_BLOCK_TITLES


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


# --- Prose templates (placeholders: {componente}, {numero_medicoes}, etc.) ---

PROSE_TEMPLATES: dict[str, dict[str, str]] = {
    "introducao": {
        "objetivo": (
            "Apresentar os resultados da inspeção dimensional realizada no componente "
            "identificado como {componente}, com base no relatório ZEISS CALYPSO."
        ),
        "escopo": (
            "A análise contempla as características cadastradas, avaliando conformidade "
            "com os limites nominais e de tolerância."
        ),
        "referencia": (
            "Valores nominais e limites conforme relatório emitido pelo software ZEISS CALYPSO."
        ),
        "valor_amostra": "1 peça",
        "valor_valores": "{numero_medicoes_cabecalho}",
        "valor_fora": "{total_fora} valores",
        "valor_mmc": "{maquina_mmc}",
    },
    "resultados": {
        "intro": (
            "A tabela abaixo apresenta os resultados extraídos do relatório de medição dimensional. "
            "A classificação “Dentro” ou “Fora” foi determinada com base nos limites cadastrados "
            "no relatório ZEISS CALYPSO."
        ),
    },
    "grafica": {
        "intro": (
            "Espaço reservado para inserção de fotografias, diagramas ou gráficos analíticos "
            "do componente."
        ),
    },
    "tomografia": {
        "intro": (
            "Avaliação qualitativa da integridade interna do componente realizada por ensaio tomográfico."
        ),
    },
    "metodo_escopo": {
        "body": "",
    },
    "registro_componente": {
        "intro": "",
    },
    "resultados_inspecao": {
        "body": "",
    },
    "observacoes_limitacoes": {
        "body": "",
        "aprovacao": "",
    },
    "interpretacao": {
        "intro": (
            "Análise detalhada das {numero_medicoes} características inspecionadas no "
            "componente {componente}:"
        ),
    },
    "controle_tecnico": {
        "intro": (
            "Registro dos responsáveis técnicos pela medição, revisão e, quando aplicável, "
            "aprovação deste relatório."
        ),
        "label_measured_by": "Medido por",
        "label_reviewed_by": "Revisado por",
        "label_approved_by": "Aprovado por",
        "label_role": "Cargo",
        "label_institutional_email": "E-mail institucional",
    },
    "identificacao": {
        "intro": "",
    },
    "conclusao": {
        "texto": "",
        "texto_aprovado": (
            "O componente analisado atende plenamente aos requisitos dimensionais especificados "
            "no relatório de origem, estando aprovado."
        ),
        "texto_reprovado": (
            "O componente analisado encontra-se reprovado parcialmente devido às divergências "
            "dimensionais constatadas, cabendo avaliação do setor de engenharia e qualidade "
            "para liberação ou retrabalho."
        ),
    },
    "historico_versoes": {
        "intro": "Registro das versões emitidas deste relatório.",
    },
}

@dataclass(frozen=True)
class IntroducaoBlockDef:
    title_key: str
    body_key: str | None
    label: str


INTRODUCAO_CONTENT_BLOCKS: tuple[IntroducaoBlockDef, ...] = (
    IntroducaoBlockDef("title_objetivo", "objetivo", "Objetivo"),
    IntroducaoBlockDef("title_escopo", "escopo", "Escopo da análise"),
    IntroducaoBlockDef("title_referencia", "referencia", "Referência de medição"),
)

INTRODUCAO_HEADER_ONLY_BLOCKS: tuple[IntroducaoBlockDef, ...] = (
    IntroducaoBlockDef("title_amostra", "valor_amostra", "Amostra"),
    IntroducaoBlockDef("title_valores", "valor_valores", "Valores avaliados"),
    IntroducaoBlockDef("title_fora", "valor_fora", "Fora dos limites"),
    IntroducaoBlockDef("title_mmc", "valor_mmc", "Máquina de medição (MMC)"),
)

_SECTION_FIELDS: dict[str, tuple[SectionFieldDef, ...]] = {
    "introducao": (),
    "identificacao": (
        SectionFieldDef("intro", "Texto introdutório", "textarea"),
    ),
    "metodo_escopo": (
        SectionFieldDef("body", "Texto do método e escopo", "textarea"),
    ),
    "registro_componente": (
        SectionFieldDef("intro", "Texto introdutório", "textarea"),
    ),
    "controle_tecnico": (
        SectionFieldDef("label_measured_by", "Título — Medido por"),
        SectionFieldDef("measured_by", "Medido por"),
        SectionFieldDef("label_reviewed_by", "Título — Revisado por"),
        SectionFieldDef("reviewed_by", "Revisado por"),
        SectionFieldDef("label_approved_by", "Título — Aprovado por"),
        SectionFieldDef("approved_by", "Aprovado por"),
        SectionFieldDef("label_role", "Título — Cargo"),
        SectionFieldDef("role", "Cargo"),
        SectionFieldDef("label_institutional_email", "Título — E-mail institucional"),
        SectionFieldDef("institutional_email", "E-mail institucional"),
    ),
    "resultados": (
        SectionFieldDef("intro", "Texto introdutório", "textarea"),
    ),
    "grafica": (
        SectionFieldDef("intro", "Texto introdutório", "textarea"),
    ),
    "tomografia": (
        SectionFieldDef("intro", "Texto introdutório", "textarea"),
    ),
    "resultados_inspecao": (
        SectionFieldDef("body", "Texto dos resultados", "textarea"),
    ),
    "interpretacao": (
        SectionFieldDef("intro", "Texto introdutório", "textarea"),
        SectionFieldDef("bullet_1", "Interpretação 1", "textarea"),
        SectionFieldDef("bullet_2", "Interpretação 2", "textarea"),
        SectionFieldDef("bullet_3", "Interpretação 3", "textarea"),
        SectionFieldDef("bullet_4", "Interpretação 4", "textarea"),
    ),
    "conclusao": (
        SectionFieldDef("texto", "Texto da conclusão", "textarea"),
        SectionFieldDef("modo", "Modo", "text", editable=False),
    ),
    "observacoes_limitacoes": (
        SectionFieldDef("body", "Texto das observações", "textarea"),
        SectionFieldDef("aprovacao", "Aprovação / Coordenação", "text"),
    ),
    "historico_versoes": (
        SectionFieldDef("intro", "Texto introdutório", "textarea"),
    ),
}

_SECTION_MEDIA: dict[str, tuple[SectionMediaDef, ...]] = {
    "introducao": (SectionMediaDef("photos", "Fotografias"),),
    "grafica": (
        SectionMediaDef("photos", "Fotografias"),
        SectionMediaDef("graphics", "Gráficos"),
    ),
    "tomografia": (SectionMediaDef("photos", "Fotografias"),),
    "registro_componente": (SectionMediaDef("photos", "Fotografias"),),
    "resultados": (SectionMediaDef("tables", "Tabela de resultados"),),
    "identificacao": (SectionMediaDef("tables", "Tabela de identificação"),),
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


def default_prose_values(section_id: str, context: dict[str, str] | None = None) -> dict[str, str]:
    """Templates de prosa com placeholders — não resolve valores globais."""
    base = dict(PROSE_TEMPLATES.get(section_id, {}))
    if context and context.get("report_kind") == "tomografia":
        from src.core.domain.tomo_template_defaults import TOMO_PROSE_DEFAULTS

        base.update(TOMO_PROSE_DEFAULTS.get(section_id, {}))
    return base


def merge_section_prose(
    section_id: str,
    overrides: dict[str, str],
    context: dict[str, str] | None = None,
) -> dict[str, str]:
    defaults = default_prose_values(section_id, context)
    merged = {
        **defaults,
        **{
            k: v
            for k, v in overrides.items()
            if v is not None
            and not k.startswith("title_")
            and k not in {"section_title", "table_rows", "media_kinds"}
        },
    }
    return merged


def is_field_overridden(section_id: str, field_key: str, overrides: dict[str, dict]) -> bool:
    section_ov = overrides.get(section_id, {})
    if field_key not in section_ov:
        return False
    defaults = default_prose_values(section_id)
    return section_ov.get(field_key, "") != defaults.get(field_key, "")


def section_has_overrides(section_id: str, overrides: dict[str, dict]) -> bool:
    section_ov = overrides.get(section_id, {})
    if section_ov.get("section_title"):
        return True
    if section_ov.get("table_rows"):
        return True
    for key in INTRODUCAO_BLOCK_TITLES:
        if key in section_ov:
            return True
    for field_def in get_edit_fields(section_id):
        if field_def.editable and is_field_overridden(section_id, field_def.key, overrides):
            return True
    return bool(section_ov)
