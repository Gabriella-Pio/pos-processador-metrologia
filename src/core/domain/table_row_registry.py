"""Definição das linhas de tabela por seção (espelham o preview PDF)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TableRowDef:
    id: str
    label: str
    default_value: str


SECTION_HEADING_DEFAULTS: dict[str, str] = {
    "introducao": "RELATÓRIO TÉCNICO — ANÁLISE DIMENSIONAL E TOMOGRÁFICA",
    "identificacao": "IDENTIFICAÇÃO E CONDIÇÕES DE MEDIÇÃO",
    "metodo_escopo": "MÉTODO E ESCOPO DA AVALIAÇÃO",
    "registro_componente": "REGISTRO DO COMPONENTE",
    "resultados": "RESULTADOS DIMENSIONAIS",
    "grafica": "ANÁLISE GRÁFICA DOS RESULTADOS",
    "tomografia": "INSPEÇÃO TOMOGRÁFICA",
    "resultados_inspecao": "RESULTADOS DA INSPEÇÃO",
    "interpretacao": "INTERPRETAÇÃO DOS RESULTADOS",
    "conclusao": "CONCLUSÃO",
    "observacoes_limitacoes": "OBSERVAÇÕES E LIMITAÇÕES",
    "controle_tecnico": "CONTROLE TÉCNICO",
    "historico_versoes": "HISTÓRICO DE VERSÕES",
    "anexos": "ANEXOS",
}

NUMBERED_SECTION_IDS: frozenset[str] = frozenset({
    "identificacao",
    "metodo_escopo",
    "registro_componente",
    "resultados",
    "grafica",
    "tomografia",
    "resultados_inspecao",
    "interpretacao",
    "conclusao",
    "observacoes_limitacoes",
    "controle_tecnico",
    "historico_versoes",
    "anexos",
})

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
    TableRowDef("approved_by", "Aprovado por", "Não aplicável"),
    TableRowDef("role", "Cargo", ""),
    TableRowDef("institutional_email", "E-mail institucional", ""),
    TableRowDef("timestamp_str", "Data/Hora", ""),
)

CONTROLE_TECNICO_VALUE_IDS = frozenset(row.id for row in CONTROLE_TECNICO_TABLE_ROWS)

# Valores padrão vêm de PROSE_TEMPLATES — montados em default_table_rows.
# Objetivo/Escopo/Referência ficam no Conteúdo (prose), não na tabela de métricas.
INTRODUCAO_PROSE_ROW_IDS = frozenset({"objetivo", "escopo", "referencia"})

INTRODUCAO_ROW_SPECS: tuple[tuple[str, str, str], ...] = (
    ("amostra", "title_amostra", "valor_amostra"),
    ("valores", "title_valores", "valor_valores"),
    ("fora", "title_fora", "valor_fora"),
    ("mmc", "title_mmc", "valor_mmc"),
)

TABLE_SECTIONS = frozenset({"identificacao", "controle_tecnico", "introducao"})


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
    if section_id == "introducao":
        from src.core.domain.report_field_registry import PROSE_TEMPLATES

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


def apply_legacy_introducao_overrides(
    rows: list[dict[str, str]],
    overrides: dict | None,
) -> list[dict[str, str]]:
    """Aplica pares title_* / corpo legados sobre as linhas de métricas."""
    if not overrides:
        return [dict(row) for row in rows]

    label_keys = {
        "amostra": "title_amostra",
        "valores": "title_valores",
        "fora": "title_fora",
        "mmc": "title_mmc",
        "tipo_analise": "title_valores",
        "metodo": "title_fora",
        "equipamento": "title_mmc",
        "trincas": "title_trincas",
        "impurezas": "title_impurezas",
        "obstrucoes": "title_obstrucoes",
    }
    value_keys = {
        "amostra": "valor_amostra",
        "valores": "valor_valores",
        "fora": "valor_fora",
        "mmc": "valor_mmc",
        "tipo_analise": "valor_tipo_analise",
        "metodo": "valor_metodo",
        "equipamento": "valor_equipamento",
        "trincas": "valor_trincas",
        "impurezas": "valor_impurezas",
        "obstrucoes": "valor_obstrucoes",
    }
    filled: list[dict[str, str]] = []
    for row in rows:
        item = dict(row)
        row_id = item.get("id", "")
        title_key = label_keys.get(row_id)
        value_key = value_keys.get(row_id)
        if title_key and title_key in overrides:
            item["label"] = str(overrides[title_key])
        if value_key and value_key in overrides:
            item["value"] = str(overrides[value_key])
        filled.append(item)
    return filled


def _strip_introducao_prose_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [dict(row) for row in rows if row.get("id") not in INTRODUCAO_PROSE_ROW_IDS]


def resolve_introducao_table_rows(
    overrides: dict | None,
    *,
    report_kind: str = "mmc",
) -> list[dict[str, str]]:
    overrides = overrides or {}
    stored = overrides.get("table_rows")
    if stored:
        stored = _strip_introducao_prose_rows(stored)
    if report_kind == "tomografia":
        defaults = default_tomo_introducao_rows()
        if stored:
            # Respeita remoções/adições do usuário — não reanexa defaults faltantes.
            return _merge_with_defaults(defaults, stored, append_missing=False)
        return apply_legacy_introducao_overrides(defaults, overrides)
    if stored:
        return _merge_with_defaults(
            default_table_rows("introducao"), stored, append_missing=False,
        )
    return apply_legacy_introducao_overrides(default_table_rows("introducao"), overrides)


def _merge_with_defaults(
    defaults: list[dict[str, str]],
    stored: list,
    *,
    append_missing: bool = True,
) -> list[dict[str, str]]:
    default_by_id = {row["id"]: row for row in defaults}
    merged: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in stored:
        row_id = row.get("id", "")
        base = default_by_id.get(row_id, {"id": row_id, "label": row.get("label", ""), "value": ""})
        merged.append({
            "id": row_id or base["id"],
            "label": row.get("label", base["label"]),
            "value": row.get("value", base["value"]),
        })
        if row_id:
            seen.add(row_id)
    if append_missing:
        for row in defaults:
            if row["id"] not in seen:
                merged.append(dict(row))
    return merged


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


def default_tomo_identificacao_rows() -> list[dict[str, str]]:
    from src.core.domain.tomo_template_defaults import IDENTIFICACAO_TOMO_TABLE_ROWS

    return [
        {"id": row_id, "label": label, "value": value}
        for row_id, label, value in IDENTIFICACAO_TOMO_TABLE_ROWS
    ]


def merge_table_rows(section_id: str, stored: list | None) -> list[dict[str, str]]:
    defaults = default_table_rows(section_id)
    if not stored:
        return defaults
    return _merge_with_defaults(defaults, stored)