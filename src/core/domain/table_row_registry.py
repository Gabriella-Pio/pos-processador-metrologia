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
})

_FIXED_SECTION_IDS: frozenset[str] = frozenset({"cabecalho", "historico_versoes"})

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


def default_table_rows(section_id: str) -> list[dict[str, str]]:
    if section_id == "identificacao":
        return [
            {"id": row.id, "label": row.label, "value": row.default_value}
            for row in IDENTIFICACAO_TABLE_ROWS
        ]
    return []


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
    for row in defaults:
        if row["id"] not in seen:
            merged.append(dict(row))
    return merged
