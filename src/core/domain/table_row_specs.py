"""Especificações estáticas de linhas de tabela por seção."""
from __future__ import annotations

from dataclasses import dataclass

from src.core.domain.prose_templates import PROSE_TEMPLATES
from src.core.domain.section_catalog import numbered_section_ids, section_heading_defaults


@dataclass(frozen=True)
class TableRowDef:
    id: str
    label: str
    default_value: str


SECTION_HEADING_DEFAULTS: dict[str, str] = section_heading_defaults()

NUMBERED_SECTION_IDS: frozenset[str] = numbered_section_ids()

INTRODUCAO_BLOCK_TITLES: dict[str, str] = {
    "title_objetivo": "OBJETIVO",
    "title_escopo": "ESCOPO DA ANÁLISE",
    "title_referencia": "REFERÊNCIA DE MEDIÇÃO",
    "title_amostra": "AMOSTRA",
    "title_valores": "VALORES AVALIADOS",
    "title_fora": "FORA DOS LIMITES",
    "title_mmc": "MÁQUINA DE MEDIÇÃO (MMC)",
}

IDENTIFICACAO_TABLE_ROWS: tuple[TableRowDef, ...] = (
    TableRowDef("client_project", "Cliente / Projeto", "{client_project}"),
    TableRowDef("evaluated_component", "Componente Avaliado", "{evaluated_component}"),
    TableRowDef("componente", "Identificação no Relatório CALYPSO", "{componente}"),
    TableRowDef("maquina_mmc", "Máquina de Medição", "{maquina_mmc}"),
    TableRowDef("numero_mmc", "Número da MMC", "{numero_mmc}"),
    TableRowDef("software", "Software", "{software} {versao_software}"),
    TableRowDef("operador", "Operador", "{operador}"),
    TableRowDef("data_hora", "Data/Hora da Medição", "{data_hora}"),
    TableRowDef(
        "numero_medicoes_cabecalho",
        "Quantidade de características",
        "{numero_medicoes_cabecalho} valore(s) medido(s)",
    ),
)

CONTROLE_TECNICO_TABLE_ROWS: tuple[TableRowDef, ...] = (
    TableRowDef("measured_by", "Medido por", ""),
    TableRowDef("reviewed_by", "Revisado por", ""),
    TableRowDef("approved_by", "Aprovado por", "Matheus de Oliveira e Silva"),
    TableRowDef("role", "Cargo", ""),
    TableRowDef("institutional_email", "E-mail institucional", ""),
    TableRowDef("timestamp_str", "Data/Hora", ""),
)

CONTROLE_TECNICO_VALUE_IDS = frozenset(row.id for row in CONTROLE_TECNICO_TABLE_ROWS)

INTRODUCAO_PROSE_ROW_IDS = frozenset({"objetivo", "escopo", "referencia"})

INTRODUCAO_ROW_SPECS: tuple[tuple[str, str, str], ...] = (
    ("amostra", "title_amostra", "valor_amostra"),
    ("valores", "title_valores", "valor_valores"),
    ("fora", "title_fora", "valor_fora"),
    ("mmc", "title_mmc", "valor_mmc"),
)

TABLE_SECTIONS = frozenset({"identificacao", "controle_tecnico", "introducao", "discussao_falha"})


def uses_table_rows_editor(section_id: str) -> bool:
    """Seções cuja aba Tabela usa o editor label/valor (inclui resumos estatísticos)."""
    from src.core.domain.section_schema import is_custom_section_id
    from src.core.application.statistical_aggregator import tipo_from_estat_section_id

    return (
        section_id in TABLE_SECTIONS
        or is_custom_section_id(section_id)
        or bool(tipo_from_estat_section_id(section_id))
    )


def default_table_rows(section_id: str) -> list[dict[str, str]]:
    if section_id == "identificacao":
        source = IDENTIFICACAO_TABLE_ROWS
        return [
            {"id": row.id, "label": row.label, "value": row.default_value}
            for row in source
        ]
    if section_id == "controle_tecnico":
        source = CONTROLE_TECNICO_TABLE_ROWS
        return [
            {"id": row.id, "label": row.label, "value": row.default_value}
            for row in source
        ]
    if section_id == "discussao_falha":
        return default_discussao_falha_rows()
    if section_id == "introducao":
        prose = PROSE_TEMPLATES.get("introducao", {})
        return [
            {
                "id": row_id,
                "label": INTRODUCAO_BLOCK_TITLES.get(title_key, row_id.upper()),
                "value": str(prose.get(value_key, "")),
            }
            for row_id, title_key, value_key in INTRODUCAO_ROW_SPECS
        ]
    return []


def default_tomo_introducao_rows() -> list[dict[str, str]]:
    from src.core.domain.tomo_template_defaults import INTRODUCAO_TOMO_TABLE_ROWS

    return [
        {"id": row_id, "label": label, "value": value}
        for row_id, label, value in INTRODUCAO_TOMO_TABLE_ROWS
    ]


def default_tomo_identificacao_rows() -> list[dict[str, str]]:
    from src.core.domain.tomo_template_defaults import IDENTIFICACAO_TOMO_TABLE_ROWS

    return [
        {"id": row_id, "label": label, "value": value}
        for row_id, label, value in IDENTIFICACAO_TOMO_TABLE_ROWS
    ]


def default_falha_introducao_rows() -> list[dict[str, str]]:
    from src.core.domain.falha_template_defaults import INTRODUCAO_FALHA_TABLE_ROWS

    return [
        {"id": row_id, "label": label, "value": value}
        for row_id, label, value in INTRODUCAO_FALHA_TABLE_ROWS
    ]


def default_falha_identificacao_rows() -> list[dict[str, str]]:
    from src.core.domain.falha_template_defaults import IDENTIFICACAO_FALHA_TABLE_ROWS

    return [
        {"id": row_id, "label": label, "value": value}
        for row_id, label, value in IDENTIFICACAO_FALHA_TABLE_ROWS
    ]


def default_discussao_falha_rows() -> list[dict[str, str]]:
    from src.core.domain.falha_template_defaults import DISCUSSAO_FALHA_TABLE_ROWS

    return [
        {"id": row_id, "label": label, "value": value}
        for row_id, label, value in DISCUSSAO_FALHA_TABLE_ROWS
    ]


def apply_control_info_to_rows(rows: list[dict[str, str]], control_info) -> list[dict[str, str]]:
    """Preenche valores das linhas a partir de ``TechnicalControlInfo``."""
    if control_info is None:
        return [dict(row) for row in rows]
    values = {
        "measured_by": control_info.measured_by or "",
        "reviewed_by": control_info.reviewed_by or "",
        "approved_by": control_info.approved_by or "Não aplicável",
        "role": control_info.role or "",
        "institutional_email": control_info.institutional_email or "",
        "timestamp_str": control_info.timestamp.strftime("%d/%m/%Y %H:%M"),
    }
    filled: list[dict[str, str]] = []
    for row in rows:
        item = dict(row)
        row_id = item.get("id", "")
        if row_id in values:
            item["value"] = values[row_id]
        filled.append(item)
    return filled


def control_info_updates_from_rows(rows: list[dict[str, str]]) -> dict[str, str]:
    """Extrai campos de ``TechnicalControlInfo`` a partir das linhas editadas."""
    updates: dict[str, str] = {}
    for row in rows:
        row_id = row.get("id", "")
        if row_id in CONTROLE_TECNICO_VALUE_IDS and row_id != "timestamp_str":
            updates[row_id] = str(row.get("value") or "")
    return updates
